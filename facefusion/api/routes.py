import os
import shutil
import uuid
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from facefusion import state_manager
from facefusion.execution import get_available_execution_providers, detect_static_execution_devices
from facefusion.filesystem import resolve_file_paths, get_file_name, create_directory
from facefusion.processors.core import get_processors_modules
from facefusion.jobs import job_manager, job_runner, job_helper
from facefusion.args import collect_step_args
from facefusion.core import process_step
from facefusion.api.database import get_db, JobModel

router = APIRouter()



class JobCreateRequest(BaseModel):
    source_paths: List[str]
    target_path: str
    face_swapper_weight: Optional[float] = 0.5
    face_mask_blur: Optional[float] = 0.3
    detection_threshold: Optional[float] = 0.5
    smoothing: Optional[int] = 5
    processors: Optional[List[str]] = ["face_swapper"]
    output_format: Optional[str] = "mp4"


@router.get("/hardware/providers")
def get_hardware_providers() -> List[str]:
    """
    Retorna todos os provedores de execução (hardware acceleration) disponíveis na máquina.
    """
    try:
        return get_available_execution_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler provedores de hardware: {str(e)}")


@router.get("/hardware/devices")
def get_hardware_devices() -> List[Dict[str, Any]]:
    """
    Retorna detalhes de temperatura, memória e uso dos dispositivos NVIDIA (GPUs) detectados.
    """
    try:
        devices = detect_static_execution_devices()
        return [dict(device) for device in devices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao detectar dispositivos NVIDIA: {str(e)}")


@router.get("/processors/list")
def get_available_processors() -> List[str]:
    """
    Retorna a lista de processadores de frame disponíveis no sistema.
    """
    try:
        processors_paths = resolve_file_paths("facefusion/processors/modules")
        return [get_file_name(path) for path in processors_paths if get_file_name(path)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao varrer processadores: {str(e)}")


@router.get("/config")
def get_current_config() -> Dict[str, Any]:
    """
    Retorna as configurações e o estado global atual da aplicação em execução.
    """
    try:
        return {
            "temp_path": state_manager.get_item("temp_path"),
            "jobs_path": state_manager.get_item("jobs_path"),
            "log_level": state_manager.get_item("log_level"),
            "execution_providers": state_manager.get_item("execution_providers"),
            "execution_thread_count": state_manager.get_item("execution_thread_count"),
            "video_memory_strategy": state_manager.get_item("video_memory_strategy"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler configuração do estado: {str(e)}")


@router.post("/media/upload")
def upload_media(file: UploadFile = File(...)):
    """
    Faz o upload de uma imagem ou vídeo para a pasta temporária de jobs.
    """
    try:
        jobs_path = state_manager.get_item("jobs_path") or ".jobs"
        uploads_dir = os.path.join(jobs_path, "uploads")
        create_directory(uploads_dir)
        
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "file_path": os.path.abspath(file_path),
            "filename": file.filename,
            "unique_filename": unique_filename,
            "url": f"/api/media/upload/{unique_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload da mídia: {str(e)}")


@router.get("/media/upload/{filename}")
def get_upload_file(filename: str):
    """
    Retorna um arquivo de mídia enviado para a pasta temporária.
    """
    jobs_path = state_manager.get_item("jobs_path") or ".jobs"
    uploads_dir = os.path.abspath(os.path.join(jobs_path, "uploads"))
    file_path = os.path.abspath(os.path.join(uploads_dir, filename))
    
    if not file_path.startswith(uploads_dir):
        raise HTTPException(status_code=400, detail="Caminho de arquivo inválido")
        
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Arquivo de mídia não encontrado")


@router.get("/media/output/{filename}")
def get_output_file(filename: str):
    """
    Retorna o arquivo final gerado pelo processamento.
    """
    jobs_path = state_manager.get_item("jobs_path") or ".jobs"
    outputs_dir = os.path.abspath(os.path.join(jobs_path, "outputs"))
    file_path = os.path.abspath(os.path.join(outputs_dir, filename))
    
    if not file_path.startswith(outputs_dir):
        raise HTTPException(status_code=400, detail="Caminho de arquivo inválido")
        
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Arquivo de mídia não encontrado")


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Retorna a lista de todas as tarefas (jobs) cadastradas no sistema, lidas a partir do banco de dados relacional.
    """
    try:
        jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).all()
        jobs_list = []
        for job in jobs:
            source = ""
            if job.source_paths:
                try:
                    source_list = json.loads(job.source_paths)
                    if source_list:
                        source = f"/api/media/upload/{os.path.basename(source_list[0])}"
                except Exception:
                    pass
            
            target = ""
            if job.target_path:
                target = f"/api/media/upload/{os.path.basename(job.target_path)}"
                
            output = ""
            if job.output_path:
                output = f"/api/media/output/{os.path.basename(job.output_path)}"
                
            jobs_list.append({
                "id": job.id,
                "status": job.status,
                "progress": job.progress,
                "date_created": job.created_at,
                "date_updated": job.updated_at,
                "source": source,
                "target": target,
                "output": output,
                "error_message": job.error_message
            })
        return jobs_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar jobs: {str(e)}")


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retorna o status e os detalhes de uma tarefa específica.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    source = ""
    if job.source_paths:
        try:
            source_list = json.loads(job.source_paths)
            if source_list:
                source = f"/api/media/upload/{os.path.basename(source_list[0])}"
        except Exception:
            pass
            
    target = ""
    if job.target_path:
        target = f"/api/media/upload/{os.path.basename(job.target_path)}"
        
    output = ""
    if job.output_path and job.status == "completed":
        output = f"/api/media/output/{os.path.basename(job.output_path)}"

    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "date_created": job.created_at.isoformat(),
        "date_updated": job.updated_at.isoformat(),
        "source": source,
        "target": target,
        "output": output,
        "error_message": job.error_message
    }


@router.post("/jobs")
def create_job(request: JobCreateRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Cria uma nova tarefa de Face Swap na fila persistente do banco de dados e no disco.
    """
    try:
        step_args = collect_step_args()
        
        # Resolução automática de caminhos de mídia enviados como URLs da API ou caminhos absolutos
        resolved_source_paths = []
        jobs_path = state_manager.get_item("jobs_path") or ".jobs"
        uploads_dir = os.path.abspath(os.path.join(jobs_path, "uploads"))
        
        for path in request.source_paths:
            if path.startswith("/api/media/upload/"):
                filename = os.path.basename(path)
                resolved_source_paths.append(os.path.join(uploads_dir, filename))
            else:
                resolved_source_paths.append(path)
                
        resolved_target_path = request.target_path
        if request.target_path.startswith("/api/media/upload/"):
            filename = os.path.basename(request.target_path)
            resolved_target_path = os.path.join(uploads_dir, filename)
            
        step_args["source_paths"] = resolved_source_paths
        step_args["target_path"] = resolved_target_path
        step_args["processors"] = request.processors
        
        if request.face_swapper_weight is not None:
            step_args["face_swapper_weight"] = request.face_swapper_weight
        if request.face_mask_blur is not None:
            step_args["face_mask_blur"] = request.face_mask_blur
        if request.detection_threshold is not None:
            step_args["face_detector_score"] = request.detection_threshold
            step_args["face_landmarker_score"] = request.detection_threshold
            
        outputs_dir = os.path.join(jobs_path, "outputs")
        create_directory(outputs_dir)
        
        target_ext = os.path.splitext(resolved_target_path)[1] or ".mp4"
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        
        output_filename = f"{job_id}_swapped{target_ext}"
        output_path = os.path.abspath(os.path.join(outputs_dir, output_filename))
        step_args["output_path"] = output_path
        
        # 1. Criar os arquivos de job no disco (para o runner de steps do FaceFusion funcionar)
        if not job_manager.create_job(job_id):
            raise HTTPException(status_code=500, detail="Falha ao criar arquivo de job.")
            
        if not job_manager.add_step(job_id, step_args):
            raise HTTPException(status_code=500, detail="Falha ao adicionar step ao job.")
            
        if not job_manager.submit_job(job_id):
            raise HTTPException(status_code=500, detail="Falha ao enviar job para fila.")
            
        # 2. Registrar no banco de dados SQLite
        db_job = JobModel(
            id=job_id,
            status="queued",
            progress=0,
            source_paths=json.dumps(resolved_source_paths),
            target_path=resolved_target_path,
            output_path=output_path,
            face_swapper_weight=request.face_swapper_weight,
            face_mask_blur=request.face_mask_blur,
            detection_threshold=request.detection_threshold,
            smoothing=request.smoothing,
            processors=json.dumps(request.processors)
        )
        db.add(db_job)
        db.commit()
        
        return {
            "job_id": job_id,
            "status": "queued",
            "output_path": output_path,
            "output_url": f"/api/media/output/{output_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar job: {str(e)}")

