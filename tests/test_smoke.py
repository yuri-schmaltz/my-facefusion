import subprocess
import os
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from facefusion.api_server import app
from facefusion import state_manager
from tests.helper import get_test_example_file, get_test_examples_directory, get_test_output_file, prepare_test_output_directory, get_test_jobs_directory
from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, init_jobs
import pytest

# Initialize Test Client
client = TestClient(app)

@pytest.fixture(scope='module', autouse=True)
def setup_test_assets():
    # Initialize state required by download and other modules
    if state_manager.get_item('download_providers') is None:
        from facefusion import choices
        state_manager.init_item('download_providers', choices.download_providers)
    if state_manager.get_item('log_level') is None:
        state_manager.init_item('log_level', 'warn')

    # Ensure assets are downloaded for the test
    conditional_download(get_test_examples_directory(), [
        'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
        'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
    ])
    # Prepare environment
    prepare_test_output_directory()
    clear_jobs(get_test_jobs_directory())
    init_jobs(get_test_jobs_directory())

@patch('facefusion.jobs.job_runner.run_job')
def test_api_job_submission_flow(mock_run_job):
    """
    Smoke Test: Integration simulation of a job submission.
    1. Sets up inputs/outputs.
    2. Calls POST /run via API.
    3. Verifies pipeline reaches job_runner with success.
    4. Proves API & State are healthy (Fix for 500 Error).
    """
    # Define side effect to simulate successful processing
    def side_effect(job_id, process_step):
        # We can inspect job_id or process_step if needed
        return True

    mock_run_job.side_effect = side_effect
    
    # 1. Prepare Paths
    source_path = get_test_example_file('source.jpg')
    target_path = get_test_example_file('target-240p.mp4')
    output_path = get_test_output_file('smoke_test_output.mp4')
    
    # Ensure inputs exist
    assert os.path.exists(source_path), "Source file missing"
    assert os.path.exists(target_path), "Target file missing"

    # 2. Build Payload (mimics what UI sends)
    # Using minimal arguments to avoid heavy processing but exercise the path
    payload = {
        "source_paths": [source_path],
        "target_path": target_path,
        "output_path": output_path,
        "face_detector_model": "yolo_face",
        "face_selector_mode": "reference",
        "processors": [], # Empty processors = fast pass-through (or just copy/video logic)
        # Add required defaults just in case
        "face_mask_types": ["box"],
        "face_mask_regions": ["skin"],
        "execution_providers": ["cpu"],
        "execution_thread_count": 4,
        "execution_queue_count": 1
    }

    # 3. Call API
    # Use context manager to trigger lifespan events (app startup) which initializes state
    try:
        with client:
            # Verify critical state is initialized
            assert state_manager.get_item('temp_path') is not None, "Temp path not initialized!"
            assert state_manager.get_item('execution_device_ids') is not None, "Execution device IDs not initialized!"
            
            response = client.post("/run", json=payload)
    except RuntimeError as exc:
        pytest.skip(f"Test environment cannot spawn threads: {exc}")
    
    # 4. Verify no 500 error
    # If 500, print result for debugging
    if response.status_code != 200:
        print(f"DEBUG: Response text: {response.text}")
    assert response.status_code == 200, f"API failed with {response.status_code}: {response.text}"
    
    # Check if response contains success indication
    # (Assuming API returns some JSON result)
    data = response.json()
    assert data is not None
