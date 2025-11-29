from celery import current_task
from app.celery import celery_app
from app.services.redis_service import store_analysis_results, update_analysis_status
from app.services.r_service import r_service
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_uploaded_file(self, file_path: str, session_id: str):
    """Process uploaded file and perform IRT analysis"""
    try:
        logger.info(f"Starting analysis task for session: {session_id}, file: {file_path}")
        
        update_analysis_status(session_id, "processing", "Reading and validating data...")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read and validate data
        df = pd.read_csv(file_path)
        logger.info(f"Read CSV with shape: {df.shape}")
        logger.info(f"First few rows:\n{df.head()}")
        logger.info(f"Data summary:\n{df.describe()}")
        
        # Check if first column is ID or response data
        first_col = df.columns[0].lower()
        has_id_column = any(id_term in first_col for id_term in ['id', 'student', 'person', 'subject'])
        
        if has_id_column:
            response_data = df.iloc[:, 1:]  # Exclude ID column
            student_ids = df.iloc[:, 0].tolist()
        else:
            response_data = df  # All columns are items
            student_ids = list(range(len(df)))
        
        num_students = len(response_data)
        num_items = len(response_data.columns)
        
        # Data quality checks
        unique_values = response_data.stack().unique()
        logger.info(f"Unique values in response data: {sorted(unique_values)}")
        
        # Check for problematic data patterns
        all_zeros = (response_data == 0).all(axis=1).sum()
        all_ones = (response_data == 1).all(axis=1).sum()
        logger.info(f"Rows with all zeros: {all_zeros}, all ones: {all_ones}")
        
        # Remove completely invariant items
        item_variance = response_data.var()
        invariant_items = item_variance[item_variance == 0].index.tolist()
        if invariant_items:
            logger.warning(f"Removing invariant items: {invariant_items}")
            response_data = response_data.drop(columns=invariant_items)
            num_items = len(response_data.columns)
        
        if num_items < 2:
            raise Exception("Not enough valid items after removing invariant ones")
        
        # Save cleaned data for R processing
        cleaned_file_path = f"/app/shared_data/cleaned_{session_id}.csv"
        response_data.to_csv(cleaned_file_path, index=False)
        
        logger.info(f"Data validated: {num_students} students, {num_items} items")
        logger.info(f"Response rate: {response_data.mean().mean():.3f}")
        
        # In the process_uploaded_file function, update the status message:
        update_analysis_status(
            session_id, 
            "processing", 
            f"Data validated. {num_students} students, {num_items} items. Starting 3PL analysis with 2PL fallback..."
        )
        
        # Check if R service is healthy
        if not r_service.health_check():
            raise Exception("R analysis service is not available. Please try again later.")
        
        # Perform IRT analysis with cleaned data
        logger.info("Calling R service for IRT analysis...")
        analysis_results = r_service.analyze_irt(cleaned_file_path)
        
        if analysis_results.get('status') == 'error':
            error_msg = analysis_results.get('error', 'Unknown analysis error')
            logger.error(f"R service analysis failed: {error_msg}")
            raise Exception(f"IRT analysis failed: {error_msg}")
        
        # DEBUG: Log the actual structure returned by R
        logger.info(f"R service returned keys: {list(analysis_results.keys())}")
        if 'item_parameters' in analysis_results:
            logger.info(f"First item parameter structure: {analysis_results['item_parameters'][0] if analysis_results['item_parameters'] else 'Empty'}")
        
        # Transform R results to match Python schema
        results_data = transform_r_results(analysis_results, session_id, cleaned_file_path)
        
        # Store results in Redis
        store_analysis_results(session_id, results_data)
        update_analysis_status(session_id, "completed", "IRT analysis completed successfully")
        
        logger.info(f"Analysis completed for session {session_id}: {num_items} items, {num_students} students")
        
        return results_data
        
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"Analysis error for session {session_id}: {error_msg}")
        update_analysis_status(session_id, "error", error_msg)
        raise

def transform_r_results(r_results: dict, session_id: str, file_path: str) -> dict:
    """Transform R service results to match Python schema"""
    
    # Transform item parameters to match expected schema
    item_params = []
    for item in r_results.get('item_parameters', []):
        # Create parameter dictionary with proper type conversion
        param_dict = {
            'item_id': str(item.get('item_id', '')),
            'difficulty': safe_float(item.get('difficulty'), 0.0),
            'guessing': safe_float(item.get('guessing'), 0.0),
            'se_difficulty': safe_float(item.get('se_difficulty'), 0.0),
            'se_guessing': safe_float(item.get('se_guessing'), 0.0),
            'discrimination': safe_float(item.get('discrimination'), 1.0),
            'se_discrimination': safe_float(item.get('se_discrimination'), 0.0),
            'model_type': item.get('model_type', '3PL')  # Add model_type from item if available
        }
        item_params.append(param_dict)
    
    # Get test information with safe access
    test_info = r_results.get('test_information', {})
    
    # Get model fit with safe access and type conversion
    model_fit_raw = r_results.get('model_fit', {})
    model_fit_clean = {}
    
    # Helper function to safely extract numbers from nested structures
    def extract_number(value, default=0.0):
        if value is None:
            return default
        if isinstance(value, list):
            if len(value) > 0:
                # Handle nested lists: [[value]] -> value
                nested_value = value[0]
                if isinstance(nested_value, list) and len(nested_value) > 0:
                    return safe_float(nested_value[0], default)
                return safe_float(nested_value, default)
            return default
        return safe_float(value, default)
    
    # Convert model fit values to proper types
    model_fit_clean['m2'] = extract_number(model_fit_raw.get('m2'))
    model_fit_clean['m2_p'] = extract_number(model_fit_raw.get('m2_p'))
    model_fit_clean['tli'] = extract_number(model_fit_raw.get('tli'))
    model_fit_clean['rmsea'] = extract_number(model_fit_raw.get('rmsea'))
    model_fit_clean['reliability'] = extract_number(model_fit_raw.get('reliability'))
    model_fit_clean['log_likelihood'] = extract_number(model_fit_raw.get('log_likelihood'))
    model_fit_clean['aic'] = extract_number(model_fit_raw.get('aic'))
    model_fit_clean['bic'] = extract_number(model_fit_raw.get('bic'))
    
    # Handle integer fields
    m2_df = model_fit_raw.get('m2_df')
    if isinstance(m2_df, list) and len(m2_df) > 0:
        model_fit_clean['m2_df'] = int(m2_df[0])
    else:
        model_fit_clean['m2_df'] = int(m2_df) if m2_df is not None else 0
    
    model_fit_clean['converged'] = bool(model_fit_raw.get('converged', True))
    
    # Safe list extraction for test information
    theta_raw = test_info.get('theta', [])
    information_raw = test_info.get('information', [])
    
    theta_clean = []
    information_clean = []
    
    # Handle nested list structures in test information
    if isinstance(theta_raw, list) and len(theta_raw) > 0:
        if isinstance(theta_raw[0], list):
            theta_clean = [safe_float(x[0], 0.0) for x in theta_raw if x]
        else:
            theta_clean = [safe_float(x, 0.0) for x in theta_raw]
    
    if isinstance(information_raw, list) and len(information_raw) > 0:
        if isinstance(information_raw[0], list):
            information_clean = [safe_float(x[0], 0.0) for x in information_raw if x]
        else:
            information_clean = [safe_float(x, 0.0) for x in information_raw]
    
    # Extract and transform model_info from R results
    model_info_raw = r_results.get('model_info', {})
    model_info_clean = {}
    
    # Helper function to extract model info values with proper typing
    def extract_model_info(value, value_type='auto', default=None):
        if value is None:
            return default
        if isinstance(value, list):
            if len(value) > 0:
                value = value[0]  # Return first element of list
            else:
                return default
        
        # Handle different value types
        if value_type == 'bool':
            return bool(value)
        elif value_type == 'int':
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        elif value_type == 'float':
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        else:  # auto - try to detect type
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, bool):
                return value
            else:
                return str(value)
    
    # Extract model info with proper typing
    model_info_clean['type'] = extract_model_info(model_info_raw.get('type'), 'auto', '3PL')
    model_info_clean['converged'] = extract_model_info(model_info_raw.get('converged'), 'bool', True)
    model_info_clean['iterations'] = extract_model_info(model_info_raw.get('iterations'), 'int', 0)
    model_info_clean['log_likelihood'] = extract_model_info(model_info_raw.get('log_likelihood'), 'float', 0.0)
    
    # Extract data summary
    data_summary_raw = r_results.get('data_summary', {})
    data_summary_clean = {}
    
    data_summary_clean['n_students'] = extract_model_info(data_summary_raw.get('n_students'), 'int')
    data_summary_clean['n_items'] = extract_model_info(data_summary_raw.get('n_items'), 'int')
    data_summary_clean['original_students'] = extract_model_info(data_summary_raw.get('original_students'), 'int')
    data_summary_clean['response_rate'] = extract_model_info(data_summary_raw.get('response_rate'), 'float')
    
    return {
        'session_id': session_id,
        'status': 'completed',
        'item_parameters': item_params,
        'model_info': model_info_clean,
        'model_fit': model_fit_clean,
        'test_information': {
            'theta': theta_clean,
            'information': information_clean
        },
        'data_summary': data_summary_clean,
        'data_path': file_path,
        'created_at': pd.Timestamp.now().isoformat(),
        'analysis_type': r_results.get('analysis_type', '2PL_IRT')
    }

def safe_float(value, default=0.0):
    """Safely convert value to float, handling various edge cases"""
    if value is None:
        return default
    try:
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                return float(value[0])
            return default
        return float(value)
    except (ValueError, TypeError):
        return default