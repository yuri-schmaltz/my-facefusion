import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from facefusion.api.database import Base, JobModel
# Import worker functions to test
import facefusion.api.worker as worker

# Setup isolated in-memory database for worker testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def setup_worker_database():
    Base.metadata.create_all(bind=engine)
    # Override SessionLocal inside worker module to use our testing db
    with patch("facefusion.api.worker.SessionLocal", TestingSessionLocal):
        yield
    Base.metadata.drop_all(bind=engine)


def test_worker_recovery_stuck_jobs() -> None:
    """Verifica se o worker recupera jobs travados em status 'processing' no início."""
    db = TestingSessionLocal()
    # Criar um job preso em 'processing'
    stuck_job = JobModel(
        id="job-stuck-1",
        status="processing",
        progress=50,
        source_paths='["/fake/source.jpg"]',
        target_path="/fake/target.mp4",
        output_path="/fake/output.mp4"
    )
    db.add(stuck_job)
    db.commit()
    db.close()

    # Executar a recuperação do worker mockando a parte do loop infinito
    # Para testar apenas a inicialização e recuperação
    with patch("facefusion.state_manager.get_item", return_value=".jobs"), \
         patch("facefusion.state_manager.init_item"), \
         patch("facefusion.jobs.job_manager.init_jobs"), \
         patch("facefusion.program.create_program"), \
         patch("facefusion.args.apply_args"), \
         patch("facefusion.jobs.job_runner.run_job"):
        
        # Chamamos uma versão controlada de worker_loop ou apenas mockamos a chamada de loop
        # Vamos rodar a primeira parte de worker_loop antes do 'while True'
        # Podemos testar isso mockando a parte do loop principal
        with patch("facefusion.api.worker._worker_stop_event.wait", side_effect=InterruptedError("Stop loop")):
            try:
                worker.worker_loop()
            except InterruptedError:
                pass

    # Verificar se o status do stuck_job mudou para 'failed'
    db = TestingSessionLocal()
    j1 = db.query(JobModel).filter(JobModel.id == "job-stuck-1").first()
    
    assert j1 is not None
    assert j1.status == "failed"
    assert "reiniciado" in j1.error_message
    assert j1.progress == 0
    db.close()


def test_worker_process_success_job() -> None:
    """Verifica se o worker processa com sucesso um job na fila."""
    db = TestingSessionLocal()
    job = JobModel(
        id="job-success-1",
        status="queued",
        progress=0,
        source_paths='["/fake/source.jpg"]',
        target_path="/fake/target.mp4",
        output_path="/fake/output.mp4"
    )
    db.add(job)
    db.commit()
    db.close()

    # Mockar a chamada real de execução do job
    with patch("facefusion.jobs.job_runner.run_job", return_value=True) as mock_run_job, \
         patch("facefusion.state_manager.get_item", return_value=".jobs"), \
         patch("facefusion.state_manager.set_item"), \
         patch("facefusion.state_manager.init_item"), \
         patch("facefusion.program.create_program"), \
         patch("facefusion.args.apply_args"), \
         patch("facefusion.jobs.job_manager.init_jobs"), \
         patch("facefusion.api.worker._worker_stop_event.wait", side_effect=InterruptedError("Stop loop")):
        
        try:
            worker.worker_loop()
        except InterruptedError:
            pass
        
        mock_run_job.assert_called_once()

    # Verificar se o status mudou para completed e progresso 100
    db = TestingSessionLocal()
    j = db.query(JobModel).filter(JobModel.id == "job-success-1").first()
    assert j is not None
    assert j.status == "completed"
    assert j.progress == 100
    db.close()


def test_worker_process_failed_job() -> None:
    """Verifica se o worker trata corretamente falha na execução do job."""
    db = TestingSessionLocal()
    job = JobModel(
        id="job-fail-1",
        status="queued",
        progress=0,
        source_paths='["/fake/source.jpg"]',
        target_path="/fake/target.mp4",
        output_path="/fake/output.mp4"
    )
    db.add(job)
    db.commit()
    db.close()

    # Mockar a chamada real de execução do job retornando False
    with patch("facefusion.jobs.job_runner.run_job", return_value=False) as mock_run_job, \
         patch("facefusion.state_manager.get_item", return_value=".jobs"), \
         patch("facefusion.state_manager.set_item"), \
         patch("facefusion.state_manager.init_item"), \
         patch("facefusion.program.create_program"), \
         patch("facefusion.args.apply_args"), \
         patch("facefusion.jobs.job_manager.init_jobs"), \
         patch("facefusion.api.worker._worker_stop_event.wait", side_effect=InterruptedError("Stop loop")):
        
        try:
            worker.worker_loop()
        except InterruptedError:
            pass

    # Verificar se o status mudou para failed e progresso 0 com erro
    db = TestingSessionLocal()
    j = db.query(JobModel).filter(JobModel.id == "job-fail-1").first()
    assert j is not None
    assert j.status == "failed"
    assert j.progress == 0
    assert "Erro de execução" in j.error_message
    db.close()


def test_worker_process_exception_handling() -> None:
    """Verifica se o worker trata exceções durante a execução salvando o traceback."""
    db = TestingSessionLocal()
    job = JobModel(
        id="job-exception-1",
        status="queued",
        progress=0,
        source_paths='["/fake/source.jpg"]',
        target_path="/fake/target.mp4",
        output_path="/fake/output.mp4"
    )
    db.add(job)
    db.commit()
    db.close()

    # Mockar a chamada real de execução do job levantando exceção
    with patch("facefusion.jobs.job_runner.run_job", side_effect=RuntimeError("GPU out of memory error")) as mock_run_job, \
         patch("facefusion.state_manager.get_item", return_value=".jobs"), \
         patch("facefusion.state_manager.set_item"), \
         patch("facefusion.state_manager.init_item"), \
         patch("facefusion.program.create_program"), \
         patch("facefusion.args.apply_args"), \
         patch("facefusion.jobs.job_manager.init_jobs"), \
         patch("facefusion.api.worker._worker_stop_event.wait", side_effect=InterruptedError("Stop loop")):
        
        try:
            worker.worker_loop()
        except InterruptedError:
            pass

    # Verificar se o status mudou para failed e erro gravou o traceback
    db = TestingSessionLocal()
    j = db.query(JobModel).filter(JobModel.id == "job-exception-1").first()
    assert j is not None
    assert j.status == "failed"
    assert j.progress == 0
    assert "GPU out of memory error" in j.error_message
    assert "Traceback" in j.error_message
    db.close()
