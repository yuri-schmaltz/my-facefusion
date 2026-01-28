from fastapi.testclient import TestClient
from facefusion.api_server import app
from facefusion.orchestrator import get_orchestrator
from facefusion.orchestrator.models import Job, JobStatus

client = TestClient(app)

def test_get_job_status_unknown():
    response = client.get("/jobs/invalid_job_id")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'unknown'
    assert data['progress'] == 0.0

def test_update_job_progress():
    import uuid
    # Setup - Create a real job in the orchestrator
    orch = get_orchestrator()
    job_id = f"test_job_progress_{uuid.uuid4()}"
    
    # Create a dummy job
    job = Job(
        job_id=job_id,
        status=JobStatus.RUNNING,
        progress=0.0
    )
    orch.store.create_job(job)
    
    # Check initial via API
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()['progress'] == 0.0
    
    # Update manually via orchestrator/job object
    job.update_progress(0.55)
    orch.store.update_job(job)
    
    # Check update via API
    response = client.get(f"/jobs/{job_id}")
    assert response.json()['progress'] == 0.55
    
    # Cleanup
    # orch.store.delete_job(job_id) # If method exists, or just leave it since it's temp DB

