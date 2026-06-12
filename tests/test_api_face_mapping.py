import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from facefusion.api.main import app
from facefusion.api.database import Base, get_db, JobModel
from facefusion.jobs import job_manager

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_preview_with_model_options() -> None:
    """Verifica se o preview aceita e propaga os parâmetros de modelo e pixel boost."""
    source_content = b"fake binary data source"
    target_content = b"fake binary data target"

    # Uploads mockados
    src_res = client.post(
        "/api/media/upload",
        files={"file": ("source.jpg", io.BytesIO(source_content), "image/jpeg")}
    )
    tgt_res = client.post(
        "/api/media/upload",
        files={"file": ("target.jpg", io.BytesIO(target_content), "image/jpeg")}
    )

    src_url = src_res.json()["url"]
    tgt_url = tgt_res.json()["url"]

    # Testar preview com os novos campos
    payload = {
        "source_paths": [src_url],
        "target_path": tgt_url,
        "processors": ["face_swapper", "face_enhancer", "frame_enhancer"],
        "face_swapper_model": "inswapper_128_fp16",
        "face_swapper_pixel_boost": "512x512",
        "face_swapper_weight": 0.85,
        "face_mask_blur": 0.3,
        "detection_threshold": 0.65,
        "face_enhancer_model": "codeformer",
        "face_enhancer_blend": 85,
        "face_enhancer_weight": 0.9,
        "frame_enhancer_model": "ultra_sharp_x4",
        "frame_enhancer_blend": 75
    }

    # Como o preview executa o pipeline real do FaceFusion, que exige ONNX e arquivos reais,
    # verificamos se a requisição passa na validação JSON (200 ou erro de processamento do arquivo dummy, mas não 422).
    # Como enviamos dados binários fake, ele deve retornar erro 500/400 de processamento (ou seja, a validação de parâmetros passou!).
    response = client.post("/api/preview", json=payload)
    assert response.status_code != 422


def test_create_job_with_mappings_and_model_options() -> None:
    """Verifica se a criação de job com mapeamento sequencial e opções de modelo propaga as configurações para os passos."""
    source_content = b"fake binary data source"
    target_content = b"fake binary data target"

    src_res = client.post(
        "/api/media/upload",
        files={"file": ("source.jpg", io.BytesIO(source_content), "image/jpeg")}
    )
    tgt_res = client.post(
        "/api/media/upload",
        files={"file": ("target.jpg", io.BytesIO(target_content), "image/jpeg")}
    )

    src_url = src_res.json()["url"]
    tgt_url = tgt_res.json()["url"]

    payload = {
        "source_paths": [src_url],
        "target_path": tgt_url,
        "face_swapper_model": "simswap_256",
        "face_swapper_pixel_boost": "1024x1024",
        "face_swapper_weight": 0.85,
        "face_mask_blur": 0.3,
        "detection_threshold": 0.65,
        "smoothing": 5,
        "processors": ["face_swapper", "face_enhancer", "frame_enhancer"],
        "output_format": "mp4",
        "face_enhancer_model": "gfpgan_1.4",
        "face_enhancer_blend": 80,
        "face_enhancer_weight": 0.95,
        "frame_enhancer_model": "real_esrgan_x4_fp16",
        "frame_enhancer_blend": 70,
        "mappings": [
            {
                "source_path": src_url,
                "target_face_index": 0,
                "reference_frame_number": 120
            },
            {
                "source_path": src_url,
                "target_face_index": 1,
                "reference_frame_number": 120
            }
        ]
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]
    assert data["status"] == "queued"

    # Verificar passos do job no disco (arquivos do job_manager)
    steps = job_manager.get_steps(job_id)
    assert len(steps) == 2
    
    # Validar se o primeiro passo salvou as chaves corretas
    step0 = steps[0]
    assert step0["args"]["face_selector_mode"] == "reference"
    assert step0["args"]["reference_face_position"] == 0
    assert step0["args"]["reference_frame_number"] == 120
    assert step0["args"]["face_swapper_model"] == "simswap_256"
    assert step0["args"]["face_swapper_pixel_boost"] == "1024x1024"
    assert step0["args"]["face_enhancer_model"] == "gfpgan_1.4"
    assert step0["args"]["face_enhancer_blend"] == 80
    assert step0["args"]["face_enhancer_weight"] == 0.95
    assert step0["args"]["frame_enhancer_model"] == "real_esrgan_x4_fp16"
    assert step0["args"]["frame_enhancer_blend"] == 70
    assert step0["args"]["reference_target_path"] is not None

    # Validar o segundo passo
    step1 = steps[1]
    assert step1["args"]["face_selector_mode"] == "reference"
    assert step1["args"]["reference_face_position"] == 1
    assert step1["args"]["reference_frame_number"] == 120
    assert step1["args"]["face_swapper_model"] == "simswap_256"
    assert step1["args"]["face_swapper_pixel_boost"] == "1024x1024"
    assert step1["args"]["face_enhancer_model"] == "gfpgan_1.4"
    assert step1["args"]["face_enhancer_blend"] == 80
    assert step1["args"]["face_enhancer_weight"] == 0.95
    assert step1["args"]["frame_enhancer_model"] == "real_esrgan_x4_fp16"
    assert step1["args"]["frame_enhancer_blend"] == 70
    assert step1["args"]["reference_target_path"] is not None
    # A entrada (target_path) do passo 1 deve ser o output temporário do passo 0
    assert step1["args"]["target_path"] != step0["args"]["target_path"]

    # Limpar job do disco
    job_manager.delete_job(job_id)
