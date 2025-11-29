from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class UploadResponse(BaseModel):
    task_id: str
    session_id: str
    status: AnalysisStatus
    message: str

class AnalysisRequest(BaseModel):
    session_id: str
    file_name: str

class IRTParameters(BaseModel):
    item_id: str
    difficulty: float
    discrimination: float
    guessing: float
    se_difficulty: Optional[float] = None
    se_discrimination: Optional[float] = None
    se_guessing: Optional[float] = None

class AnalysisResults(BaseModel):
    session_id: str
    status: AnalysisStatus
    item_parameters: List[IRTParameters]
    test_information: Optional[Dict[str, Any]] = None
    item_information: Optional[Dict[str, Any]] = None
    model_fit: Dict[str, float]
    created_at: str