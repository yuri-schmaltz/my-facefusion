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
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
