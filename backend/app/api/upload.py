from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import pandas as pd
import io
from app.tasks.analysis_tasks import process_uploaded_file
from app.models.schemas import UploadResponse, AnalysisStatus

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_test_data(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read and validate CSV
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Basic validation
        if df.shape[1] < 2:
            raise HTTPException(status_code=400, detail="CSV must have at least 2 columns (student_id and items)")
        
        # Generate session and task IDs
        session_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        # Save file temporarily
        file_path = f"/app/shared_data/{session_id}_{file.filename}"
        df.to_csv(file_path, index=False)
        
        # Start Celery task
        task = process_uploaded_file.delay(file_path, session_id)
        
        return UploadResponse(
            task_id=task_id,
            session_id=session_id,
            status=AnalysisStatus.PENDING,
            message="File uploaded successfully. Analysis started."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")