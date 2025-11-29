from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.redis_service import get_analysis_results, get_analysis_status
from app.models.schemas import AnalysisResults
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/analysis/{session_id}")
async def get_analysis_results_endpoint(session_id: str):
    try:
        logger.info(f"Fetching analysis results for session: {session_id}")
        results = get_analysis_results(session_id)

        if results is None:
            # Check if analysis is at least known / started
            status = get_analysis_status(session_id)

            if status:
                # Analysis is known but not finished yet
                return JSONResponse(
                    status_code=202,
                    content={"status": "processing"}
                )
            else:
                # No such session_id at all → real 404
                logger.warning(f"Unknown session: {session_id}")
                raise HTTPException(
                    status_code=404,
                    detail="Analysis session not found"
                )

        logger.info(f"Successfully retrieved results for session: {session_id}")
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis results for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    try:
        status_data = get_analysis_status(session_id)
        if not status_data:
            raise HTTPException(status_code=404, detail="Status not found")
        return status_data
    except Exception as e:
        logger.error(f"Error fetching status for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")