import os
import shutil
import time
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile

from facefusion import state_manager, metadata, execution
from facefusion.jobs import job_manager, job_runner
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
    face_mask_types: Optional[List[str]] = None
    face_mask_regions: Optional[List[str]] = None
    output_video_quality: Optional[int] = None
    output_video_encoder: Optional[str] = None
    execution_providers: Optional[List[str]] = None
    execution_thread_count: Optional[int] = None
    execution_queue_count: Optional[int] = None
    # generic bag for anything else
    settings: Optional[dict] = None

# ...

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/system/info")
def system_info():
    return {
        "name": metadata.get("name"),
        "version": metadata.get("version"),
        "execution_providers": execution.get_available_execution_providers(),
        "execution_devices": execution.detect_execution_devices() # This might be slow if nvidia-smi is called every time, but acceptable for now
    }

@app.get("/processors")
def list_processors():
    # Use pkgutil to robustly find processor modules
    import pkgutil
    import facefusion.processors.modules
    
    available = []
    if hasattr(facefusion.processors.modules, '__path__'):
        for _, name, is_pkg in pkgutil.iter_modules(facefusion.processors.modules.__path__):
            if is_pkg: # Processors are subpackages (e.g. face_swapper directory)
                available.append(name)
    
    # Sort for consistency
    available.sort()
    
    # Get currently active
    active = state_manager.get_item('processors')
    return {"available": available, "active": active}

@app.get("/config")
def get_config():
    # Return a subset of interesting config
    return {
        "processors": state_manager.get_item('processors'),
        "face_selector_mode": state_manager.get_item('face_selector_mode'),
        "face_mask_types": state_manager.get_item('face_mask_types'),
        "face_mask_regions": state_manager.get_item('face_mask_regions'),
        "output_video_quality": state_manager.get_item('output_video_quality'),
        "output_video_encoder": state_manager.get_item('output_video_encoder'),
        "execution_providers": state_manager.get_item('execution_providers'),
        "execution_thread_count": state_manager.get_item('execution_thread_count'),
        "execution_queue_count": state_manager.get_item('execution_queue_count'),
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
    if config.face_mask_types is not None:
        state_manager.set_item('face_mask_types', config.face_mask_types)
    if config.face_mask_regions is not None:
        state_manager.set_item('face_mask_regions', config.face_mask_regions)
    if config.output_video_quality is not None:
        state_manager.set_item('output_video_quality', config.output_video_quality)
    if config.output_video_encoder is not None:
        state_manager.set_item('output_video_encoder', config.output_video_encoder)
    if config.execution_providers is not None:
        state_manager.set_item('execution_providers', config.execution_providers)
    if config.execution_thread_count is not None:
        state_manager.set_item('execution_thread_count', config.execution_thread_count)
    if config.execution_queue_count is not None:
        state_manager.set_item('execution_queue_count', config.execution_queue_count)
        
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
    
    # Initialize default state items
    # ensuring that critical items like download_providers are not None
    # Use init_item to ensure it populates ALL contexts (cli and ui)
    if state_manager.get_item('download_providers') is None:
        from facefusion import choices
        state_manager.init_item('download_providers', choices.download_providers)
    
    if state_manager.get_item('execution_providers') is None:
        state_manager.init_item('execution_providers', ['cpu'])
        
    if state_manager.get_item('execution_thread_count') is None:
        state_manager.init_item('execution_thread_count', 4)

    if state_manager.get_item('execution_queue_count') is None:
        state_manager.init_item('execution_queue_count', 1)
        
    if state_manager.get_item('output_video_quality') is None:
        state_manager.init_item('output_video_quality', 80)
        
    if state_manager.get_item('face_selector_mode') is None:
        state_manager.init_item('face_selector_mode', 'reference')
        
    if state_manager.get_item('face_mask_types') is None:
        state_manager.init_item('face_mask_types', ['box'])

    if state_manager.get_item('face_mask_regions') is None:
        state_manager.init_item('face_mask_regions', ['skin'])

    if state_manager.get_item('processors') is None:
        state_manager.init_item('processors', [])

@app.post("/run")
def run_job():
    print("--- RUN JOB REQUEST RECEIVED ---")
    # 1. Prepare Job ID e Output Path
    job_id = "job_" + str(int(time.time()))
    print(f"Generated Job ID: {job_id}")
    
    # Check if output path is set, else generate one
    output_path = state_manager.get_item('output_path')
    if not output_path:
        output_name = f"output_{job_id}.mp4" # Assuming video for now, or detect based on source
        output_path = os.path.join(get_temp_path(), "api_outputs", output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Output Path: {output_path}")

    # 2. Collect Args (Current State)
    # We need to gather all relevant args from state_manager to pass to the step
    # For now, we assume state_manager has been populated by /config and /upload
    # job_runner.process_step will eventually call apply_args(step_args), so we need to pass them here.
    # However, job_manager.add_step expects 'step_args'. 
    # Let's collect a subset or all items from state_manager that correspond to Args.
    
    # Simpler approach: Pass the target_path and processors. The rest are defaults or set via config.
    # Ideally, we should collect all 'Args' fields.
    
    processors = state_manager.get_item('processors') or []
    
    step_args = {
        'source_paths': state_manager.get_item('source_paths'),
        'target_path': state_manager.get_item('target_path'),
        'output_path': output_path,
        'processors': processors,
        'face_selector_mode': state_manager.get_item('face_selector_mode'),
        'face_mask_types': state_manager.get_item('face_mask_types'),
        'face_mask_regions': state_manager.get_item('face_mask_regions'),
        'execution_providers': state_manager.get_item('execution_providers'),
        'execution_thread_count': state_manager.get_item('execution_thread_count'),
        'execution_queue_count': state_manager.get_item('execution_queue_count'),
    }
    
    print(f"Step Args: {step_args}")

    # 3. Job Workflow
    print("Creating Job...")
    if job_manager.create_job(job_id):
        print("Job Created. Adding Step...")
        if job_manager.add_step(job_id, step_args):
            print("Step Added. Submitting Job...")
            if job_manager.submit_job(job_id):
                print("Job Submitted. Running Job...")
                # 4. Run Job (Synchronous for MVP, Async later)
                # We need to import process_step from core, or pass a processor function
                from facefusion.core import process_step
                
                if job_runner.run_job(job_id, process_step):
                    print("--- JOB COMPLETED SUCCESSFULLY ---")
                    return {
                        "status": "completed",
                        "job_id": job_id,
                        "output_path": output_path,
                        "preview_url": f"/files/preview?path={output_path}" # Convenience
                    }
                else:
                    print("--- JOB FAILED DURING EXECUTION ---")
            else:
                print("--- JOB SUBMISSION FAILED ---")
        else:
            print("--- STEP ADDITION FAILED ---")
    else:
        print("--- JOB CREATION FAILED ---")
                
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

# --- Filesystem API ---

class FilesystemRequest(BaseModel):
    path: Optional[str] = None

@app.post("/filesystem/list")
def list_filesystem(req: FilesystemRequest):
    import platform
    
    input_path = req.path
    print(f"DEBUG: Filesystem Request input_path='{input_path}'")
    
    current_path = input_path
    
    # Handle initial load
    if not current_path:
        current_path = os.path.expanduser("~")
        print(f"DEBUG: Defaulting to Home: '{current_path}'")
        if platform.system() == "Windows":
             pass
    
    # Force absolute path resolution
    resolved_path = os.path.abspath(current_path)
    print(f"DEBUG: Resolved path: '{resolved_path}'")
    
    # Security/Validity Check
    if not os.path.exists(resolved_path):
        print(f"ERROR: Path does not exist: {resolved_path}")
        raise HTTPException(status_code=400, detail=f"Path not found: {resolved_path}")
        
    if not os.path.isdir(resolved_path):
        print(f"ERROR: Path is not a directory: {resolved_path}")
        raise HTTPException(status_code=400, detail=f"Not a directory: {resolved_path}")
    
    items = []
    parent = os.path.dirname(resolved_path)
    
    try:
        with os.scandir(resolved_path) as it:
            for entry in it:
                try:
                    # Use follow_symlinks=False to avoid FileNotFoundError on broken symlinks
                    is_dir = entry.is_dir(follow_symlinks=True)
                    item_type = "folder" if is_dir else "file"
                    
                    size = 0
                    if not is_dir:
                        try:
                            size = entry.stat().st_size
                        except OSError:
                            # broken symlink or permission issue on specific file
                            size = 0

                    items.append({
                        "name": entry.name,
                        "type": item_type,
                        "path": entry.path,
                        "size": size
                    })
                except (PermissionError, OSError) as e:
                    # Skip things we can't even "is_dir" (like broken symlinks or locked files)
                    print(f"DEBUG: Skipping entry '{entry.name}' due to error: {e}")
                    continue
    except PermissionError:
        print(f"ERROR: Permission denied: {resolved_path}")
        raise HTTPException(status_code=400, detail=f"Permission denied accessing: {resolved_path}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
        
    # Sort: Folders first, then files
    items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
    
    print(f"DEBUG: Success. Returning {len(items)} items.")
    
@app.get("/processors/choices")
def get_processor_choices():
    from facefusion.processors.modules.face_swapper import choices as face_swapper_choices
    from facefusion.processors.modules.face_enhancer import choices as face_enhancer_choices
    from facefusion.processors.modules.frame_enhancer import choices as frame_enhancer_choices
    from facefusion.processors.modules.lip_syncer import choices as lip_syncer_choices
    from facefusion.processors.modules.age_modifier import choices as age_modifier_choices
    from facefusion.processors.modules.expression_restorer import choices as expression_restorer_choices

    return {
        "face_swapper": {
            "models": face_swapper_choices.face_swapper_models,
            "set": face_swapper_choices.face_swapper_set,
            "weight_range": list(face_swapper_choices.face_swapper_weight_range)
        },
        "face_enhancer": {
            "models": face_enhancer_choices.face_enhancer_models,
            "blend_range": list(face_enhancer_choices.face_enhancer_blend_range),
            "weight_range": list(face_enhancer_choices.face_enhancer_weight_range)
        },
        "frame_enhancer": {
            "models": frame_enhancer_choices.frame_enhancer_models,
            "blend_range": list(frame_enhancer_choices.frame_enhancer_blend_range)
        },
        "lip_syncer": {
            "models": lip_syncer_choices.lip_syncer_models,
            "weight_range": list(lip_syncer_choices.lip_syncer_weight_range)
        },
        "age_modifier": {
            "models": age_modifier_choices.age_modifier_models,
            "direction_range": list(age_modifier_choices.age_modifier_direction_range)
        },
        "expression_restorer": {
            "models": expression_restorer_choices.expression_restorer_models,
            "factor_range": list(expression_restorer_choices.expression_restorer_factor_range),
            "areas": expression_restorer_choices.expression_restorer_areas
        }
    }



