import os
import shutil
import time
import pickle
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
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
from facefusion.scene_detector import get_scene_timeframes
from facefusion.face_clusterer import cluster_faces
from facefusion.auto_tuner import suggest_settings






@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager for startup/shutdown events."""
    # Register keys by creating the program
    from facefusion import core
    core.create_program()
    
    # Startup
    jobs_path = os.path.join(get_temp_path(), "jobs")
    job_manager.init_jobs(jobs_path)
    load_wizard_state()

    
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
    source_paths: Optional[List[str]] = None
    target_path: Optional[str] = None
    output_path: Optional[str] = None
    # face selector
    face_selector_mode: Optional[str] = None
    face_selector_order: Optional[str] = None
    face_selector_gender: Optional[str] = None
    face_selector_race: Optional[str] = None
    face_selector_age_start: Optional[int] = None
    face_selector_age_end: Optional[int] = None
    reference_face_position: Optional[int] = None
    reference_face_distance: Optional[float] = None
    reference_frame_number: Optional[int] = None
    # watermark remover
    watermark_remover_model: Optional[str] = None
    watermark_remover_area_start: Optional[List[int]] = None
    watermark_remover_area_end: Optional[List[int]] = None
    # face masker
    face_mask_types: Optional[List[str]] = None
    face_mask_regions: Optional[List[str]] = None
    # output
    output_video_quality: Optional[int] = None
    output_video_encoder: Optional[str] = None
    # execution
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
    import os
    return {
        "name": metadata.get("name"),
        "version": metadata.get("version"),
        "execution_providers": execution.get_available_execution_providers(),
        "execution_devices": execution.detect_execution_devices(),
        "cpu_count": os.cpu_count() or 4
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
        'source_paths': config.source_paths,
        'target_path': config.target_path,
        'output_path': config.output_path,
        'face_selector_mode': config.face_selector_mode,
        'face_selector_order': config.face_selector_order,
        'face_selector_gender': config.face_selector_gender,
        'face_selector_race': config.face_selector_race,
        'face_selector_age_start': config.face_selector_age_start,
        'face_selector_age_end': config.face_selector_age_end,
        'reference_face_position': config.reference_face_position,
        'reference_face_distance': config.reference_face_distance,
        'reference_frame_number': config.reference_frame_number,
        'watermark_remover_model': config.watermark_remover_model,
        'watermark_remover_area_start': config.watermark_remover_area_start,
        'watermark_remover_area_end': config.watermark_remover_area_end,
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

@app.post("/stop")
def stop_processing():
    from facefusion import process_manager
    process_manager.stop()
    return {"status": "stopping"}

def process_job_background(job_id: str, output_path: str):
    print(f"Starting background processing for {job_id}")
    from facefusion.core import process_step
    
    # Define a progress callback helper
    def progress_callback(progress_float):
        update_job_progress(job_id, progress_float * 100)

    # Attach to state_manager so workflow can find it? 
    # Hack for now: We will attach it to state_manager temporarily for the workflow to discover
    # Force set in specific contexts to avoid detection issues
    from facefusion.state_manager import STATE_SET
    STATE_SET['cli']['current_job_progress_callback'] = progress_callback
    STATE_SET['ui']['current_job_progress_callback'] = progress_callback
    
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
    from facefusion.processors.modules.watermark_remover import choices as watermark_remover_choices

    return {
        "watermark_remover": {
            "models": watermark_remover_choices.watermark_remover_models
        },
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


@app.get("/api/v1/choices")
def get_global_choices():
    from facefusion import choices
    from facefusion.uis import choices as uis_choices
    return {
        "face_detector_models": choices.face_detector_models,
        "face_detector_set": choices.face_detector_set,
        "face_landmarker_models": choices.face_landmarker_models,
        "face_occluder_models": choices.face_occluder_models,
        "face_parser_models": choices.face_parser_models,
        "face_mask_types": choices.face_mask_types,
        "face_mask_regions": choices.face_mask_regions,
        "face_mask_areas": choices.face_mask_areas,
        "voice_extractor_models": choices.voice_extractor_models,
        "temp_frame_formats": choices.temp_frame_formats,
        "output_video_presets": choices.output_video_presets,
        "video_memory_strategies": choices.video_memory_strategies,
        "log_levels": choices.log_levels,
        "ui_workflows": choices.ui_workflows,
        "execution_providers": choices.execution_providers,
        "face_detector_angles": list(choices.face_detector_angles),
        "preview_modes": uis_choices.preview_modes,
        "preview_resolutions": uis_choices.preview_resolutions,
        "ranges": {
            "face_detector_score": list(choices.face_detector_score_range),
            "face_landmarker_score": list(choices.face_landmarker_score_range),
            "face_mask_blur": list(choices.face_mask_blur_range),
            "face_mask_padding": list(choices.face_mask_padding_range),
            "system_memory_limit": list(choices.system_memory_limit_range),
            "face_detector_margin": list(choices.face_detector_margin_range),
            "output_video_scale": list(choices.output_video_scale_range),
            "reference_face_distance": list(choices.reference_face_distance_range)
        }
    }

# --- Faces API ---

class FaceDetectRequest(BaseModel):
    path: str
    frame_number: int = 0
    time_seconds: float = None

@app.post("/preview")
def get_preview_endpoint(req: FaceDetectRequest):
    import cv2
    import base64
    from facefusion import face_analyser, state_manager, audio
    from facefusion.processors.core import get_processors_modules
    from facefusion.vision import read_static_image, read_video_frame, detect_video_fps, read_static_images, extract_vision_mask, conditional_merge_vision_mask
    
    path = req.path
    path = os.path.realpath(os.path.abspath(path.strip('"\'')))
    
    # 1. Get Target Frame
    vision_frame = None
    if is_image(path):
        vision_frame = read_static_image(path)
    elif is_video(path):
        fps = detect_video_fps(path) or 30.0
        frame_num = int(req.time_seconds * fps) if req.time_seconds is not None else req.frame_number
        vision_frame = read_video_frame(path, frame_num)
    
    if vision_frame is None:
        raise HTTPException(400, "Could not read target frame")

    # 2. Get Source and Reference
    source_paths = state_manager.get_item('source_paths')
    processors = state_manager.get_item('processors')
    
    # If no source or no processors, return the original target frame
    if not source_paths or not processors:
         _, buffer = cv2.imencode('.jpg', vision_frame)
         b64 = base64.b64encode(buffer).decode('utf-8')
         return {"preview": f"data:image/jpeg;base64,{b64}"}

    source_vision_frames = read_static_images(source_paths)
    reference_frame_number = state_manager.get_item('reference_frame_number')
    reference_vision_frame = read_video_frame(path, reference_frame_number)
    
    # 3. Process
    temp_vision_frame = vision_frame.copy()
    temp_vision_mask = extract_vision_mask(temp_vision_frame)
    
    for processor_module in get_processors_modules(processors):
        # Ensure model is loaded for preview
        processor_module.pre_process('preview')
        
        temp_vision_frame, temp_vision_mask = processor_module.process_frame(
        {
            'reference_vision_frame': reference_vision_frame,
            'source_vision_frames': source_vision_frames,
            'source_audio_frame': audio.create_empty_audio_frame(),
            'source_voice_frame': audio.create_empty_audio_frame(),
            'target_vision_frame': vision_frame[:, :, :3],
            'temp_vision_frame': temp_vision_frame[:, :, :3],
            'temp_vision_mask': temp_vision_mask
        })

    temp_vision_frame = conditional_merge_vision_mask(temp_vision_frame, temp_vision_mask)
    
    # 4. Return
    _, buffer = cv2.imencode('.jpg', temp_vision_frame)
    b64 = base64.b64encode(buffer).decode('utf-8')
    return {"preview": f"data:image/jpeg;base64,{b64}"}

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


# --- Wizard API ---

class WizardAnalyzeRequest(BaseModel):
    video_path: str

wizard_tasks = {}
wizard_suggestions = {}
analyzed_videos = {}

def get_wizard_state_path() -> str:
    from facefusion.state_manager import get_item
    jobs_path = get_item('jobs_path') or os.path.join(get_temp_path(), "jobs")
    return os.path.join(jobs_path, "wizard_state.pkl")

def save_wizard_state():
    try:
        state_path = get_wizard_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, 'wb') as f:
            pickle.dump({
                "wizard_tasks": wizard_tasks,
                "wizard_suggestions": wizard_suggestions,
                "analyzed_videos": analyzed_videos
            }, f)
        print(f"[WIZARD] State saved to {state_path}")
    except Exception as e:
        print(f"[WIZARD] Failed to save state: {e}")

def load_wizard_state():
    global wizard_tasks, wizard_suggestions, analyzed_videos
    try:
        state_path = get_wizard_state_path()
        if os.path.exists(state_path):
            with open(state_path, 'rb') as f:
                data = pickle.load(f)
                wizard_tasks = data.get("wizard_tasks", {})
                wizard_suggestions = data.get("wizard_suggestions", {})
                analyzed_videos = data.get("analyzed_videos", {})
            print(f"[WIZARD] State loaded from {state_path} ({len(wizard_tasks)} tasks)")
        else:
            print("[WIZARD] No saved state found.")
    except Exception as e:
        print(f"[WIZARD] Failed to load state: {e}")

def process_wizard_analysis(job_id: str, video_path: str):
    from facefusion.vision import read_video_frame
    from facefusion import face_analyser
    
    print(f"[WIZARD] Starting analysis for job {job_id} on {video_path}")
    try:
        wizard_tasks[job_id]["status"] = "detecting_scenes"
        save_wizard_state()
        print(f"[WIZARD] Job {job_id} set to detecting_scenes")
        
        def on_scenes_progress(progress):
            print(f"[WIZARD] Job {job_id} scene progress: {progress}")
            wizard_tasks[job_id]["progress"] = progress * 0.5 # Scene detection is 50%
            
        print(f"[WIZARD] Calling get_scene_timeframes...")
        scenes = get_scene_timeframes(video_path, progress_callback=on_scenes_progress)
        print(f"[WIZARD] Scenes detected: {len(scenes)}")
        
        wizard_tasks[job_id]["status"] = "analyzing_faces"
        save_wizard_state()
        print(f"[WIZARD] Job {job_id} set to analyzing_faces")
        scene_faces = {}
        total_scenes = len(scenes)
        
        for idx, (start, end) in enumerate(scenes):
            wizard_tasks[job_id]["progress"] = 0.5 + (idx / total_scenes) * 0.5
            middle_frame = start + (end - start) // 2
            vision_frame = read_video_frame(video_path, middle_frame)
            if vision_frame is not None:
                faces = face_analyser.get_many_faces([vision_frame])
                scene_faces[idx] = faces
                
        analyzed_videos[job_id] = {
            "video_path": video_path,
            "scenes": scenes,
            "scene_faces": scene_faces,
            "face_thumbnails": {}  # Will be populated during clustering
        }
        wizard_tasks[job_id]["status"] = "completed"
        wizard_tasks[job_id]["progress"] = 1.0
        save_wizard_state()
    except Exception as e:
        print(f"Wizard analysis failed: {e}")
        wizard_tasks[job_id]["status"] = "failed"
        wizard_tasks[job_id]["error"] = str(e)
        save_wizard_state()

@app.post("/api/v1/wizard/analyze")
async def wizard_analyze(req: WizardAnalyzeRequest, background_tasks: BackgroundTasks):
    video_path = os.path.realpath(os.path.abspath(req.video_path.strip('"\'')))
    if not os.path.exists(video_path):
        raise HTTPException(404, "Video not found")
        
    job_id = "wizard_" + str(int(time.time()))
    wizard_tasks[job_id] = {
        "status": "queued",
        "progress": 0.0
    }
    
    save_wizard_state()
    background_tasks.add_task(process_wizard_analysis, job_id, video_path)
    
    return {"job_id": job_id}

@app.get("/api/v1/wizard/progress/{job_id}")
async def wizard_progress(job_id: str):
    if job_id not in wizard_tasks:
        raise HTTPException(404, "Task not found")
    
    res = wizard_tasks[job_id].copy()
    if res["status"] == "completed":
        data = analyzed_videos.get(job_id, {})
        res["result"] = {
            "scenes_count": len(data.get("scenes", [])),
            "scenes": data.get("scenes", [])
        }
    return res

class WizardClusterRequest(BaseModel):
    job_id: str
    threshold: float = 0.4  # Cosine distance threshold for face similarity

@app.post("/api/v1/wizard/cluster")
async def wizard_cluster(req: WizardClusterRequest):
    if req.job_id not in analyzed_videos:
        raise HTTPException(404, "Analyzed data not found for this job_id")
        
    data = analyzed_videos[req.job_id]
    video_path = data.get("video_path")
    scenes = data.get("scenes", [])
    scene_faces = data.get("scene_faces", {})
    
    print(f"[WIZARD_CLUSTER] job_id={req.job_id}, video_path={video_path}")
    print(f"[WIZARD_CLUSTER] scenes count: {len(scenes)}, scene_faces keys: {list(scene_faces.keys())}")
    
    all_faces = []
    face_scene_map = []  # Track which scene each face came from
    
    for scene_idx, faces in scene_faces.items():
        print(f"[WIZARD_CLUSTER] scene {scene_idx}: {len(faces)} faces")
        for face in faces:
            all_faces.append(face)
            face_scene_map.append(int(scene_idx))
    
    print(f"[WIZARD_CLUSTER] Total faces collected: {len(all_faces)}")
    
    # Map face objects to their scene index using id() to avoid numpy comparison issues
    face_to_scene = {id(face): scene_idx for face, scene_idx in zip(all_faces, face_scene_map)}
        
    clusters = cluster_faces(all_faces, req.threshold)
    print(f"[WIZARD_CLUSTER] Clusters formed: {len(clusters)}")
    
    # Prepare response with thumbnails
    cluster_results = []
    import cv2
    import base64
    from facefusion.vision import read_video_frame
    
    for c_idx, cluster in enumerate(clusters):
        # Use first face as representative
        rep_face = cluster[0]
        
        # Find which scene this face came from using id()
        scene_idx = face_to_scene.get(id(rep_face), 0)
        
        # Get scene frame for thumbnail
        thumbnail_b64 = None
        if video_path and scenes and scene_idx < len(scenes):
            start_frame, end_frame = scenes[scene_idx]
            middle_frame = start_frame + (end_frame - start_frame) // 2
            vision_frame = read_video_frame(video_path, middle_frame)
            
            if vision_frame is not None:
                box = rep_face.bounding_box
                margin = 16
                top = max(0, int(box[1]) - margin)
                bottom = min(vision_frame.shape[0], int(box[3]) + margin)
                left = max(0, int(box[0]) - margin)
                right = min(vision_frame.shape[1], int(box[2]) + margin)
                
                crop = vision_frame[top:bottom, left:right]
                _, buffer = cv2.imencode('.jpg', crop)
                thumbnail_b64 = base64.b64encode(buffer).decode('utf-8')
        
        cluster_results.append({
            "cluster_index": c_idx,
            "face_count": len(cluster),
            "thumbnail": f"data:image/jpeg;base64,{thumbnail_b64}" if thumbnail_b64 else None,
            "representative": {
                "gender": str(rep_face.gender),
                "age": int(rep_face.age.start if isinstance(rep_face.age, range) else rep_face.age),
                "race": str(rep_face.race)
            }
        })
        
    return {"clusters": cluster_results}

@app.post("/api/v1/wizard/suggest")
async def wizard_suggest(req: WizardClusterRequest):
    if req.job_id not in analyzed_videos:
        raise HTTPException(404, "Analyzed data not found")
        
    data = analyzed_videos[req.job_id]
    all_faces = []
    for faces in data["scene_faces"].values():
        all_faces.extend(faces)
        
    settings = suggest_settings(data["video_path"], all_faces)
    wizard_suggestions[req.job_id] = settings
    save_wizard_state()
    return {"suggestions": settings}


class WizardGenerateRequest(BaseModel):
    job_id: str

@app.post("/api/v1/wizard/generate")
async def wizard_generate(req: WizardGenerateRequest):
    if req.job_id not in analyzed_videos:
          raise HTTPException(404, "Data not found")
          
    data = analyzed_videos[req.job_id]
    video_path = data.get("video_path")  # Get from analyzed_videos, not wizard_tasks
    
    if not video_path:
        raise HTTPException(400, "Video path not found in analyzed data")
    
    # Check if we have suggestions
    settings = wizard_suggestions.get(req.job_id, {})
    
    # Create jobs for each scene
    scenes = data.get("scenes", [])
    created_jobs = []
    
    for i, (start_frame, end_frame) in enumerate(scenes):
        # Create a job for this scene
        # We'll use the suggested settings + clip trimming
        
        # Determine output path
        dir_name = os.path.dirname(video_path)
        base_name = os.path.basename(video_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_scene_{i+1}{ext}")
        
        # Generate unique job ID (create_job takes the ID, not a display name)
        job_id = f"wizard_{int(time.time() * 1000)}_{i}"
        
        if not job_manager.create_job(job_id):
            raise HTTPException(500, f"Failed to create job {job_id}")
        
        # Apply suggested settings to the job
        # Note: job_manager doesn't support applying a dict directly yet in this mock,
        # but normally we would update the job's config.
        # For now, we'll just queue it with the trim arguments.
        
        # Ideally, we would clone the current global settings AND applied wizard settings
        # to this specific job. 
        # For this implementation, we will assume global state is used for execution 
        # but we set the specific trim arguments.
        
        job_manager.add_step(job_id, {
            "name": "process",
            "args": {
                "trim_frame_start": start_frame,
                "trim_frame_end": end_frame,
                "target_path": video_path,
                "output_path": output_path,
                **settings # Apply optimized settings
            }
        })
        
        created_jobs.append(job_id)
        
    return {"created_jobs": created_jobs, "count": len(created_jobs)}


# ========================================
# JOB MANAGEMENT API
# ========================================

@app.get("/api/v1/jobs")
async def list_jobs():
    """List all jobs with their status and details."""
    all_jobs = []
    
    for status in ['drafted', 'queued', 'completed', 'failed']:
        job_ids = job_manager.find_job_ids(status)
        for job_id in job_ids:
            job_data = job_manager.read_job_file(job_id)
            if job_data:
                steps = job_data.get('steps', [])
                # Extract key info from first step if available
                first_step_args = steps[0].get('args', {}) if steps else {}
                all_jobs.append({
                    'id': job_id,
                    'status': status,
                    'date_created': job_data.get('date_created'),
                    'date_updated': job_data.get('date_updated'),
                    'step_count': len(steps),
                    'target_path': first_step_args.get('target_path'),
                    'output_path': first_step_args.get('output_path'),
                })
    
    return {"jobs": all_jobs}


@app.get("/api/v1/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get full details of a specific job including all steps and settings."""
    job_data = job_manager.read_job_file(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Find job status
    job_status = None
    for status in ['drafted', 'queued', 'completed', 'failed']:
        if job_id in job_manager.find_job_ids(status):
            job_status = status
            break
    
    steps = job_data.get('steps', [])
    
    # Build detailed response
    detailed_steps = []
    for idx, step in enumerate(steps):
        args = step.get('args', {})
        detailed_steps.append({
            'index': idx,
            'status': step.get('status', 'unknown'),
            'target_path': args.get('target_path'),
            'output_path': args.get('output_path'),
            'source_paths': args.get('source_paths', []),
            'processors': args.get('processors', []),
            'face_selector_mode': args.get('face_selector_mode'),
            'face_selector_gender': args.get('face_selector_gender'),
            'face_selector_age_start': args.get('face_selector_age_start'),
            'face_selector_age_end': args.get('face_selector_age_end'),
            'output_video_quality': args.get('output_video_quality'),
            'output_video_encoder': args.get('output_video_encoder'),
            'execution_providers': args.get('execution_providers', []),
            'trim_frame_start': args.get('trim_frame_start'),
            'trim_frame_end': args.get('trim_frame_end'),
            # Include all other args for full transparency
            'all_args': args,
        })
    
    return {
        'id': job_id,
        'status': job_status,
        'version': job_data.get('version'),
        'date_created': job_data.get('date_created'),
        'date_updated': job_data.get('date_updated'),
        'step_count': len(steps),
        'steps': detailed_steps,
    }


class SubmitJobsRequest(BaseModel):
    job_ids: List[str]

@app.post("/api/v1/jobs/submit")
async def submit_jobs(req: SubmitJobsRequest):
    """Submit drafted jobs to the queue for processing."""
    results = {}
    for job_id in req.job_ids:
        success = job_manager.submit_job(job_id)
        results[job_id] = success
    
    return {"results": results, "submitted": sum(1 for v in results.values() if v)}


class UnqueueJobsRequest(BaseModel):
    job_ids: List[str]

@app.post("/api/v1/jobs/unqueue")
async def unqueue_jobs(req: UnqueueJobsRequest):
    """Return queued jobs back to drafted status."""
    results = {}
    for job_id in req.job_ids:
        queued_job_ids = job_manager.find_job_ids('queued')
        if job_id in queued_job_ids:
            # Move job from queued back to drafted
            success = job_manager.set_steps_status(job_id, 'drafted') and job_manager.move_job_file(job_id, 'drafted')
            results[job_id] = success
        else:
            results[job_id] = False
    
    return {"results": results, "unqueued": sum(1 for v in results.values() if v)}


class DeleteJobsRequest(BaseModel):
    job_ids: List[str]

@app.delete("/api/v1/jobs")
async def delete_jobs(req: DeleteJobsRequest):
    """Delete specified jobs."""
    results = {}
    for job_id in req.job_ids:
        success = job_manager.delete_job(job_id)
        results[job_id] = success
    
    return {"results": results, "deleted": sum(1 for v in results.values() if v)}


@app.post("/api/v1/jobs/run")
async def run_queued_jobs(background_tasks: BackgroundTasks):
    """Run all queued jobs in the background."""
    from facefusion.core import process_step
    
    queued_job_ids = job_manager.find_job_ids('queued')
    
    if not queued_job_ids:
        return {"status": "no_jobs", "message": "No queued jobs to run"}
    
    # Process each job in background
    for job_id in queued_job_ids:
        job_data = job_manager.read_job_file(job_id)
        if job_data:
            steps = job_data.get('steps', [])
            output_path = steps[0].get('args', {}).get('output_path', '') if steps else ''
            
            # Initialize progress tracking
            job_progress[job_id] = {
                "status": "running",
                "progress": 0.0,
                "preview_url": None
            }
            
            # Add to background tasks
            background_tasks.add_task(process_job_background, job_id, output_path)
    
    return {
        "status": "started",
        "jobs_started": len(queued_job_ids),
        "job_ids": queued_job_ids
    }


@app.get("/api/v1/jobs/status")
async def get_queue_status():
    """Get the current status of all jobs being processed."""
    return {
        "running": {jid: data for jid, data in job_progress.items() if data.get("status") == "running"},
        "completed": len([1 for data in job_progress.values() if data.get("status") == "completed"]),
        "failed": len([1 for data in job_progress.values() if data.get("status") == "failed"]),
    }


# Global cache
# analyzed_videos is now declared above with persistence helpers
