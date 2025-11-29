"""
Version tracking for IRT AnalyzeR platform
"""
import os
from typing import Dict, Any

def get_version() -> str:
    """Get current application version"""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "1.0.0"  # Fallback version

def get_version_info() -> Dict[str, Any]:
    """Get comprehensive version information"""
    return {
        "version": get_version(),
        "name": "IRT AnalyzeR",
        "description": "Modern IRT Analysis Platform",
        "build_date": os.getenv('BUILD_DATE', '2024-01-01'),
        "commit_hash": os.getenv('COMMIT_HASH', 'dev'),
        "environment": os.getenv('ENVIRONMENT', 'development')
    }