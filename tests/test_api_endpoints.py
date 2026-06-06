import os
import io
import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from facefusion.api.main import app
from facefusion.api.database import Base, get_db, JobModel

# Configurar banco de dados SQLite temporário em memória para os testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Criar tabelas temporárias
    Base.metadata.create_all(bind=engine)
    yield
    # Limpar tabelas ao final
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Substituir a dependência do banco real pela versão em memória nos testes
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_read_root() -> None:
    """Verifica se a rota raiz da API retorna status 200 e informações online."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "FaceFusion API"
    assert "version" in data
    assert data["status"] == "online"


def test_get_hardware_providers() -> None:
    """Verifica se o endpoint de provedores de aceleração retorna uma lista válida."""
    response = client.get("/api/hardware/providers")
    assert response.status_code == 200
    providers = response.json()
    assert isinstance(providers, list)
    assert len(providers) > 0


def test_get_hardware_devices() -> None:
    """Verifica se o endpoint de dispositivos de hardware retorna uma lista de dispositivos."""
    response = client.get("/api/hardware/devices")
    assert response.status_code == 200
    devices = response.json()
    assert isinstance(devices, list)


def test_get_available_processors() -> None:
    """Verifica se o endpoint de processadores lista os módulos nativos do FaceFusion."""
    response = client.get("/api/processors/list")
    assert response.status_code == 200
    processors = response.json()
    assert isinstance(processors, list)
    assert "face_swapper" in processors


def test_get_current_config() -> None:
    """Verifica se o endpoint de configuração do estado retorna variáveis de ambiente essenciais."""
    response = client.get("/api/config")
    assert response.status_code == 200
    config_data = response.json()
    assert "jobs_path" in config_data
    assert "temp_path" in config_data


def test_upload_and_retrieve_media() -> None:
    """Testa o ciclo de upload e recuperação de arquivos de mídia temporários."""
    dummy_content = b"fake binary data for image"
    
    # 1. Realizar upload do arquivo
    response = client.post(
        "/api/media/upload",
        files={"file": ("test_img.jpg", io.BytesIO(dummy_content), "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_path" in data
    assert data["filename"] == "test_img.jpg"
    assert "unique_filename" in data
    assert "url" in data

    unique_filename = data["unique_filename"]

    # 2. Recuperar o arquivo enviado e verificar se o conteúdo bate
    get_response = client.get(f"/api/media/upload/{unique_filename}")
    assert get_response.status_code == 200
    assert get_response.content == dummy_content


def test_create_list_and_query_jobs() -> None:
    """Testa criação, listagem e busca individual de tarefas com resolução de caminhos."""
    # 1. Enviar arquivos de origem e destino
    source_content = b"dummy source face"
    target_content = b"dummy target video"

    source_res = client.post(
        "/api/media/upload",
        files={"file": ("source_face.jpg", io.BytesIO(source_content), "image/jpeg")}
    )
    assert source_res.status_code == 200
    source_url = source_res.json()["url"]

    target_res = client.post(
        "/api/media/upload",
        files={"file": ("target_video.mp4", io.BytesIO(target_content), "video/mp4")}
    )
    assert target_res.status_code == 200
    target_url = target_res.json()["url"]

    # 2. Criar uma tarefa usando as URLs parciais (testando a resolução de caminhos absoluta no backend)
    req_payload = {
        "source_paths": [source_url],
        "target_path": target_url,
        "face_swapper_weight": 0.85,
        "face_mask_blur": 0.3,
        "detection_threshold": 0.65,
        "smoothing": 5,
        "processors": ["face_swapper"],
        "output_format": "mp4"
    }

    create_res = client.post("/api/jobs", json=req_payload)
    assert create_res.status_code == 200
    job_data = create_res.json()
    assert "job_id" in job_data
    job_id = job_data["job_id"]
    assert job_data["status"] == "queued"
    assert "output_url" in job_data

    # 3. Listar tarefas e verificar se ela foi incluída no banco de dados SQLite
    list_res = client.get("/api/jobs")
    assert list_res.status_code == 200
    jobs_list = list_res.json()
    assert len(jobs_list) > 0
    assert any(j["id"] == job_id for j in jobs_list)

    # 4. Obter status individual da tarefa
    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["id"] == job_id
    assert status_data["status"] == "queued"
    assert status_data["progress"] == 0
    assert "source" in status_data
    assert "target" in status_data


def test_get_hardware_providers_error() -> None:
    """Verifica se erro ao buscar provedores de hardware retorna 500."""
    with patch("facefusion.api.routes.get_available_execution_providers") as mock_get:
        mock_get.side_effect = Exception("Hardware detection failed")
        response = client.get("/api/hardware/providers")
        assert response.status_code == 500
        assert "Erro ao ler provedores de hardware" in response.json()["detail"]


def test_get_hardware_devices_error() -> None:
    """Verifica se erro ao detectar dispositivos de hardware retorna 500."""
    with patch("facefusion.api.routes.detect_static_execution_devices") as mock_detect:
        mock_detect.side_effect = Exception("NVIDIA SMI failure")
        response = client.get("/api/hardware/devices")
        assert response.status_code == 500
        assert "Erro ao detectar dispositivos NVIDIA" in response.json()["detail"]


def test_get_available_processors_error() -> None:
    """Verifica se erro ao varrer processadores retorna 500."""
    with patch("facefusion.api.routes.resolve_file_paths") as mock_resolve:
        mock_resolve.side_effect = Exception("Filesystem error")
        response = client.get("/api/processors/list")
        assert response.status_code == 500
        assert "Erro ao varrer processadores" in response.json()["detail"]


def test_get_current_config_error() -> None:
    """Verifica se erro ao ler a configuração global do estado retorna 500."""
    with patch("facefusion.state_manager.get_item") as mock_get:
        mock_get.side_effect = Exception("State manager uninitialized")
        response = client.get("/api/config")
        assert response.status_code == 500
        assert "Erro ao ler configuração do estado" in response.json()["detail"]


def test_create_job_invalid_payload() -> None:
    """Verifica se o endpoint de criação de job rejeita payloads inválidos."""
    # 1. Payload vazio
    response = client.post("/api/jobs", json={})
    assert response.status_code == 422

    # 2. Faltando target_path
    response = client.post("/api/jobs", json={"source_paths": ["/api/media/upload/test.jpg"]})
    assert response.status_code == 422

    # 3. Faltando source_paths
    response = client.post("/api/jobs", json={"target_path": "/api/media/upload/test.mp4"})
    assert response.status_code == 422

    # 4. Tipo inválido de face_swapper_weight
    response = client.post("/api/jobs", json={
        "source_paths": ["/api/media/upload/test.jpg"],
        "target_path": "/api/media/upload/test.mp4",
        "face_swapper_weight": "very_high"
    })
    assert response.status_code == 422

    # 5. Tipo inválido de processors
    response = client.post("/api/jobs", json={
        "source_paths": ["/api/media/upload/test.jpg"],
        "target_path": "/api/media/upload/test.mp4",
        "processors": "face_swapper"
    })
    assert response.status_code == 422


def test_get_upload_file_not_found() -> None:
    """Verifica se buscar um arquivo de upload inexistente retorna 404."""
    response = client.get("/api/media/upload/non_existent_file.jpg")
    assert response.status_code == 404
    assert response.json()["detail"] == "Arquivo de mídia não encontrado"


def test_get_output_file_not_found() -> None:
    """Verifica se buscar um arquivo de output inexistente retorna 404."""
    response = client.get("/api/media/output/non_existent_file.mp4")
    assert response.status_code == 404
    assert response.json()["detail"] == "Arquivo de mídia não encontrado"


def test_get_job_status_not_found() -> None:
    """Verifica se buscar o status de um job inexistente retorna 404."""
    response = client.get("/api/jobs/job-non-existent-12345")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada"


def test_media_endpoints_path_traversal() -> None:
    """Verifica se tentativas de path traversal são bloqueadas por segurança."""
    # Testar com caminhos contendo traversal relativo
    response1 = client.get("/api/media/upload/../../etc/passwd")
    assert response1.status_code in (400, 404)

    response2 = client.get("/api/media/output/../../etc/passwd")
    assert response2.status_code in (400, 404)
