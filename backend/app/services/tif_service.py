from app.services.redis_service import get_analysis_results
from app.services.r_service import r_service
from app.utils.tif_math import tif_3pl, sem_from_tif
import logging

logger = logging.getLogger(__name__)

class TIFService:

    @staticmethod
    def get_tif(session_id: str):
        """
        Comprehensive TIF service following ICC pattern:
        1. Try R service first
        2. Fallback to Python computation
        """
        results = get_analysis_results(session_id)
        if not results:
            return {"status": "error", "error": "Session not found"}

        data_path = results.get("data_path")
        item_params = results.get("item_parameters")

        if not data_path or not item_params:
            return {"status": "error", "error": "Missing analysis results"}

        # Try R service first
        try:
            r_tif = r_service.get_test_info(data_path=data_path)
            if r_tif.get("status") == "success":
                logger.info("Using R-computed TIF")
                return r_tif
        except Exception as e:
            logger.warning(f"R TIF failed: {e}")

        # Fallback to Python computation
        logger.info("Falling back to Python TIF computation")
        return TIFService.compute_python_tif(item_params)

    @staticmethod
    def compute_python_tif(item_params):
        """Python fallback TIF computation"""
        try:
            theta, tif = tif_3pl(item_params)
            sem = sem_from_tif(tif)

            return {
                "status": "success",
                "theta": theta,
                "tif": tif,
                "sem": sem
            }
        except Exception as e:
            logger.error(f"Python TIF computation failed: {e}")
            return {"status": "error", "error": f"TIF computation failed: {str(e)}"}  
			
	