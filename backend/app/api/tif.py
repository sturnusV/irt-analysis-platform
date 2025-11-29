# app/routers/tif.py
from fastapi import APIRouter, HTTPException
from app.services.tif_service import TIFService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/tif/{session_id}")
async def get_tif(session_id: str):
    """
    Gets Test Information Function from:
    - R (primary)
    - Python fallback (secondary)
    """
    try:
        response = TIFService.get_tif(session_id)

        if response.get("status") != "success":
            raise HTTPException(status_code=500, detail=response.get("error"))

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"TIF failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="TIF failed")