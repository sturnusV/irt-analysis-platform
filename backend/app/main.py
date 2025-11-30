from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api import upload, analysis, export, icc, tif, iif
from app.version import get_version_info

app = FastAPI(title="IRT Analysis Platform", version="1.0.0")

# Get environment
environment = os.getenv("ENVIRONMENT", "development")

# Dynamic CORS configuration
def get_allowed_origins():
    # Get frontend URL from environment
    frontend_url = os.getenv("FRONTEND_URL", "")
    
    # Base origins for development
    dev_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://0.0.0.0:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://frontend:3000",  # Docker service name
    ]
    
    # Production origins
    prod_origins = []
    
    # Add frontend URL if provided
    if frontend_url:
        prod_origins.append(frontend_url)
        # Also add without trailing slash
        if frontend_url.endswith('/'):
            prod_origins.append(frontend_url[:-1])
    
    # Add common production patterns
    prod_origins.extend([
        "https://*.render.com",
        "https://*.vercel.app", 
        "https://*.netlify.app",
        "https://*.github.io",
    ])
    
    # Combine based on environment
    if environment == "production":
        origins = prod_origins
        # Allow all origins in production (with caution) OR be specific
        # origins = ["*"]  # Uncomment if you want to allow all origins
    else:
        origins = dev_origins + prod_origins
    
    # Remove duplicates and empty values
    origins = list(set([origin for origin in origins if origin]))
    
    print(f"Environment: {environment}")
    print(f"CORS allowed origins: {origins}")
    return origins

# Get allowed origins
allowed_origins = get_allowed_origins()

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