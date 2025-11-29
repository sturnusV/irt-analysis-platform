# app/routers/icc.py
from fastapi import APIRouter, HTTPException
from app.services.icc_service import ICCService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/icc/{session_id}")
async def get_icc(session_id: str, item_id: str = None):
    """
    Gets ICC curves from:
    - R (primary)
    - Python fallback (secondary)
    """
    try:
        response = ICCService.get_icc(session_id, item_id)

        if response.get("status") != "success":
            raise HTTPException(status_code=500, detail=response.get("error"))

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"ICC failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="ICC failed")
    
