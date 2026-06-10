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
from facefusion.filesystem import resolve_file_paths, get_file_name, create_directory, get_default_path
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
    trim_frame_start: Optional[int] = None
    trim_frame_end: Optional[int] = None


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


class ConfigUpdateRequest(BaseModel):
    temp_path: Optional[str] = None
    jobs_path: Optional[str] = None
    log_level: Optional[str] = None
    execution_providers: Optional[List[str]] = None
    execution_thread_count: Optional[int] = None
    video_memory_strategy: Optional[str] = None


@router.post("/config")
def update_config(request: ConfigUpdateRequest) -> Dict[str, Any]:
    """
    Atualiza as configurações do estado em memória.
    """
    try:
        if request.temp_path is not None:
            state_manager.set_item("temp_path", request.temp_path)
        if request.jobs_path is not None:
            state_manager.set_item("jobs_path", request.jobs_path)
        if request.log_level is not None:
            state_manager.set_item("log_level", request.log_level)
        if request.execution_providers is not None:
            state_manager.set_item("execution_providers", request.execution_providers)
        if request.execution_thread_count is not None:
            state_manager.set_item("execution_thread_count", request.execution_thread_count)
        if request.video_memory_strategy is not None:
            state_manager.set_item("video_memory_strategy", request.video_memory_strategy)
        return {"status": "success", "config": get_current_config()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar configuração: {str(e)}")


@router.post("/media/upload")
def upload_media(file: UploadFile = File(...)):
    """
    Faz o upload de uma imagem ou vídeo para a pasta temporária de jobs.
    """
    try:
        jobs_path = state_manager.get_item("jobs_path") or get_default_path('data')
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
    jobs_path = state_manager.get_item("jobs_path") or get_default_path('data')
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
    jobs_path = state_manager.get_item("jobs_path") or get_default_path('data')
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
        jobs_path = state_manager.get_item("jobs_path") or get_default_path('data')
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
        if request.trim_frame_start is not None:
            step_args["trim_frame_start"] = request.trim_frame_start
        if request.trim_frame_end is not None:
            step_args["trim_frame_end"] = request.trim_frame_end
            
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


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Exclui uma tarefa do banco de dados, seus arquivos de job no disco e a mídia de saída se gerada.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    try:
        # Excluir arquivos de job no disco
        job_manager.delete_job(job_id)
        
        # Excluir arquivos físicos de mídia se existirem
        if job.output_path and os.path.exists(job.output_path):
            try:
                os.remove(job.output_path)
            except Exception:
                pass
            
        # Excluir do banco
        db.delete(job)
        db.commit()
        
        return {"status": "success", "message": f"Job {job_id} excluído com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir job: {str(e)}")


@router.get("/diagnostic/export")
def export_diagnostic():
    """
    Gera um pacote ZIP contendo logs e configurações higienizados (sem PII ou segredos).
    """
    import tempfile
    import zipfile
    import platform
    try:
        from facefusion.filesystem import get_default_path
        from facefusion import state_manager
        
        # 1. Obter caminhos
        cache_dir = get_default_path('cache')
        log_file_path = os.path.join(cache_dir, 'facefusion.log')
        config_path = state_manager.get_item('config_path') or 'facefusion.ini'
        
        # 2. Criar arquivo zip temporário
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_zip_name = temp_zip.name
        temp_zip.close()
        
        def sanitize_text(text: str) -> str:
            import re
            # Mascarar caminhos de usuário no Linux / macOS
            text = re.sub(r'/home/[a-zA-Z0-9_-]+', '/home/user', text)
            # Mascarar caminhos de usuário no Windows
            text = re.sub(r'[cC]:\\Users\\[a-zA-Z0-9_-]+', 'C:\\Users\\user', text)
            # Mascarar possíveis tokens/senhas
            text = re.sub(r'(?i)(token|password|secret|key)["\s:=]+[a-zA-Z0-9_=-]+', r'\1: [MASKED]', text)
            return text

        with zipfile.ZipFile(temp_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adicionar log higienizado se existir
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    sanitized_log = sanitize_text(log_content)
                    zipf.writestr('facefusion.log', sanitized_log)
                except Exception as ex:
                    zipf.writestr('log_error.txt', f"Erro ao ler log: {str(ex)}")
            else:
                zipf.writestr('facefusion.log', 'Nenhum log gerado ainda.')
                
            # Adicionar ini de configuração higienizado
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        config_content = f.read()
                    sanitized_config = sanitize_text(config_content)
                    zipf.writestr('facefusion.ini', sanitized_config)
                except Exception as ex:
                    zipf.writestr('config_error.txt', f"Erro ao ler config: {str(ex)}")
                    
            # Adicionar dados do sistema/hardware
            system_info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
                "execution_providers": state_manager.get_item('execution_providers') or [],
                "video_memory_strategy": state_manager.get_item('video_memory_strategy') or 'balanced',
            }
            zipf.writestr('system_info.json', json.dumps(system_info, indent=4))
            
        return FileResponse(
            temp_zip_name,
            media_type="application/zip",
            filename="facefusion_diagnostic.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar diagnóstico: {str(e)}")


class PreviewRequest(BaseModel):
    source_paths: List[str]
    target_path: str
    processors: Optional[List[str]] = ["face_swapper"]
    frame_number: Optional[int] = 0
    timestamp: Optional[float] = None
    face_swapper_weight: Optional[float] = 0.5
    face_mask_blur: Optional[float] = 0.3
    detection_threshold: Optional[float] = 0.5


@router.post("/preview")
def generate_preview(request: PreviewRequest):
    """
    Gera um preview instantâneo aplicando os processadores selecionados em um único frame
    da mídia de destino, sem criar um job completo. Reutiliza a lógica nativa de preview
    do FaceFusion (mesma do Gradio UI).
    """
    import cv2
    import numpy
    import tempfile

    try:
        from facefusion.vision import read_static_image, read_static_images, read_video_frame, extract_vision_mask, merge_vision_mask, restrict_frame, unpack_resolution, detect_video_fps
        from facefusion.audio import create_empty_audio_frame
        from facefusion.processors.core import get_processors_modules
        from facefusion.filesystem import is_image, is_video
        from facefusion import state_manager as sm, logger as ff_logger

        # Resolver caminhos
        jobs_path = sm.get_item("jobs_path") or get_default_path('data')
        uploads_dir = os.path.abspath(os.path.join(jobs_path, "uploads"))

        resolved_source_paths = []
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

        # Validar que os arquivos existem
        for sp in resolved_source_paths:
            if not os.path.exists(sp):
                raise HTTPException(status_code=400, detail=f"Arquivo source não encontrado: {sp}")
        if not os.path.exists(resolved_target_path):
            raise HTTPException(status_code=400, detail=f"Arquivo target não encontrado: {resolved_target_path}")

        # Configurar state_manager temporariamente para o preview
        old_source = sm.get_item('source_paths')
        old_target = sm.get_item('target_path')
        old_processors = sm.get_item('processors')

        sm.set_item('source_paths', resolved_source_paths)
        sm.set_item('target_path', resolved_target_path)
        sm.set_item('processors', request.processors)

        if request.face_swapper_weight is not None:
            sm.set_item('face_swapper_weight', request.face_swapper_weight)
        if request.face_mask_blur is not None:
            sm.set_item('face_mask_blur', request.face_mask_blur)
        if request.detection_threshold is not None:
            sm.set_item('face_detector_score', request.detection_threshold)
            sm.set_item('face_landmarker_score', request.detection_threshold)

        try:
            # Ler frames de origem
            source_vision_frames = read_static_images(resolved_source_paths)
            source_audio_frame = create_empty_audio_frame()
            source_voice_frame = create_empty_audio_frame()

            # Ler frame de destino
            if is_image(resolved_target_path):
                reference_vision_frame = read_static_image(resolved_target_path)
                target_vision_frame = read_static_image(resolved_target_path, 'rgba')
            elif is_video(resolved_target_path):
                # Determinar o frame_number de acordo com timestamp ou frame_number fornecido
                if request.timestamp is not None:
                    fps = detect_video_fps(resolved_target_path) or 30.0
                    frame_number = int(request.timestamp * fps)
                else:
                    frame_number = request.frame_number or 0
                reference_vision_frame = read_video_frame(resolved_target_path, frame_number)
                target_vision_frame = read_video_frame(resolved_target_path, frame_number)
                if target_vision_frame is None:
                    raise HTTPException(status_code=400, detail="Não foi possível ler o frame do vídeo.")
                # Converter para RGBA se necessário
                if len(target_vision_frame.shape) == 3 and target_vision_frame.shape[2] == 3:
                    target_vision_frame = cv2.cvtColor(target_vision_frame, cv2.COLOR_BGR2BGRA)
            else:
                raise HTTPException(status_code=400, detail="Formato de mídia de destino não suportado.")

            if reference_vision_frame is None or target_vision_frame is None:
                raise HTTPException(status_code=400, detail="Não foi possível ler a mídia de destino.")

            # Processar preview (mesma lógica do Gradio preview.py)
            preview_resolution = '1024x1024'
            temp_vision_frame = restrict_frame(target_vision_frame, unpack_resolution(preview_resolution))
            temp_vision_frame_copy = temp_vision_frame.copy()
            temp_vision_mask = extract_vision_mask(temp_vision_frame_copy)

            for processor_module in get_processors_modules(request.processors):
                ff_logger.disable()
                if processor_module.pre_process('preview'):
                    ff_logger.enable()
                    temp_vision_frame_copy, temp_vision_mask = processor_module.process_frame(
                    {
                        'reference_vision_frame': reference_vision_frame,
                        'source_audio_frame': source_audio_frame,
                        'source_voice_frame': source_voice_frame,
                        'source_vision_frames': source_vision_frames,
                        'target_vision_frame': temp_vision_frame[:, :, :3],
                        'temp_vision_frame': temp_vision_frame_copy[:, :, :3],
                        'temp_vision_mask': temp_vision_mask
                    })
                ff_logger.enable()

            # Converter para imagem JPEG para retorno
            if len(temp_vision_frame_copy.shape) == 3 and temp_vision_frame_copy.shape[2] == 4:
                output_frame = cv2.cvtColor(temp_vision_frame_copy, cv2.COLOR_BGRA2BGR)
            elif len(temp_vision_frame_copy.shape) == 3 and temp_vision_frame_copy.shape[2] == 3:
                output_frame = temp_vision_frame_copy
            else:
                output_frame = temp_vision_frame_copy

            # Salvar como JPEG temporário
            outputs_dir = os.path.join(jobs_path, "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            preview_filename = f"preview_{uuid.uuid4().hex[:8]}.jpg"
            preview_path = os.path.join(outputs_dir, preview_filename)
            cv2.imwrite(preview_path, output_frame, [cv2.IMWRITE_JPEG_QUALITY, 92])

            return {
                "preview_url": f"/api/media/output/{preview_filename}",
                "status": "success"
            }

        finally:
            # Restaurar state_manager
            if old_source is not None:
                sm.set_item('source_paths', old_source)
            if old_target is not None:
                sm.set_item('target_path', old_target)
            if old_processors is not None:
                sm.set_item('processors', old_processors)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")
