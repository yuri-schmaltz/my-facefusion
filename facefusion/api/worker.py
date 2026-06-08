import time
import threading
from facefusion.api.database import SessionLocal, JobModel
from facefusion.jobs import job_runner
from facefusion.core import process_step
from facefusion import state_manager


_worker_stop_event = threading.Event()


def start_worker():
    global _worker_stop_event
    _worker_stop_event.clear()
    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()


def stop_worker():
    global _worker_stop_event
    print("[Worker] Sinalizando encerramento para o worker loop...", flush=True)
    _worker_stop_event.set()


def worker_loop():
    print("[Worker] Inicializando fila sequencial no segundo plano...", flush=True)
    
    # Garantir que JOBS_PATH e o state_manager estejam devidamente carregados nesta thread
    try:
        from facefusion import state_manager
        from facefusion.program import create_program
        from facefusion.args import apply_args
        from facefusion.jobs import job_manager
        from facefusion.filesystem import get_default_path

        program = create_program()
        args = vars(program.parse_args(['run']))
        apply_args(args, state_manager.init_item)
        
        jobs_path = state_manager.get_item('jobs_path') or get_default_path('data')
        job_manager.init_jobs(jobs_path)
        print(f"[Worker] Caminho de jobs inicializado: {jobs_path}", flush=True)
    except Exception as e:
        print(f"[Worker] Erro crítico ao inicializar parâmetros: {str(e)}", flush=True)

    # Recuperação de jobs travados em 'processing' devido a desligamento ou reinício
    try:
        db = SessionLocal()
        stuck_jobs = db.query(JobModel).filter(JobModel.status == "processing").all()
        for stuck_job in stuck_jobs:
            print(f"[Worker] Recuperando job travado {stuck_job.id} para status 'failed'.", flush=True)
            stuck_job.status = "failed"
            stuck_job.progress = 0
            stuck_job.error_message = "O servidor foi reiniciado enquanto esta tarefa estava sendo processada."
        db.commit()
        db.close()
    except Exception as e:
        print(f"[Worker] Erro ao recuperar jobs travados: {str(e)}", flush=True)

    print("[Worker] Loop de escuta de tarefas iniciado.", flush=True)
    while not _worker_stop_event.is_set():
        try:
            db = SessionLocal()
            # Buscar o job mais antigo na fila
            job = db.query(JobModel).filter(JobModel.status == "queued").order_by(JobModel.created_at.asc()).first()
            
            if job:
                job_id = job.id
                print(f"[Worker] Selecionado job para processamento: {job_id}", flush=True)
                
                # Atualizar estado para processando
                job.status = "processing"
                job.progress = 15
                db.commit()
                db.close()
                
                try:
                    from facefusion.logger import set_job_context
                    set_job_context(job_id)

                    # Garantir que o comando está configurado para executar
                    state_manager.set_item('command', 'job-run')
                    
                    # Chamar o pipeline de execução nativo do FaceFusion
                    success = job_runner.run_job(job_id, process_step)
                    
                    db = SessionLocal()
                    job_to_update = db.query(JobModel).filter(JobModel.id == job_id).first()
                    if job_to_update:
                        if success:
                            job_to_update.status = "completed"
                            job_to_update.progress = 100
                            print(f"[Worker] Job {job_id} concluído com sucesso.", flush=True)
                        else:
                            job_to_update.status = "failed"
                            job_to_update.progress = 0
                            job_to_update.error_message = "Erro de execução nos passos do FaceFusion."
                            print(f"[Worker] Job {job_id} falhou nos passos de execução.", flush=True)
                        db.commit()
                    db.close()
                    
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"[Worker] Falha ao rodar o job {job_id}: {str(e)}\n{error_trace}", flush=True)
                    
                    db = SessionLocal()
                    job_to_update = db.query(JobModel).filter(JobModel.id == job_id).first()
                    if job_to_update:
                        job_to_update.status = "failed"
                        job_to_update.progress = 0
                        job_to_update.error_message = f"Exceção: {str(e)}\n{error_trace}"
                        db.commit()
                    db.close()
                finally:
                    from facefusion.logger import set_job_context
                    set_job_context('')
            else:
                db.close()
                _worker_stop_event.wait(1)
        except Exception as e:
            print(f"[Worker] Erro no loop de execução do worker: {str(e)}", flush=True)
            _worker_stop_event.wait(2)

