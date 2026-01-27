from fastapi.testclient import TestClient
from facefusion.api_server import app, job_progress

client = TestClient(app)

def test_get_job_status_unknown():
    response = client.get("/jobs/invalid_job_id")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'unknown'
    assert data['progress'] == 0.0

def test_update_job_progress():
    # Simulate a job
    job_id = "test_job_123"
    job_progress[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0.0
    }
    
    # Check initial
    response = client.get(f"/jobs/{job_id}")
    assert response.json()['progress'] == 0.0
    
    # Update manually
    job_progress[job_id]["progress"] = 50.5
    
    # Check update
    response = client.get(f"/jobs/{job_id}")
    assert response.json()['progress'] == 50.5
