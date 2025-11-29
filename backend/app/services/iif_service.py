from app.services.redis_service import get_analysis_results
from app.services.r_service import r_service
from app.utils.iif_math import compute_item_information
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class IIFService:

    @staticmethod
    def get_iif(session_id: str):
        """
        Comprehensive IIF service:
        1. Try R service first using the /iif plumber endpoint.
        2. Fallback to Python computation.
        """
        logger.info(f"=== IIF SERVICE STARTED for session {session_id} ===")
        
        results = get_analysis_results(session_id)
        if not results:
            logger.error(f"Session {session_id} not found in Redis")
            return {"status": "error", "error": "Session not found"}

        data_path = results.get("data_path")
        item_params = results.get("item_parameters")

        if not data_path or not item_params:
            logger.error(f"Missing data for session {session_id}: data_path={data_path is not None}, item_params={item_params is not None}")
            return {"status": "error", "error": "Missing analysis results or item parameters"}

        # 1. Try R service first
        try:
            logger.info(f"Attempting R service IIF with data_path: {data_path}")
            r_iif = r_service.get_iif(data_path=data_path)
            
            if r_iif.get("status") == "success":
                logger.info("✓ R IIF service successful")
                return r_iif 
            else:
                logger.warning(f"R IIF returned non-success status: {r_iif.get('status')}")
                
        except Exception as e:
            logger.warning(f"R IIF failed: {e}")
            logger.info("Falling back to Python IIF computation...")

        # 2. Fallback to Python computation
        logger.info("Using Python fallback IIF computation")
        return IIFService.compute_python_iif(item_params)


    @staticmethod
    def compute_python_iif(item_params: List[Dict[str, Any]]):
        """Python fallback IIF computation using app.utils.iif_math."""
        try:
            # Use the utility function to get the IIF data
            iif_data_by_item = compute_item_information(item_params)
            
            # Transform the item-keyed data into the long format expected by the frontend response structure
            full_iif_long_format = []
            for item_id, data in iif_data_by_item.items():
                for theta, info in zip(data['theta'], data['info']):
                    full_iif_long_format.append({
                        "theta": theta,
                        "iif": info, # Use 'iif' here to match the R endpoint output field name
                        "item_id": item_id
                    })

            return {
                "status": "success",
                "iif_data": full_iif_long_format
            }
        except Exception as e:
            logger.error(f"Python IIF computation failed: {e}")
            return {"status": "error", "error": f"Python IIF computation failed: {str(e)}"}