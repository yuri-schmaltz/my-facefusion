import os
import shutil
import time
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile

from facefusion import state_manager, job_manager
from facefusion.jobs import job_runner
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
    # common settings
    face_selector_mode: Optional[str] = None
    output_video_quality: Optional[int] = None
    frame_processor_checkpoint: Optional[str] = None # Example
    # generic bag for anything else
    settings: Optional[dict] = None

# ...

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

@app.get("/config")
def get_config():
    # Return a subset of interesting config
    return {
        "processors": state_manager.get_item('processors'),
        "face_selector_mode": state_manager.get_item('face_selector_mode'),
        "output_video_quality": state_manager.get_item('output_video_quality'),
        "execution_providers": state_manager.get_item('execution_providers'),
        # Add more defaults as needed for the UI to populate
    }

@app.post("/config")
def update_config(config: ConfigUpdate):
    if config.processors is not None:
        state_manager.set_item('processors', config.processors)
    if config.output_path is not None:
        state_manager.set_item('output_path', config.output_path)
    if config.face_selector_mode is not None:
        state_manager.set_item('face_selector_mode', config.face_selector_mode)
    if config.output_video_quality is not None:
        state_manager.set_item('output_video_quality', config.output_video_quality)
        
    if config.settings:
        for key, value in config.settings.items():
            state_manager.set_item(key, value)
            
    return {"status": "updated", "current_state": get_config()}

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

@app.on_event("startup")
def startup_event():
    # Initialize jobs directory
    jobs_path = os.path.join(get_temp_path(), "jobs")
    job_manager.init_jobs(jobs_path)

@app.post("/run")
def run_job():
    # 1. Prepare Job ID e Output Path
    job_id = "job_" + str(int(time.time()))
    
    # Check if output path is set, else generate one
    output_path = state_manager.get_item('output_path')
    if not output_path:
        output_name = f"output_{job_id}.mp4" # Assuming video for now, or detect based on source
        output_path = os.path.join(get_temp_path(), "api_outputs", output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 2. Collect Args (Current State)
    # We need to gather all relevant args from state_manager to pass to the step
    # For now, we assume state_manager has been populated by /config and /upload
    # job_runner.process_step will eventually call apply_args(step_args), so we need to pass them here.
    # However, job_manager.add_step expects 'step_args'. 
    # Let's collect a subset or all items from state_manager that correspond to Args.
    
    # Simpler approach: Pass the target_path and processors. The rest are defaults or set via config.
    # Ideally, we should collect all 'Args' fields.
    
    step_args = {
        'source_paths': state_manager.get_item('source_paths'),
        'target_path': state_manager.get_item('target_path'),
        'output_path': output_path,
        'processors': state_manager.get_item('processors'),
        # Add other critical args here if needed (e.g. face_selector_mode)
    }

    # 3. Job Workflow
    if job_manager.create_job(job_id):
        if job_manager.add_step(job_id, step_args):
            if job_manager.submit_job(job_id):
                # 4. Run Job (Synchronous for MVP, Async later)
                # We need to import process_step from core, or pass a processor function
                from facefusion.core import process_step
                
                if job_runner.run_job(job_id, process_step):
                    return {
                        "status": "completed",
                        "job_id": job_id,
                        "output_path": output_path,
                        "preview_url": f"/files/preview?path={output_path}" # Convenience
                    }
                
    raise HTTPException(500, "Job execution failed")

@app.get("/files/preview")
def get_preview(path: str):
    # Security note: This is unsafe for production, allows reading any file. 
    # For local "Senior" app tool, it's acceptable for now but should be scoped.
    # Also strip quotes just in case
    path = path.strip('"\'')
    if os.path.exists(path):
        return FileResponse(path)
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect

# --- Logging Infrastructure ---
log_queue = asyncio.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            entry = self.format(record)
            # Fire and forget put
            try:
                log_queue.put_nowait(entry)
            except asyncio.QueueFull:
                pass
        except Exception:
            self.handleError(record)

# Attach handler to root logger or facefusion logger
queue_handler = QueueHandler()
queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger('facefusion').addHandler(queue_handler)
# Also capture basic logger if needed
logging.getLogger().addHandler(queue_handler)

@app.websocket("/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Simple polling/getting from queue with timeout or similar
            # Ideally we want an event driven broadcast, but for one connection queue is okay.
            # To support multiple clients, we need a BroadcastManager.

            # Simplified Broadcast for single "Senior" user
            line = await log_queue.get()
            await websocket.send_text(line)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")


