import os
import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from facefusion import state_manager
from facefusion.filesystem import get_default_path

# Configurar caminho do banco de dados dinamicamente
jobs_path = state_manager.get_item('jobs_path')
if not jobs_path:
    jobs_path = get_default_path('data')

db_dir = jobs_path
os.makedirs(db_dir, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(db_dir, 'jobs.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="queued")  # drafted, queued, processing, completed, failed
    progress = Column(Integer, default=0)
    source_paths = Column(Text)  # JSON string list
    target_path = Column(String)
    output_path = Column(String)
    face_swapper_weight = Column(Float, default=0.5)
    face_mask_blur = Column(Float, default=0.3)
    detection_threshold = Column(Float, default=0.5)
    smoothing = Column(Integer, default=5)
    processors = Column(Text)  # JSON string list
    step = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN step TEXT"))
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def update_job_progress_and_step(progress_val: int, step_text: str) -> None:
    try:
        from facefusion import state_manager
        from facefusion.jobs import job_manager
        job_id = state_manager.get_item('job_id')
        if job_id:
            db = SessionLocal()
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                # Obter o total de passos e o passo atual
                step_index = state_manager.get_item('step_index') or 0
                step_total = job_manager.count_step_total(job_id) or 1
                
                # Calcular o progresso geral proporcionalmente
                scaled_progress = int((step_index * 100 + progress_val) / step_total)
                scaled_progress = min(max(scaled_progress, 0), 99)
                
                job.progress = scaled_progress
                job.step = f"Passo {step_index + 1}/{step_total}: {step_text}"
                db.commit()
            db.close()
    except Exception:
        pass
