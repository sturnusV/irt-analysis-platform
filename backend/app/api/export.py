from fastapi import APIRouter, HTTPException
from app.services.redis_service import get_analysis_results
from app.services.export_service import export_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/export/csv/{session_id}")
async def export_csv(session_id: str):
    """Export analysis results as CSV"""
    try:
        results = get_analysis_results(session_id)
        if not results:
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        return export_service.export_to_csv(results)
        
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/pdf/{session_id}")
async def export_pdf(session_id: str):
    """Export analysis results as PDF"""
    try:
        results = get_analysis_results(session_id)
        if not results:
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        return export_service.export_to_pdf(results)
        
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF export not available: {str(e)}")