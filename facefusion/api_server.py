from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from facefusion import state_manager, job_manager

app = FastAPI(
    title="FaceFusion API",
    version="2.0.0",
    description="API for FaceFusion 2.0 (React + FastAPI)"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "facefusion-api"}

@app.get("/system/info")
def system_info():
    return {
        "version": "2.0.0",
        "backend": "FastAPI",
        "python_version": state_manager.get_item('python_version') or "unknown"
    }
