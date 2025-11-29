from app.services.redis_service import get_analysis_results
from app.services.r_service import r_service
from app.utils.icc_math import generate_icc
import logging

logger = logging.getLogger(__name__)

class ICCService:

    @staticmethod
    def get_icc(session_id: str, item_id: str = None):
        results = get_analysis_results(session_id)
        if not results:
            return {"status": "error", "error": "Session not found"}

        data_path = results.get("data_path")
        item_params = results.get("item_parameters")

        if not data_path or not item_params:
            return {"status": "error", "error": "Missing analysis results"}

        # Try R first
        try:
            r_icc = r_service.get_icc(data_path=data_path, item_id=item_id)
            if r_icc.get("status") == "success":
                return r_icc
        except Exception as e:
            logger.warning(f"R ICC failed: {e}")

        # fallback
        return ICCService.compute_python_icc(item_params, item_id)

    @staticmethod
    def compute_python_icc(item_params, item_id=None):
        icc_points = []

        for item in item_params:
            if item_id and item["item_id"] != item_id:
                continue

            a = item["discrimination"]
            b = item["difficulty"]
            c = item.get("guessing", 0.0) or 0.0

            points = generate_icc(a, b, c, item["item_id"])

            icc_points.extend(points)   # <-- merged flat list

        return {
            "status": "success",
            "icc_data": icc_points
        }

