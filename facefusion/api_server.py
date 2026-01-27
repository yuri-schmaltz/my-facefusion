import os
import shutil
import time
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import anyio
import subprocess

from facefusion import state_manager, execution
import facefusion.metadata as metadata
from facefusion.jobs import job_manager, job_runner
from facefusion.filesystem import is_image, is_video, resolve_file_paths, get_file_name
from facefusion.processors.core import get_processors_modules, load_processor_module

print(f"DEBUG: api_server.py imported. metadata type: {type(metadata)}")
if metadata is None:
    print("DEBUG: metadata is None! Trying to reload or check sys.modules")
    import sys
    print(f"DEBUG: sys.modules['facefusion.metadata']: {sys.modules.get('facefusion.metadata')}")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager for startup/shutdown events."""
    # Register keys by creating the program
    from facefusion import core
    core.create_program()
    
    # Startup
    jobs_path = os.path.join(get_temp_path(), "jobs")
    job_manager.init_jobs(jobs_path)

    
    # Initialize default state items
    if state_manager.get_item('download_providers') is None:
        from facefusion import choices
        state_manager.init_item('download_providers', choices.download_providers)
        
        if state_manager.get_item('execution_providers') is None:
            state_manager.init_item('execution_providers', ['cpu'])
            
        if state_manager.get_item('execution_device_ids') is None:
            state_manager.init_item('execution_device_ids', [0])
    
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
    
        # Ensure temp_path is set
        if state_manager.get_item('temp_path') is None:
            state_manager.init_item('temp_path', tempfile.gettempdir())
    
        # Common Face Detector settings
        if state_manager.get_item('face_detector_model') is None:
            state_manager.init_item('face_detector_model', 'yolo_face')
        if state_manager.get_item('face_detector_size') is None:
            state_manager.init_item('face_detector_size', '640x640')
        if state_manager.get_item('face_detector_angles') is None:
            state_manager.init_item('face_detector_angles', [0])
        if state_manager.get_item('face_detector_margin') is None:
            state_manager.init_item('face_detector_margin', [0, 0, 0, 0])
        if state_manager.get_item('face_detector_score') is None:
            state_manager.init_item('face_detector_score', 0.5)
    
        # Face Landmarker settings
        if state_manager.get_item('face_landmarker_model') is None:
            state_manager.init_item('face_landmarker_model', '2dfan4')
        if state_manager.get_item('face_landmarker_score') is None:
            state_manager.init_item('face_landmarker_score', 0.5)
    
        # Face Selector settings
        if state_manager.get_item('face_selector_order') is None:
            state_manager.init_item('face_selector_order', 'large-small')
        if state_manager.get_item('reference_face_position') is None:
            state_manager.init_item('reference_face_position', 0)
        if state_manager.get_item('reference_face_distance') is None:
            state_manager.init_item('reference_face_distance', 0.6)
        if state_manager.get_item('reference_frame_number') is None:
            state_manager.init_item('reference_frame_number', 0)
    
        # Face Mask settings
        if state_manager.get_item('face_occluder_model') is None:
            state_manager.init_item('face_occluder_model', 'xseg_1')
        if state_manager.get_item('face_parser_model') is None:
            state_manager.init_item('face_parser_model', 'bisenet_resnet_34')
        if state_manager.get_item('face_mask_areas') is None:
            from facefusion import choices
            state_manager.init_item('face_mask_areas', choices.face_mask_areas)
        if state_manager.get_item('face_mask_blur') is None:
            state_manager.init_item('face_mask_blur', 0.3)
        if state_manager.get_item('face_mask_padding') is None:
            state_manager.init_item('face_mask_padding', [0, 0, 0, 0])
    
        # Voice settings
        if state_manager.get_item('voice_extractor_model') is None:
            state_manager.init_item('voice_extractor_model', 'kim_vocal_2')
    
        # Output / Temp settings
        if state_manager.get_item('temp_frame_format') is None:
            state_manager.init_item('temp_frame_format', 'png')
        if state_manager.get_item('output_image_quality') is None:
            state_manager.init_item('output_image_quality', 80)
        if state_manager.get_item('output_image_scale') is None:
            state_manager.init_item('output_image_scale', 1.0)
        if state_manager.get_item('output_audio_quality') is None:
            state_manager.init_item('output_audio_quality', 80)
        if state_manager.get_item('output_video_preset') is None:
            state_manager.init_item('output_video_preset', 'veryfast')
        if state_manager.get_item('output_video_scale') is None:
            state_manager.init_item('output_video_scale', 1.0)
    
        if state_manager.get_item('processors') is None:
            state_manager.init_item('processors', [])
        
        # Initialize processor-specific defaults
        if state_manager.get_item('face_swapper_model') is None:
            state_manager.init_item('face_swapper_model', 'hyperswap_1a_256')
        if state_manager.get_item('face_swapper_pixel_boost') is None:
            state_manager.init_item('face_swapper_pixel_boost', '256x256')
        if state_manager.get_item('face_swapper_weight') is None:
            state_manager.init_item('face_swapper_weight', 0.5)
            
        if state_manager.get_item('face_enhancer_model') is None:
            state_manager.init_item('face_enhancer_model', 'gfpgan_1.4')
        if state_manager.get_item('face_enhancer_blend') is None:
            state_manager.init_item('face_enhancer_blend', 80)
        if state_manager.get_item('face_enhancer_weight') is None:
            state_manager.init_item('face_enhancer_weight', 1.0)
    
        if state_manager.get_item('frame_enhancer_model') is None:
            state_manager.init_item('frame_enhancer_model', 'realsr_x2_clear')
        if state_manager.get_item('frame_enhancer_blend') is None:
            state_manager.init_item('frame_enhancer_blend', 80)
            
        if state_manager.get_item('lip_syncer_model') is None:
            state_manager.init_item('lip_syncer_model', 'wav2lip_gan')
        
        if state_manager.get_item('age_modifier_model') is None:
            state_manager.init_item('age_modifier_model', 'styleganex_age')
        if state_manager.get_item('age_modifier_direction') is None:
            state_manager.init_item('age_modifier_direction', 0)
            
        if state_manager.get_item('expression_restorer_model') is None:
            state_manager.init_item('expression_restorer_model', 'live_portrait')
        if state_manager.get_item('expression_restorer_factor') is None:
            state_manager.init_item('expression_restorer_factor', 80)
        
        yield  # Application runs here
        
        # Shutdown - cleanup if needed
        pass



app = FastAPI(
    title="FaceFusion API",
    version="2.0.0",
    description="API for FaceFusion 2.0 (React + FastAPI)",
    lifespan=lifespan
)

# CORS configuration - configurable via environment variable
# Default: localhost only. Set CORS_ORIGINS=http://host1,http://host2 for multiple origins
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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

    class Config:
        extra = "allow"

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
        "execution_devices": execution.detect_execution_devices()
    }

@app.get("/system/help")
def get_help():
    """Returns help text for all configuration keys for tooltips."""
    from facefusion import translator, jobs
    help_dict = {}
    
    # Common keys from job_store
    all_keys = jobs.job_store.get_job_keys() + jobs.job_store.get_step_keys()
    
    for key in all_keys:
        # Try to find help in translator
        # Most keys are prefixed with 'help.'
        help_text = translator.get(f"help.{key}")
        if help_text:
            help_dict[key] = help_text
        else:
            # Try without prefix
            help_text = translator.get(key)
            if help_text:
                help_dict[key] = help_text
                
    return help_dict

@app.get("/system/select-file")
async def select_file(multiple: bool = False, initial_path: Optional[str] = None):
    """Triggers a native OS file selection dialog using Zenity."""
    def run_zenity():
        command = ["zenity", "--file-selection", "--title=Select Media"]
        if multiple:
            command.append("--multiple")
            command.append("--separator=|")
        if initial_path and os.path.exists(initial_path):
            command.append(f"--filename={initial_path}")
        
        try:
            # Set timeout to avoid hanging if zenity fails to show
            return subprocess.check_output(command, stderr=subprocess.DEVNULL).decode().strip()
        except subprocess.CalledProcessError:
            return ""

    result = await anyio.to_thread.run_sync(run_zenity)
    
    if not result:
        return {"path": None, "paths": []}
    
    if multiple:
        paths = result.split("|")
        return {"path": paths[0] if paths else None, "paths": paths}
    return {"path": result, "paths": [result]}

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
    from facefusion.args import collect_step_args, collect_job_args
    # Return all step and job args for the UI to stay in sync
    config_data = collect_step_args()
    config_data.update(collect_job_args())
    return config_data

@app.post("/config")
def update_config(config: ConfigUpdate):
    # Handle explicit fields
    update_map = {
        'processors': config.processors,
        'output_path': config.output_path,
        'face_selector_mode': config.face_selector_mode,
        'face_mask_types': config.face_mask_types,
        'face_mask_regions': config.face_mask_regions,
        'output_video_quality': config.output_video_quality,
        'output_video_encoder': config.output_video_encoder,
        'execution_providers': config.execution_providers,
        'execution_thread_count': config.execution_thread_count,
        'execution_queue_count': config.execution_queue_count,
    }
    
    for key, value in update_map.items():
        if value is not None:
            state_manager.set_item(key, value)
            
    # Handle extra fields (like processor-specific settings)
    extra_data = config.model_extra or {}
    for key, value in extra_data.items():
        state_manager.set_item(key, value)

    if config.settings:
        for key, value in config.settings.items():
            state_manager.set_item(key, value)
            
    return {"status": "updated", "current_state": get_config()}

# Note: File upload functionality replaced by FileBrowser component + /filesystem/list API
# Users select files from the server filesystem directly via the FileBrowserDialog
# Note: Startup initialization is handled by the lifespan context manager above

# --- Job Progress & Status Management ---
# Global shared state for job progress
job_progress = {}

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id not in job_progress:
         # Try to load from disk via job_manager if not in memory
         status = "unknown"
         # For now simple check
         return {"job_id": job_id, "status": "unknown", "progress": 0.0}
    return job_progress[job_id]


def update_job_progress(job_id: str, progress: float):
    if job_id in job_progress:
        job_progress[job_id]["progress"] = progress

from fastapi import BackgroundTasks

@app.post("/run")
async def run_job(background_tasks: BackgroundTasks):
    print("--- RUN JOB REQUEST RECEIVED ---")
    # 1. Prepare Job ID e Output Path
    job_id = "job_" + str(int(time.time()))
    print(f"Generated Job ID: {job_id}")
    
    # Initialize progress tracking
    job_progress[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0
    }

    # Check if output path is set, else generate one
    output_path = state_manager.get_item('output_path')
    target_path = state_manager.get_item('target_path')
    
    if not target_path:
        raise HTTPException(status_code=400, detail="No target media selected. Please re-select the file.")

    if not output_path:
        extension = ".mp4" # Default fallback
        if target_path:
            _, ext = os.path.splitext(target_path)
            if ext:
                extension = ext
                
        output_name = f"output_{job_id}{extension}"
        output_path = os.path.join(get_temp_path(), "api_outputs", output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 2. Collect Args
    from facefusion.args import collect_step_args, collect_job_args
    step_args = collect_step_args()
    step_args.update(collect_job_args())
    step_args['output_path'] = output_path
    
    # 3. Create Job (Synchronous setup)
    if job_manager.create_job(job_id):
        if job_manager.add_step(job_id, step_args):
            if job_manager.submit_job(job_id):
                # 4. Run Job Asynchronously
                job_progress[job_id]["status"] = "processing"
                background_tasks.add_task(process_job_background, job_id, output_path)
                return {
                    "status": "processing",
                    "job_id": job_id,
                    "output_path": output_path
                }

    job_progress[job_id]["status"] = "failed"
    raise HTTPException(500, "Job creation failed")

def process_job_background(job_id: str, output_path: str):
    print(f"Starting background processing for {job_id}")
    from facefusion.core import process_step
    
    # Define a progress callback helper
    def progress_callback(progress_float):
        update_job_progress(job_id, progress_float * 100)

    # Attach to state_manager so workflow can find it? 
    # Better: Patch state_manager or use a global in api_server referenced by workflow?
    # Since workflow is in another storage, we need a way to pass this.
    # Hack for now: We will attach it to state_manager temporarily for the workflow to discover
    state_manager.set_item('current_job_progress_callback', progress_callback)

    try:
        success = job_runner.run_job(job_id, process_step)
        if success:
            job_progress[job_id]["status"] = "completed"
            job_progress[job_id]["progress"] = 100.0
            job_progress[job_id]["preview_url"] = f"/files/preview?path={output_path}"
        else:
            job_progress[job_id]["status"] = "failed"
    except Exception as e:
        print(f"Background Job Failed: {e}")
        job_progress[job_id]["status"] = "failed"

@app.get("/files/preview")
def get_preview(path: str):
    """
    Hardened preview endpoint: Only allows files within temp_path, home, or project root.
    Uses realpath to resolve symlinks and prevent symlink-based traversal attacks.
    """
    # Resolve symlinks BEFORE path validation to prevent symlink attacks
    path = os.path.realpath(os.path.abspath(path.strip('"\'')))
    
    # Allow access only to temp_path, home, or project root
    allowed_roots = [
        os.path.realpath(os.path.abspath(get_temp_path())), 
        os.path.realpath(os.path.abspath(os.path.expanduser("~"))),
        os.path.realpath(os.path.abspath(os.getcwd()))
    ]
    
    if any(path.startswith(root) for root in allowed_roots):
        if os.path.exists(path) and os.path.isfile(path):
            return FileResponse(path)
            
    raise HTTPException(status_code=403, detail="Access denied")
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
    return {
        "items": items,
        "path": resolved_path,
        "parent": parent
    }
@app.get("/processors/choices")
def get_processor_choices():
    from facefusion.processors.modules.face_swapper import choices as face_swapper_choices
    from facefusion.processors.modules.face_enhancer import choices as face_enhancer_choices
    from facefusion.processors.modules.frame_enhancer import choices as frame_enhancer_choices
    from facefusion.processors.modules.lip_syncer import choices as lip_syncer_choices
    from facefusion.processors.modules.age_modifier import choices as age_modifier_choices
    from facefusion.processors.modules.expression_restorer import choices as expression_restorer_choices
    from facefusion.processors.modules.face_debugger import choices as face_debugger_choices
    from facefusion.processors.modules.face_editor import choices as face_editor_choices
    from facefusion.processors.modules.frame_colorizer import choices as frame_colorizer_choices
    from facefusion.processors.modules.background_remover import choices as background_remover_choices
    from facefusion.processors.modules.deep_swapper import choices as deep_swapper_choices

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
            "factor_range": list(expression_restorer_choices.expression_restorer_factor_range)
        },
        "face_debugger": {
            "items": face_debugger_choices.face_debugger_items
        },
        "face_editor": {
            "models": face_editor_choices.face_editor_models,
            "eyebrow_direction_range": list(face_editor_choices.face_editor_eyebrow_direction_range),
            "eye_gaze_horizontal_range": list(face_editor_choices.face_editor_eye_gaze_horizontal_range),
            "eye_gaze_vertical_range": list(face_editor_choices.face_editor_eye_gaze_vertical_range),
            "eye_open_ratio_range": list(face_editor_choices.face_editor_eye_open_ratio_range),
            "lip_open_ratio_range": list(face_editor_choices.face_editor_lip_open_ratio_range),
            "mouth_grim_range": list(face_editor_choices.face_editor_mouth_grim_range),
            "mouth_pout_range": list(face_editor_choices.face_editor_mouth_pout_range),
            "mouth_purse_range": list(face_editor_choices.face_editor_mouth_purse_range),
            "mouth_smile_range": list(face_editor_choices.face_editor_mouth_smile_range),
            "mouth_position_horizontal_range": list(face_editor_choices.face_editor_mouth_position_horizontal_range),
            "mouth_position_vertical_range": list(face_editor_choices.face_editor_mouth_position_vertical_range),
            "head_pitch_range": list(face_editor_choices.face_editor_head_pitch_range),
            "head_yaw_range": list(face_editor_choices.face_editor_head_yaw_range),
            "head_roll_range": list(face_editor_choices.face_editor_head_roll_range)
        },
        "frame_colorizer": {
            "models": frame_colorizer_choices.frame_colorizer_models,
            "sizes": frame_colorizer_choices.frame_colorizer_sizes,
            "blend_range": list(frame_colorizer_choices.frame_colorizer_blend_range)
        },
        "background_remover": {
            "models": background_remover_choices.background_remover_models,
            # "color_range": list(background_remover_choices.background_remover_color_range) # Skipping color for now as UI doesn't support it well
        },
        "deep_swapper": {
            "models": deep_swapper_choices.deep_swapper_models,
            "morph_range": list(deep_swapper_choices.deep_swapper_morph_range)
        }
    }


# --- Faces API ---

class FaceDetectRequest(BaseModel):
    path: str
    frame_number: int = 0
    time_seconds: float = None

@app.post("/faces/detect")
def detect_faces_endpoint(req: FaceDetectRequest):
    import cv2
    import base64
    from facefusion import face_analyser
    
    path = req.path
    # Security check using existing preview logic
    path = os.path.realpath(os.path.abspath(path.strip('"\'')))
    allowed_roots = [
        os.path.realpath(os.path.abspath(get_temp_path())),
        os.path.realpath(os.path.abspath(os.path.expanduser("~"))),
        os.path.realpath(os.path.abspath(os.getcwd()))
    ]
    if not any(path.startswith(root) for root in allowed_roots) or not os.path.exists(path):
         raise HTTPException(status_code=403, detail="Access denied or file not found")

    vision_frame = None
    if is_image(path):
        from facefusion.vision import read_static_image
        vision_frame = read_static_image(path)
    elif is_video(path):
        from facefusion.vision import read_video_frame, detect_video_fps
        frame_num = req.frame_number
        if req.time_seconds is not None:
             fps = detect_video_fps(path) or 30.0
             frame_num = int(req.time_seconds * fps)
        vision_frame = read_video_frame(path, frame_num)
    
    if vision_frame is None:
         raise HTTPException(400, "Could not read frame")

    # Detect faces
    faces = face_analyser.get_many_faces([vision_frame])
    
    results = []
    for idx, face in enumerate(faces):
        # Create crop
        box = face.bounding_box
        margin = 32
        top = max(0, int(box[1]) - margin)
        bottom = min(vision_frame.shape[0], int(box[3]) + margin)
        left = max(0, int(box[0]) - margin)
        right = min(vision_frame.shape[1], int(box[2]) + margin)
        
        crop = vision_frame[top:bottom, left:right]
        
        # Encode
        _, buffer = cv2.imencode('.jpg', crop)
        b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Handle types safely
        age = face.age.start if isinstance(face.age, range) else int(face.age)
        gender = str(face.gender)
        race = str(face.race)
        score = float(face.score_set.get('detector', 0.0))

        results.append({
            "index": idx,
            "score": score,
            "gender": gender,
            "age": age,
            "race": race,
            "thumbnail": f"data:image/jpeg;base64,{b64}"
        })
        
    return {"faces": results}
