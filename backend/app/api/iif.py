# app/routers/iif.py (New File)
from fastapi import APIRouter, HTTPException
from app.services.iif_service import IIFService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/iif/{session_id}")
async def get_iif(session_id: str):
    """
    Gets Item Information Function (IIF) data from:
    - R (primary)
    - Python fallback (secondary)
    """
    try:
        # Delegate the main logic to the service layer
        response = IIFService.get_iif(session_id) 

        if response.get("status") != "success":
            # If the service layer returns an error status, raise an HTTPException
            raise HTTPException(status_code=500, detail=response.get("error"))

        return response

    except HTTPException:
        # Re-raise explicit HTTPExceptions
        raise
    except Exception as e:
        # Catch any unexpected errors, log them, and return a generic 500
        logger.exception(f"IIF failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="IIF failed due to an internal error")