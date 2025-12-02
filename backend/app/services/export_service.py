import pandas as pd
import json
from fastapi.responses import Response
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import logging
import numpy as np
from typing import Dict, List, Any
from app.version import get_version_info
from datetime import datetime

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        pass
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Convert ISO timestamp to human readable format"""
        try:
            # Handle different timestamp formats
            if 'T' in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Try parsing as string
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Format as: "December 02, 2025 08:31 AM"
            return dt.strftime('%B %d, %Y %I:%M %p')
        except Exception:
            # If parsing fails, return original
            return timestamp_str
    
    def _format_analysis_type(self, analysis_type) -> str:
        """Remove brackets and quotes from analysis type"""
        if isinstance(analysis_type, list):
            if len(analysis_type) > 0:
                # Remove brackets and quotes
                return str(analysis_type[0]).replace("'", "").replace("[", "").replace("]", "")
            return "3PL"
        elif isinstance(analysis_type, str):
            # Clean string format
            return analysis_type.replace("'", "").replace("[", "").replace("]", "")
        return "3PL"
    
    def _safe_format_value(self, value, format_spec=".3f", default="N/A", remove_trailing_zeros=True):
        """Safely format values, handling special cases"""
        if value is None:
            return default
        
        # Handle deeply nested list values
        if isinstance(value, list):
            while isinstance(value, list) and len(value) > 0:
                value = value[0]
            if isinstance(value, list) and len(value) == 0:
                return default
        
        try:
            if isinstance(value, (int, float)):
                # Special handling for integers that should have no decimals
                if isinstance(value, int):
                    return str(value)
                
                # For floats, check if it's actually an integer
                if value.is_integer():
                    return str(int(value))
                
                # Apply formatting
                if format_spec:
                    formatted = format(value, format_spec)
                    
                    # Remove trailing zeros
                    if remove_trailing_zeros:
                        # Remove trailing zeros and trailing decimal point if all zeros after decimal
                        if '.' in formatted:
                            formatted = formatted.rstrip('0').rstrip('.')
                    
                    return formatted
                return str(value)
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _safe_get(self, data_dict, key, default="N/A", format_spec=None):
        """Safely get value from dictionary and format it"""
        value = data_dict.get(key, default)
        if value == default:
            return default
        return self._safe_format_value(value, format_spec, default)
    
    def _extract_model_info(self, analysis_results: dict) -> dict:
        """Extract and properly format model information from nested structures"""
        model_info = analysis_results.get('model_info', {})
        
        # Clean model type
        model_type = model_info.get('type', 'N/A')
        if isinstance(model_type, list):
            model_type = self._format_analysis_type(model_type)
        elif model_type != 'N/A':
            model_type = str(model_type).replace("'", "").replace("[", "").replace("]", "")
        
        converged = model_info.get('converged', 'N/A')
        iterations = model_info.get('iterations', 'N/A')
        log_likelihood = model_info.get('log_likelihood', 'N/A')
        
        return {
            'type': model_type,
            'converged': str(converged) if converged != 'N/A' else 'N/A',
            'iterations': str(int(iterations)) if iterations != 'N/A' and isinstance(iterations, (int, float)) else 'N/A',
            'log_likelihood': self._safe_format_value(log_likelihood, '.2f', 'N/A')
        }
    
    def _extract_data_summary(self, analysis_results: dict) -> dict:
        """Extract and properly format data summary from nested structures"""
        data_summary = analysis_results.get('data_summary', {})
        
        # Format counts as integers (no decimals)
        n_students = data_summary.get('n_students')
        n_items = data_summary.get('n_items')
        original_students = data_summary.get('original_students')
        
        return {
            'n_students': self._safe_format_value(n_students, None, 'N/A'),
            'n_items': self._safe_format_value(n_items, None, 'N/A'),
            'response_rate': self._safe_format_value(data_summary.get('response_rate'), '.3f'),
            'original_students': self._safe_format_value(original_students, None, 'N/A')
        }
    
    def export_to_csv(self, analysis_results: dict) -> Response:
        """Export comprehensive analysis results to CSV"""
        try:
            output = io.StringIO()
            
            # Extract properly formatted data
            model_info = self._extract_model_info(analysis_results)
            data_summary = self._extract_data_summary(analysis_results)
            
            # Format timestamp
            formatted_date = self._format_timestamp(analysis_results['created_at'])
            
            # Format analysis type
            formatted_analysis_type = self._format_analysis_type(
                analysis_results.get('analysis_type', '3PL_IRT')
            )
            
            # Write header information
            output.write("COMPREHENSIVE IRT ANALYSIS REPORT\n")
            output.write("=" * 50 + "\n")
            output.write(f"Session ID: {analysis_results['session_id']}\n")
            output.write(f"Analysis Date: {formatted_date}\n")
            output.write(f"Analysis Type: {formatted_analysis_type}\n")
            
            # Data Summary
            output.write(f"Students: {data_summary['n_students']}\n")
            output.write(f"Items: {data_summary['n_items']}\n")
            output.write(f"Response Rate: {data_summary['response_rate']}\n\n")
            
            # Model Information
            output.write("MODEL INFORMATION\n")
            output.write(f"Model Type: {model_info['type']}\n")
            output.write(f"Converged: {model_info['converged']}\n")
            output.write(f"Iterations: {model_info['iterations']}\n")
            output.write(f"Log-Likelihood: {model_info['log_likelihood']}\n\n")
            
            # Model Fit Statistics
            output.write("MODEL FIT STATISTICS\n")
            model_fit = analysis_results.get('model_fit', {})
            fit_data = [
                ['M2', self._safe_format_value(model_fit.get('m2'), '.3f')],
                ['M2 p-value', self._safe_format_value(model_fit.get('m2_p'), '.3f')],
                ['M2 Degrees of Freedom', self._safe_format_value(model_fit.get('m2_df'), None)],
                ['TLI', self._safe_format_value(model_fit.get('tli'), '.3f')],
                ['RMSEA', self._safe_format_value(model_fit.get('rmsea'), '.3f')],
                ['Reliability', self._safe_format_value(model_fit.get('reliability'), '.3f')],
                ['Log-Likelihood', self._safe_format_value(model_fit.get('log_likelihood'), '.1f')]
            ]
            for stat, value in fit_data:
                output.write(f"{stat}: {value}\n")
            output.write("\n")
            
            # Item Parameters (ALL items)
            output.write("ITEM PARAMETERS\n")
            item_params = analysis_results.get('item_parameters', [])
            if item_params:
                # Convert to DataFrame for better formatting
                params_df = pd.DataFrame(item_params)
                params_df.to_csv(output, index=False)
                output.write("\n\n")
            
            # Test Information Function
            output.write("TEST INFORMATION FUNCTION\n")
            test_info = analysis_results.get('test_information', {})
            if test_info and 'theta' in test_info and 'information' in test_info:
                output.write("Theta,Information\n")
                theta_values = test_info['theta']
                info_values = test_info['information']
                
                if isinstance(theta_values, list) and isinstance(info_values, list):
                    for theta, info in zip(theta_values, info_values):
                        output.write(f"{self._safe_format_value(theta, '.4f')},{self._safe_format_value(info, '.6f')}\n")
                output.write("\n")
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=comprehensive_irt_analysis_{analysis_results['session_id']}.csv"
                }
            )
            
        except Exception as e:
            logger.error(f"Comprehensive CSV export failed: {e}")
            raise
    
    def export_to_pdf(self, analysis_results: dict) -> Response:
        """Export comprehensive analysis results to PDF"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                spaceAfter=12,
                spaceBefore=12
            )
            
            story = []
            
            # Add version info to PDF
            version_info = get_version_info()
            
            # Extract properly formatted data
            model_info = self._extract_model_info(analysis_results)
            data_summary = self._extract_data_summary(analysis_results)
            
            # Format timestamp and analysis type
            formatted_date = self._format_timestamp(analysis_results['created_at'])
            formatted_analysis_type = self._format_analysis_type(
                analysis_results.get('analysis_type', '3PL_IRT')
            )
            
            # Title Page
            title = Paragraph("COMPREHENSIVE IRT ANALYSIS REPORT", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.3*inch))
            
            # Session Information
            session_info = f"""
            <b>Session ID:</b> {analysis_results['session_id']}<br/>
            <b>Analysis Date:</b> {formatted_date}<br/>
            <b>Analysis Type:</b> {formatted_analysis_type}<br/>
            <b>Software:</b> IRT Analysis Platform {version_info['version']}
            """
            info_para = Paragraph(session_info, styles['Normal'])
            story.append(info_para)
            story.append(Spacer(1, 0.4*inch))
            
            # Data Summary
            data_title = Paragraph("Data Summary", header_style)
            story.append(data_title)
            
            data_info = f"""
            <b>Number of Students:</b> {data_summary['n_students']}<br/>
            <b>Number of Items:</b> {data_summary['n_items']}<br/>
            <b>Response Rate:</b> {data_summary['response_rate']}<br/>
            <b>Original Students:</b> {data_summary['original_students']}
            """
            data_para = Paragraph(data_info, styles['Normal'])
            story.append(data_para)
            story.append(Spacer(1, 0.3*inch))
            
            # Model Information
            model_title = Paragraph("Model Information", header_style)
            story.append(model_title)
            
            model_info_text = f"""
            <b>Model Type:</b> {model_info['type']}<br/>
            <b>Converged:</b> {model_info['converged']}<br/>
            <b>Iterations:</b> {model_info['iterations']}<br/>
            <b>Log-Likelihood:</b> {model_info['log_likelihood']}
            """
            model_para = Paragraph(model_info_text, styles['Normal'])
            story.append(model_para)
            story.append(Spacer(1, 0.3*inch))
            
            # Model Fit Statistics
            fit_title = Paragraph("Model Fit Statistics", header_style)
            story.append(fit_title)
            
            model_fit = analysis_results.get('model_fit', {})
            fit_data = [
                ['Statistic', 'Value', 'Interpretation'],
                ['M2', self._safe_format_value(model_fit.get('m2'), '.3f'), 'Overall fit (lower better)'],
                ['M2 p-value', self._safe_format_value(model_fit.get('m2_p'), '.3f'), 'p > 0.05 indicates good fit'],
                ['M2 DF', self._safe_format_value(model_fit.get('m2_df'), None), 'Degrees of freedom'],
                ['TLI', self._safe_format_value(model_fit.get('tli'), '.3f'), '> 0.90 good, > 0.95 excellent'],
                ['RMSEA', self._safe_format_value(model_fit.get('rmsea'), '.3f'), '< 0.08 acceptable, < 0.05 good'],
                ['Reliability', self._safe_format_value(model_fit.get('reliability'), '.3f'), 'Test reliability'],
                ['Log-Likelihood', self._safe_format_value(model_fit.get('log_likelihood'), '.1f'), 'Model fit']
            ]
            
            fit_table = Table(fit_data, colWidths=[1.5*inch, 1.2*inch, 2.5*inch])
            fit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
            ]))
            story.append(fit_table)
            story.append(Spacer(1, 0.4*inch))
            
            # Page break for items
            story.append(PageBreak())
            
            # Item Parameters (ALL items)
            items_title = Paragraph("Item Parameters", header_style)
            story.append(items_title)
            
            item_params = analysis_results.get('item_parameters', [])
            if item_params:
                # Prepare item data
                item_data = [['Item ID', 'Difficulty (b)', 'Discrimination (a)', 'Guessing (c)', 
                             'SE Difficulty', 'SE Discrimination', 'SE Guessing', 'Model Type']]
                
                for item in item_params:
                    item_data.append([
                        item['item_id'],
                        self._safe_format_value(item.get('difficulty'), '.3f'),
                        self._safe_format_value(item.get('discrimination'), '.3f'),
                        self._safe_format_value(item.get('guessing'), '.3f'),
                        f"±{self._safe_format_value(item.get('se_difficulty'), '.3f')}",
                        f"±{self._safe_format_value(item.get('se_discrimination'), '.3f')}",
                        f"±{self._safe_format_value(item.get('se_guessing'), '.3f')}",
                        item.get('model_type', '3PL')
                    ])
                
                # Create table with all items
                items_table = Table(item_data, repeatRows=1)
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
                ]))
                story.append(items_table)
            
            story.append(Spacer(1, 0.3*inch))
            
            # Test Information Summary
            test_info = analysis_results.get('test_information', {})
            if test_info and 'theta' in test_info and 'information' in test_info:
                info_title = Paragraph("Test Information Function Summary", header_style)
                story.append(info_title)
                
                theta_values = test_info['theta']
                info_values = test_info['information']
                
                if isinstance(theta_values, list) and isinstance(info_values, list):
                    info_array = np.array(info_values)
                    theta_array = np.array(theta_values)
                    
                    if len(info_array) > 0 and len(theta_array) > 0:
                        max_info_idx = np.argmax(info_array)
                        
                        info_summary = f"""
                        <b>Maximum Test Information:</b> {self._safe_format_value(info_array[max_info_idx], '.3f')}<br/>
                        <b>at Ability Level (θ):</b> {self._safe_format_value(theta_array[max_info_idx], '.3f')}<br/>
                        <b>Information Range:</b> {self._safe_format_value(np.min(info_array), '.3f')} - {self._safe_format_value(np.max(info_array), '.3f')}<br/>
                        <b>Average Information:</b> {self._safe_format_value(np.mean(info_array), '.3f')}
                        """
                        info_para = Paragraph(info_summary, styles['Normal'])
                        story.append(info_para)
            
            # Interpretation Guide
            guide_title = Paragraph("Interpretation Guide", header_style)
            story.append(guide_title)
            
            interpretation = """
            <b>Difficulty (b):</b> Positive values indicate harder items, negative values easier items<br/>
            <b>Discrimination (a):</b> Higher values indicate better item discrimination<br/>
            <b>Guessing (c):</b> Probability of correct answer by guessing alone<br/>
            <b>Standard Errors:</b> Lower values indicate more precise parameter estimates<br/>
            <b>Test Information:</b> Higher information indicates better measurement precision
            """
            guide_para = Paragraph(interpretation, styles['Normal'])
            story.append(guide_para)
            
            doc.build(story)
            buffer.seek(0)
            
            return Response(
                content=buffer.getvalue(),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=comprehensive_irt_analysis_{analysis_results['session_id']}.pdf"
                }
            )
            
        except Exception as e:
            logger.error(f"Comprehensive PDF export failed: {e}")
            raise
    
    def export_to_json(self, analysis_results: dict) -> Response:
        """Export complete analysis results to JSON"""
        try:
            # Format data for JSON export
            formatted_date = self._format_timestamp(analysis_results['created_at'])
            formatted_analysis_type = self._format_analysis_type(
                analysis_results.get('analysis_type', '3PL_IRT')
            )
            
            # Create a comprehensive export structure
            export_data = {
                "metadata": {
                    "export_version": "1.0",
                    "export_timestamp": formatted_date,
                    "software": "IRT Analysis Platform"
                },
                "session_info": {
                    "session_id": analysis_results['session_id'],
                    "analysis_type": formatted_analysis_type,
                    "created_at": formatted_date
                },
                "data_summary": self._extract_data_summary(analysis_results),
                "model_info": self._extract_model_info(analysis_results),
                "model_fit": analysis_results.get('model_fit', {}),
                "item_parameters": analysis_results.get('item_parameters', []),
                "test_information": analysis_results.get('test_information', {}),
            }
            
            json_content = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
            
            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=complete_irt_data_{analysis_results['session_id']}.json"
                }
            )
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise

export_service = ExportService()