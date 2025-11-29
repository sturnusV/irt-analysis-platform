import redis
import json
import os
import logging
from app.models.schemas import AnalysisStatus

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

def store_analysis_results(session_id: str, results: dict):
    """Store analysis results in Redis"""
    try:
        key = f"analysis:{session_id}"
        redis_client.setex(key, 3600, json.dumps(results))  # Expire in 1 hour
        logger.info(f"Stored analysis results for session: {session_id}")
    except Exception as e:
        logger.error(f"Error storing analysis results for session {session_id}: {str(e)}")
        raise

def get_analysis_results(session_id: str):
    """Retrieve analysis results from Redis"""
    try:
        key = f"analysis:{session_id}"
        results = redis_client.get(key)
        if results:
            logger.info(f"Retrieved analysis results for session: {session_id}")
            return json.loads(results)
        else:
            logger.warning(f"No analysis results found for session: {session_id}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving analysis results for session {session_id}: {str(e)}")
        return None

def update_analysis_status(session_id: str, status: str, message: str = ""):
    """Update analysis status in Redis"""
    try:
        key = f"status:{session_id}"
        status_data = {
            "status": status,
            "message": message
        }
        redis_client.setex(key, 3600, json.dumps(status_data))
        logger.info(f"Updated status for session {session_id}: {status} - {message}")
    except Exception as e:
        logger.error(f"Error updating status for session {session_id}: {str(e)}")

def get_analysis_status(session_id: str):
    """Get analysis status from Redis"""
    try:
        key = f"status:{session_id}"
        status_data = redis_client.get(key)
        if status_data:
            return json.loads(status_data)
        return None
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {str(e)}")
        return None