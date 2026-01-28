import time
import os
import sys
import threading
from unittest.mock import MagicMock

# Mock dependencies to avoid full environment requirement for smoke test
sys.modules['onnxruntime'] = MagicMock()
sys.modules['tensorflow'] = MagicMock()
sys.modules['torch'] = MagicMock()

from facefusion.orchestrator import get_orchestrator, RunRequest, JobStatus
from facefusion import state_manager

def test_happy_path():
    print("\n--- Testing Happy Path ---")
    orch = get_orchestrator()
    
    # Mock settings
    settings = {
        'source_paths': ['/tmp/source.jpg'],
        'target_path': '/tmp/target.mp4',
        'output_path': '/tmp/output.mp4'
    }
    
    request = RunRequest(
        source_paths=settings['source_paths'],
        target_path=settings['target_path'],
        output_path=settings['output_path'],
        processors=['face_swapper'],
        settings=settings
    )
    
    print(f"Submitting job...")
    job_id = orch.submit(request)
    print(f"Job submitted: {job_id}")
    
    job = orch.get_job(job_id)
    print(f"Initial Status: {job.status}")
    assert job.status == JobStatus.QUEUED
    
    # For smoke test, we can't easily run the actual pipeline without assets.
    # But we can verify the job exists in store.
    
    job_from_store = orch.get_job(job_id)
    assert job_from_store.job_id == job_id
    print("Persistence check passed.")
    
    # We won't call run_job here because it would fail without real assets.
    # But we can simulate a status update manually to verify store update.
    job.status = JobStatus.COMPLETED
    orch.store.update_job(job)
    
    job_final = orch.get_job(job_id)
    print(f"Final Status: {job_final.status}")
    assert job_final.status == JobStatus.COMPLETED

def test_cancel_flow():
    print("\n--- Testing Cancel Flow ---")
    orch = get_orchestrator()
    
    request = RunRequest(
        source_paths=['/tmp/s.jpg'],
        target_path='/tmp/t.mp4',
        output_path='/tmp/o.mp4',
        processors=[],
        settings={}
    )
    
    job_id = orch.submit(request)
    print(f"Job submitted: {job_id}")
    
    print("Canceling job...")
    orch.cancel_job(job_id)
    
    job = orch.get_job(job_id)
    print(f"Job Cancel Requested: {job.cancel_requested}")
    assert job.cancel_requested == True
    
    # In a real run, the Runner would see this and set status to CANCELED.
    # Here we just verify the flag is set in DB.
    job_from_store = orch.get_job(job_id)
    assert job_from_store.cancel_requested == True
    print("Cancel persistence check passed.")

if __name__ == "__main__":
    # Setup
    sys.path.append(os.getcwd())
    # Mock some state items needed for initialization
    state_manager.init_item('jobs_path', '/tmp/facefusion_jobs.sqlite')
    
    try:
        test_happy_path()
        test_cancel_flow()
        print("\n✅ Verification Successful!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
