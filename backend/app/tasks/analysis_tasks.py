from celery import current_task
from app.celery import celery_app
from app.services.redis_service import store_analysis_results, update_analysis_status
from app.services.r_service import r_service
import pandas as pd
import os
import logging
from datetime import datetime

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

def clean_string_value(value, default=""):
    """Clean string values by removing brackets, quotes, and unwanted characters"""
    if value is None:
        return default
    
    # Handle lists
    if isinstance(value, list):
        if len(value) > 0:
            value = value[0]
        else:
            return default
    
    # Convert to string and clean
    result = str(value)
    
    # Remove unwanted characters
    result = result.replace("'", "").replace('"', '')
    result = result.replace("[", "").replace("]", "")
    result = result.strip()
    
    return result

def format_timestamp_for_storage():
    """Create ISO timestamp for storage (keeps original format for storage)"""
    return datetime.now().isoformat()

def safe_float(value, default=0.0, format_decimal=False):
    """Safely convert value to float, handling various edge cases"""
    if value is None:
        return default
    
    try:
        # Handle lists
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                value = value[0]
            else:
                return default
        
        # Convert to float
        result = float(value)
        
        # Remove trailing .0 if it's actually an integer
        if result.is_integer() and format_decimal:
            return int(result)
        
        return result
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to integer"""
    if value is None:
        return default
    
    try:
        # Handle lists
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                value = value[0]
            else:
                return default
        
        # Try to convert to int
        return int(float(value))
    except (ValueError, TypeError):
        return default

def transform_r_results(r_results: dict, session_id: str, file_path: str) -> dict:
    """Transform R service results to match Python schema with clean formatting"""
    
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
            'model_type': clean_string_value(item.get('model_type', '3PL'))
        }
        item_params.append(param_dict)
    
    # Get test information with safe access
    test_info = r_results.get('test_information', {})
    
    # Get model fit with safe access and type conversion
    model_fit_raw = r_results.get('model_fit', {})
    model_fit_clean = {}
    
    # Convert model fit values to proper types
    model_fit_clean['m2'] = safe_float(model_fit_raw.get('m2'), 0.0)
    model_fit_clean['m2_p'] = safe_float(model_fit_raw.get('m2_p'), 0.0)
    model_fit_clean['tli'] = safe_float(model_fit_raw.get('tli'), 0.0)
    model_fit_clean['rmsea'] = safe_float(model_fit_raw.get('rmsea'), 0.0)
    model_fit_clean['reliability'] = safe_float(model_fit_raw.get('reliability'), 0.0)
    model_fit_clean['log_likelihood'] = safe_float(model_fit_raw.get('log_likelihood'), 0.0)
    model_fit_clean['aic'] = safe_float(model_fit_raw.get('aic'), 0.0)
    model_fit_clean['bic'] = safe_float(model_fit_raw.get('bic'), 0.0)
    
    # Handle M2 DF as integer (no decimals)
    m2_df = model_fit_raw.get('m2_df')
    model_fit_clean['m2_df'] = safe_int(m2_df, 0)
    
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
    
    # Extract model info with proper typing
    model_type = model_info_raw.get('type', '3PL')
    model_info_clean['type'] = clean_string_value(model_type)
    
    # Handle converged (might come as string "TRUE"/"FALSE" from R)
    converged_val = model_info_raw.get('converged', True)
    if isinstance(converged_val, str):
        converged_val = converged_val.lower() in ['true', 't', '1', 'yes', 'y']
    model_info_clean['converged'] = bool(converged_val)
    
    # Iterations should be integer
    iterations_val = model_info_raw.get('iterations', 0)
    model_info_clean['iterations'] = safe_int(iterations_val, 0)
    
    # Log-likelihood as float
    log_likelihood_val = model_info_raw.get('log_likelihood', 0.0)
    model_info_clean['log_likelihood'] = safe_float(log_likelihood_val, 0.0)
    
    # Extract data summary - ensure proper integer formatting
    data_summary_raw = r_results.get('data_summary', {})
    data_summary_clean = {}
    
    # All these should be integers without decimal points
    data_summary_clean['n_students'] = safe_int(data_summary_raw.get('n_students'), 0)
    data_summary_clean['n_items'] = safe_int(data_summary_raw.get('n_items'), 0)
    data_summary_clean['original_students'] = safe_int(data_summary_raw.get('original_students'), 0)
    data_summary_clean['response_rate'] = safe_float(data_summary_raw.get('response_rate'), 0.0)
    
    # Clean analysis type
    analysis_type_raw = r_results.get('analysis_type', '3PL_IRT')
    clean_analysis_type = clean_string_value(analysis_type_raw)
    
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
        'created_at': format_timestamp_for_storage(),
        'analysis_type': clean_analysis_type
    }