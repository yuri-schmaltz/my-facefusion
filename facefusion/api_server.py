import os
import shutil
import time
import pickle
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import anyio
import subprocess
import numpy

from facefusion import state_manager, execution, logger
import facefusion.metadata as metadata
from facefusion.jobs import job_manager, job_runner
from facefusion.filesystem import is_image, is_video, resolve_file_paths, get_file_name
from facefusion.processors.core import get_processors_modules, load_processor_module
from facefusion.scene_detector import get_scene_timeframes
from facefusion.face_clusterer import cluster_faces
from facefusion.auto_tuner import suggest_settings
from facefusion.orchestrator import get_orchestrator, RunRequest, JobStatus






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
    
    # Initialize Orchestrator and register event loop
    orch = get_orchestrator()
    try:
        loop = anyio.get_current_task().generator.gi_frame.f_code.co_name # complex way to get loop in async
        # simpler way in modern fastapi lifespan is just use asyncio.get_running_loop()
        import asyncio
        loop = asyncio.get_running_loop()
        orch.event_bus.set_event_loop(loop)
        logger.error(f"SUCCESS: Registered event loop {loop} with orchestrator", __name__)
    except Exception as e:
        logger.error(f"Failed to register event loop: {e}", __name__)
    
    
    # Initialize logger
    logger.init(state_manager.get_item('log_level') or 'info')
    
    # Initialize default state items
    from facefusion import choices
    
    if state_manager.get_item('download_providers') is None:
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
            state_manager.init_item('face_enhancer_model', 'codeformer')
        if state_manager.get_item('face_enhancer_blend') is None:
            state_manager.init_item('face_enhancer_blend', 80)
        if state_manager.get_item('face_enhancer_weight') is None:
            state_manager.init_item('face_enhancer_weight', 1.0)
    
        if state_manager.get_item('frame_enhancer_model') is None:
            state_manager.init_item('frame_enhancer_model', 'clear_reality_x4')
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
    
    # Global Progress Phase
    state_manager.init_item('current_job_phase', None)
    
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
@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    orch = get_orchestrator()
    job = orch.get_job(job_id)
    
    if not job:
         return {"job_id": job_id, "status": "unknown", "progress": 0.0}
         
    job_dict = job.to_dict()
    
    # Inject preview_url for UI backward compatibility
    if job.config and 'output_path' in job.config:
         from facefusion.api_server import get_preview
         import urllib.parse
         path = job.config['output_path']
         encoded_path = urllib.parse.quote(path)
         job_dict["preview_url"] = f"/files/preview?path={encoded_path}"
         
    return job_dict

from fastapi import BackgroundTasks

@app.post("/run")
async def run_job(background_tasks: BackgroundTasks):
    print("--- RUN JOB REQUEST RECEIVED ---")
    orch = get_orchestrator()
    
    # 1. Prepare Output Path
    output_path = state_manager.get_item('output_path')
    target_path = state_manager.get_item('target_path')
    
    if not target_path:
        raise HTTPException(status_code=400, detail="No target media selected. Please re-select the file.")

    # 2. Collect Args
    from facefusion.args import collect_step_args, collect_job_args
    step_args = collect_step_args()
    step_args.update(collect_job_args())
    
    if not output_path:
        # Generate temp output path if None
        extension = ".mp4"
        if target_path:
            _, ext = os.path.splitext(target_path)
            if ext:
                extension = ext
        # We will let RunRequest generate a job_id, but we need it for filename
        # So we generate one here or let orchestrator handle it.
        # RunRequest auto-generates if not provided.
        # Let's generate a basic unique string for filename
        req_id = str(int(time.time()))
        output_name = f"output_{req_id}{extension}"
        output_path = os.path.join(get_temp_path(), "api_outputs", output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    step_args['output_path'] = output_path
    
    # 3. Submit to Orchestrator
    try:
        request = RunRequest(
            source_paths=step_args.get('source_paths', []),
            target_path=step_args.get('target_path'),
            output_path=output_path,
            processors=state_manager.get_item('processors'),
            settings=step_args
        )
        
        job_id = orch.submit(request)
        print(f"Submitted Job ID: {job_id}")
        
        # 4. Start execution (non-blocking)
        if orch.run_job(job_id):
             return {
                "status": "queued",
                "job_id": job_id,
                "output_path": output_path
            }
        
        raise HTTPException(500, "Failed to start job")
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        with open("/tmp/facefusion_api_error.txt", "w") as f:
            f.write(tb)
        raise HTTPException(500, f"Job submission failed: {str(e)}")

@app.post("/stop")
def stop_processing():
    # Cancel all running jobs for now
    orch = get_orchestrator()
    running_jobs = orch.list_jobs(status=JobStatus.RUNNING)
    queued_jobs = orch.list_jobs(status=JobStatus.QUEUED)
    
    count = 0
    for job in running_jobs + queued_jobs:
        if orch.cancel_job(job.job_id):
            count += 1
            
    print(f"Stopped {count} jobs")
    return {"status": "stopping", "count": count}


@app.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    from fastapi.responses import StreamingResponse
    import json
    
    orch = get_orchestrator()
    
    async def event_generator():
        # Subscribe to new events
        # We need to handle client disconnects gracefully
        try:
             async for event in orch.event_bus.subscribe(job_id):
                data = json.dumps(event.to_dict())
                yield f"data: {data}\n\n"
        except Exception:
             pass
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
import asyncio
from typing import Set

class LogBroadcaster:
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()
        self.loop = None

    def set_loop(self, loop):
        self.loop = loop

    def broadcast(self, message: str):
        if not self.loop:
            return
        
        def push():
            for q in list(self.subscribers):
                try:
                    q.put_nowait(message)
                except asyncio.QueueFull:
                    pass
        
        self.loop.call_soon_threadsafe(push)

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.subscribers:
            self.subscribers.remove(q)

log_broadcaster = LogBroadcaster()

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            entry = self.format(record)
            log_broadcaster.broadcast(entry)
        except Exception:
            self.handleError(record)

# Attach handler to root logger or facefusion logger
queue_handler = QueueHandler()
queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger('facefusion').addHandler(queue_handler)
logging.getLogger().addHandler(queue_handler)

@app.websocket("/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    log_broadcaster.set_loop(asyncio.get_running_loop())
    q = await log_broadcaster.subscribe()
    try:
        while True:
            line = await q.get()
            await websocket.send_text(line)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        log_broadcaster.unsubscribe(q)

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
        "output_video_encoders": choices.output_video_encoders,
        "output_video_presets": choices.output_video_presets,
        "output_audio_encoders": choices.output_audio_encoders,
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
    import traceback
    from facefusion import face_analyser, state_manager, audio, logger
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

    # Helper function to encode frame
    def encode_frame(frame):
        _, buffer = cv2.imencode('.jpg', frame)
        b64 = base64.b64encode(buffer).decode('utf-8')
        return {"preview": f"data:image/jpeg;base64,{b64}"}

    # 2. Get Processors and Source
    processors = state_manager.get_item('processors')
    source_paths = state_manager.get_item('source_paths') or []
    
    # If no processors selected, return the original target frame
    if not processors:
        return encode_frame(vision_frame)
    
    # Load source frames (empty list if no sources - frame-only processors still work)
    source_vision_frames = read_static_images(source_paths) if source_paths else []
    
    # For images, use the target image as reference; for videos, use the reference frame
    if is_image(path):
        reference_vision_frame = vision_frame
    else:
        reference_frame_number = state_manager.get_item('reference_frame_number') or 0
        reference_vision_frame = read_video_frame(path, reference_frame_number)
    
    # 3. Process each processor with error handling
    temp_vision_frame = vision_frame.copy()
    temp_vision_mask = extract_vision_mask(temp_vision_frame)
    
    # Define processors that require source faces
    SOURCE_REQUIRED_PROCESSORS = ['face_swapper', 'deep_swapper', 'lip_syncer', 'makeup_transfer']
    
    for processor_name in processors:
        # Skip source-requiring processors if no source is provided
        if processor_name in SOURCE_REQUIRED_PROCESSORS and not source_vision_frames:
            continue
        
        try:
            processor_modules = get_processors_modules([processor_name])
            if not processor_modules:
                continue
                
            processor_module = processor_modules[0]
            
            # Ensure model is loaded for preview
            if not processor_module.pre_process('preview'):
                continue
            
            temp_vision_frame, temp_vision_mask = processor_module.process_frame({
                'reference_vision_frame': reference_vision_frame,
                'source_vision_frames': source_vision_frames,
                'source_audio_frame': audio.create_empty_audio_frame(),
                'source_voice_frame': audio.create_empty_audio_frame(),
                'target_vision_frame': vision_frame[:, :, :3],
                'temp_vision_frame': temp_vision_frame[:, :, :3],
                'temp_vision_mask': temp_vision_mask
            })
        except Exception as e:
            # Log error but continue with other processors
            logger.error(f'Preview processing error in {processor_name}: {str(e)}', __name__)
            traceback.print_exc()
            continue

    temp_vision_frame = conditional_merge_vision_mask(temp_vision_frame, temp_vision_mask)
    
    # 4. Return processed frame
    return encode_frame(temp_vision_frame)


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
        
        # If frame is black/empty, scan forward to find content (up to 120 frames/2-4 secs)
        if vision_frame is not None and not numpy.any(vision_frame):
             logger.info(f"Frame {frame_num} is empty (black). Scanning forward for content...", __name__)
             for i in range(1, 120):
                 next_frame = read_video_frame(path, frame_num + i)
                 if next_frame is not None and numpy.any(next_frame):
                      logger.info(f"Found content at frame {frame_num + i}", __name__)
                      vision_frame = next_frame
                      break
    
    if vision_frame is None:
         logger.error(f"Could not read frame from {path}", __name__)
         raise HTTPException(400, "Could not read frame")

    # Detect faces
    print(f"[DEBUG] Detecting faces in frame from {path}")
    faces = face_analyser.get_many_faces([vision_frame])
    print(f"[DEBUG] Found {len(faces)} faces")
    
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
    refine: bool = False    # Whether to run a refinement pass

@app.post("/api/v1/wizard/cluster")
async def wizard_cluster(req: WizardClusterRequest):
    if req.job_id not in analyzed_videos:
        raise HTTPException(404, "Analyzed data not found for this job_id")
        
    data = analyzed_videos[req.job_id]
    video_path = data.get("video_path")
    scenes = data.get("scenes", [])
    scene_faces = data.get("scene_faces", {})
    
    print(f"[WIZARD_CLUSTER] job_id={req.job_id}, video_path={video_path}, refine={req.refine}")
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
    print(f"[WIZARD_CLUSTER] Initial clusters formed: {len(clusters)}")

    if req.refine:
        # Import here to avoid circular dependencies if any
        from facefusion.face_clusterer import refine_clusters
        # Use a more aggressive threshold for refinement to merge similar faces
        clusters = refine_clusters(clusters, threshold=0.5)
        print(f"[WIZARD_CLUSTER] Refined clusters formed: {len(clusters)}")
    
    # Persist clusters to support manual operations
    analyzed_videos[req.job_id]['clusters'] = clusters
    # Verify persistence
    print(f"[WIZARD_CLUSTER] Persisted {len(clusters)} clusters for job {req.job_id}")

    
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

class WizardMergeRequest(BaseModel):
    job_id: str
    cluster_indices: List[int] # Indices of clusters to merge

@app.post("/api/v1/wizard/merge_clusters")
async def wizard_merge_clusters(req: WizardMergeRequest):
    if req.job_id not in analyzed_videos:
        raise HTTPException(404, "Analyzed data not found")
        
    data = analyzed_videos[req.job_id]
    if 'clusters' not in data:
        raise HTTPException(400, "No clusters found. Run clustering first.")
        
    clusters = data['clusters']
    
    # Sort indices in descending order to avoid index shifting problems if we pop
    # But actually we are building a new list.
    
    indices_to_merge = set(req.cluster_indices)
    if len(indices_to_merge) < 2:
        return {"error": "Need at least 2 clusters to merge"} # Or just return current
        
    new_clusters = []
    merged_group = []
    
    # Collect all faces from targeted clusters
    for i, cluster in enumerate(clusters):
        if i in indices_to_merge:
            merged_group.extend(cluster)
        else:
            new_clusters.append(cluster)
            
    # Append the combined group
    if merged_group:
         new_clusters.append(merged_group)
         
    # Update state
    data['clusters'] = new_clusters
    analyzed_videos[req.job_id]['clusters'] = new_clusters
    
    print(f"[WIZARD_MERGE] Merged indices {indices_to_merge} into one. Total clusters: {len(clusters)} -> {len(new_clusters)}")

    # Re-generate results format (similar to wizard_cluster)
    cluster_results = []
    # We need to access video properties for thumbnails
    video_path = data.get("video_path")
    scenes = data.get("scenes", [])
    
    # We need to map faces to scenes again or persist face_to_scene map.
    # Since we don't have the faces list here easily (we do inside clusters), we can re-create the map if needed,
    # OR we can just pick thumbnails naively.
    # Ideally we should reuse the logic. For now, let's copy the thumbnail logic briefly or extract it.
    # To save space, let's just assume we can get a representative face and find its scene.
    # But we don't have the face_to_scene map here.
    # We can rebuild it from scene_faces if needed, OR just skip the thumbnail for now (rendering a placeholders).
    # BETTER: Rebuild face_to_scene map.
    scene_faces = data.get("scene_faces", {})
    all_known_faces = []
    face_scene_map = []
    for scene_idx, faces in scene_faces.items():
        for face in faces:
            all_known_faces.append(face)
            face_scene_map.append(int(scene_idx))
    face_to_scene = {id(face): scene_idx for face, scene_idx in zip(all_known_faces, face_scene_map)}

    import cv2
    import base64
    from facefusion.vision import read_video_frame

    for c_idx, cluster in enumerate(new_clusters):
        rep_face = cluster[0]
        scene_idx = face_to_scene.get(id(rep_face), 0)
        
        thumbnail_b64 = None
        if video_path and scenes and scene_idx < len(scenes):
            start_frame, end_frame = scenes[scene_idx]
            middle_frame = start_frame + (end_frame - start_frame) // 2
            # Optimization: Cache thumbnails? For now, re-reading is safer/easier.
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


    return {"clusters": cluster_results}

@app.post("/api/v1/wizard/upload_source")
async def wizard_upload_source(job_id: str = Form(...), file: UploadFile = File(...)):
    if job_id not in analyzed_videos:
        raise HTTPException(404, "Job not found")
        
    import shutil
    import os
    
    # Create directory for sources
    base_dir = f"/tmp/facefusion/wizard/{job_id}/sources"
    os.makedirs(base_dir, exist_ok=True)
    
    file_path = os.path.join(base_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"path": file_path}

class WizardAssignmentRequest(BaseModel):
    job_id: str
    assignments: Dict[int, str] # cluster_idx -> source_path

@app.post("/api/v1/wizard/assignments")
async def wizard_assign_sources(req: WizardAssignmentRequest):
    if req.job_id not in analyzed_videos:
        raise HTTPException(404, "Job not found")
        
    analyzed_videos[req.job_id]['assignments'] = req.assignments
    print(f"[WIZARD] Stored {len(req.assignments)} assignments for job {req.job_id}")
    return {"status": "ok"}

class WizardSuggestRequest(BaseModel):
    job_id: str

@app.post("/api/v1/wizard/suggest")
async def wizard_suggest(req: WizardSuggestRequest):
    if req.job_id not in analyzed_videos:
        raise HTTPException(404, "Job not found")
        
    data = analyzed_videos[req.job_id]
    all_faces = []
    
    # Check if scene_faces exists
    if "scene_faces" in data:
        for faces in data["scene_faces"].values():
            all_faces.extend(faces)
            
    settings = suggest_settings(data.get("video_path", ""), all_faces)
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
    
    # --- Prepare Assignments & Overrides (Once per Job) ---
    overrides = {}
    assignments = data.get('assignments', {})
    if assignments:
        print(f"[WIZARD_GENERATE] Using {len(assignments)} explicit face assignments")
        
        # Prepare Reference Mode: Map Cluster Representative -> Source
        sorted_pairs = sorted(assignments.items(), key=lambda x: int(x[0]))
        
        source_paths = []
        reference_face_paths = []
        clusters = data.get('clusters', [])
        
        import cv2
        from facefusion.vision import read_video_frame
        
        # Helper to save reference face
        # We need a predictable path for references
        ref_dir = f"/tmp/facefusion/wizard/{req.job_id}/references"
        os.makedirs(ref_dir, exist_ok=True)
        
        scene_faces = data.get("scene_faces", {})
        scenes = data.get("scenes", [])
        
        for cluster_idx_str, source_path in sorted_pairs:
            cluster_idx = int(cluster_idx_str)
            if cluster_idx >= len(clusters):
                continue
                
            cluster = clusters[cluster_idx]
            if not cluster:
                continue
                
            # Use representative face from cluster
            rep_face = cluster[0]
            
            # Find a frame containing this face to extract usage reference
            # Optimally, we would have stored this, but we can search or trust the thumbnail logic.
            # Re-implementation of searching logic:
            target_frame_nr = 0
            found = False
            
            # Search in the scene faces map
            for s_idx, faces in scene_faces.items():
                for f in faces:
                    # Identity check: assumption is that face objects (or their properties) match
                    if f is rep_face: 
                         start, end = scenes[s_idx]
                         target_frame_nr = start + (end - start) // 2
                         found = True
                         break
                if found: break
            
            # Fallback if object identity fails (e.g. if objects were recreated/copied)
            if not found:
                 # Just take the middle frame of the first scene this cluster is known to be in?
                 # Since we don't have that map easily avail here, we skip.
                 # Actually, we can rely on the fact that existing logic works if identity is preserved.
                 # If not, this reference extraction might fail.
                 pass

            if found:
                vision_frame = read_video_frame(video_path, target_frame_nr)
                if vision_frame is not None:
                     box = rep_face.bounding_box
                     margin = 32
                     top = max(0, int(box[1]) - margin)
                     bottom = min(vision_frame.shape[0], int(box[3]) + margin)
                     left = max(0, int(box[0]) - margin)
                     right = min(vision_frame.shape[1], int(box[2]) + margin)
                     crop = vision_frame[top:bottom, left:right]
                     
                     ref_path = os.path.join(ref_dir, f"ref_{cluster_idx}.jpg")
                     cv2.imwrite(ref_path, crop)
                     
                     source_paths.append(source_path)
                     reference_face_paths.append(ref_path)

        if source_paths:
            overrides = {
                "source_paths": source_paths,
                "reference_face_paths": reference_face_paths,
                "face_selector_mode": "reference"
            }

    # --- Create Jobs for Each Scene ---
    scenes = data.get("scenes", [])
    created_jobs = []
    
    for i, (start_frame, end_frame) in enumerate(scenes):
        # Determine output path
        dir_name = os.path.dirname(video_path)
        base_name = os.path.basename(video_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_scene_{i+1}{ext}")
        
        # Generate unique job ID
        job_id = f"wizard_{int(time.time() * 1000)}_{i}"
        
        if not job_manager.create_job(job_id):
            raise HTTPException(500, f"Failed to create job {job_id}")
        
        # Apply settings and overrides
        job_manager.add_step(job_id, {
            "name": "process",
            "args": {
                "trim_frame_start": start_frame,
                "trim_frame_end": end_frame,
                "target_path": video_path,
                "output_path": output_path,
                **settings, 
                **overrides
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
