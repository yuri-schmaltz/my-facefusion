
import os
import time
import json
import asyncio
import subprocess
import httpx
import logging

if __name__ != "__main__":
    import pytest
    pytest.skip("Full integration script requires a running server.", allow_module_level=True)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntegrationTest")

BASE_URL = "http://127.0.0.1:8002"
TEMP_Video = "/tmp/facefusion_test_video.mp4"

async def create_dummy_video():
    """Generates a 5-second black video using FFmpeg for testing."""
    if os.path.exists(TEMP_Video):
        os.remove(TEMP_Video)
        
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=640x480:r=30",
        "-t", "5",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        TEMP_Video
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.wait()
    if process.returncode == 0:
        logger.info(f"Created dummy video at {TEMP_Video}")
        return True
    else:
        logger.error("Failed to create dummy video. Is FFmpeg installed?")
        return False

async def test_health(client):
    resp = await client.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    logger.info(f"Health Check Passed: {resp.json()}")

async def test_config(client):
    resp = await client.get(f"{BASE_URL}/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "processors" in data
    logger.info("Config Check Passed")

async def submit_job(client, target_path):
    # Set target path in config first (stateful API)
    await client.post(f"{BASE_URL}/config", json={"target_path": target_path})
    
    # Run
    resp = await client.post(f"{BASE_URL}/run")
    if resp.status_code != 200:
        logger.error(f"Run failed: {resp.text}")
        return None
        
    data = resp.json()
    logger.info(f"Job Submitted: {data}")
    return data["job_id"]

async def watch_job_events(client, job_id, timeout=30):
    url = f"{BASE_URL}/jobs/{job_id}/events"
    logger.info(f"Connecting to SSE: {url}")
    
    start_time = time.time()
    events_received = []
    
    async with client.stream("GET", url, timeout=timeout) as response:
        async for line in response.aiter_lines():
            if time.time() - start_time > timeout:
                logger.error("Timeout waiting for completion")
                break
                
            if line.startswith("data: "):
                data_str = line[6:]
                try:
                    event = json.loads(data_str)
                    events_received.append(event)
                    event_type = event.get("event_type")
                    
                    if event_type == "status_changed":
                        status = event.get("data")
                        logger.info(f"Job Status Changed: {status}")
                        if status == "completed":
                            return True
                        if status == "failed":
                            return False
                    
                    if event_type == "progress":
                        progress = event.get("data")
                        # logger.info(f"Progress: {progress:.2f}")

                except json.JSONDecodeError:
                    pass
    return False

async def test_cancellation(client):
    logger.info("--- Testing Cancellation ---")
    job_id = await submit_job(client, TEMP_Video)
    assert job_id is not None
    
    # Wait for running
    # We can peek at status
    for _ in range(10):
        resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
        status = resp.json().get("status")
        if status == "running":
            break
        await asyncio.sleep(0.5)
        
    logger.info("Job is running. Sending Stop command...")
    await client.post(f"{BASE_URL}/stop")
    
    # VerifyCanceled
    await asyncio.sleep(1)
    resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
    final_status = resp.json().get("status")
    logger.info(f"Final Status after Stop: {final_status}")
    assert final_status in ["canceled", "stopping"] # Stopping might be transient

async def run_tests():
    if not await create_dummy_video():
        return

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            await test_health(client)
            await test_config(client)
            
            logger.info("--- Testing Full Job Execution ---")
            job_id = await submit_job(client, TEMP_Video)
            if job_id:
                success = await watch_job_events(client, job_id, timeout=60)
                if success:
                    logger.info("Job completed successfully via SSE!")
                else:
                    logger.error("Job did not complete or failed.")
            
            await test_cancellation(client)
            
        except Exception as e:
            logger.error(f"Test Suite Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_tests())
