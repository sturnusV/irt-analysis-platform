from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api import upload, analysis, export, icc, tif, iif
from app.version import get_version_info

app = FastAPI(title="IRT Analysis Platform", version="1.0.0")

# Get allowed origins from environment
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://frontend:3000",
    "http://0.0.0.0:3000",
    frontend_url
]

# Remove duplicates and None values
allowed_origins = list(set([origin for origin in allowed_origins if origin]))

print(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(icc.router, prefix="/api", tags=["icc-chart"])
app.include_router(tif.router, prefix="/api", tags=["tif-chart"])
app.include_router(iif.router, prefix="/api", tags=["iif-chart"])

@app.get("/")
async def root():
    return {"message": "IRT Analysis Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/version")
async def get_version():
    """Get application version information"""
    return get_version_info()