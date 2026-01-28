"""
FaceFusion Orchestrator logic
-----------------------------
Handles job submission, queuing, and coordination with the runner.
"""
import logging
import threading
import queue
import traceback
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from facefusion.orchestrator.models import Job, JobStatus, RunRequest, ErrorCode
from facefusion.orchestrator.store import JobStore
from facefusion.orchestrator.events import EventBus, create_status_event, create_progress_event
from facefusion.orchestrator.resources import ResourceManager
from facefusion.orchestrator.runner import Runner


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator for managing job execution lifecycle.
    
    Responsibilities:
    - job submission and state management
    - queuing and concurrency control
    - coordination with Runner for execution
    """
    
    def __init__(self, store: JobStore, event_bus: EventBus, resources: ResourceManager):
        self.store = store
        self.event_bus = event_bus
        self.resources = resources
        
        # Thread pool for background job execution
        self._executor = ThreadPoolExecutor(
            max_workers=self.resources.get_cpu_worker_count(),
            thread_name_prefix="orchestrator_worker"
        )
        self._active_runners: Dict[str, Runner] = {}
        self._lock = threading.RLock()
    
    def submit(self, request: RunRequest) -> str:
        """
        Create and queue a new job.
        
        Args:
            request: The run parameters
            
        Returns:
            The generated job_id
        """
        job_id = request.generate_job_id()
        
        job = Job(
            job_id=job_id,
            status=JobStatus.DRAFTED,
            config=request.to_config(),
            metadata={'client': 'orchestrator'}
        )
        
        # Add a default step
        from facefusion.orchestrator.models import Step
        job.steps.append(Step(index=0, name="Processing"))
        
        self.store.create_job(job)
        self.event_bus.publish(create_status_event(job_id, "drafted"))
        
        # Auto-queue for now (can be made manual later)
        self.queue_job(job_id)
        
        return job_id
    
    def queue_job(self, job_id: str) -> bool:
        """Move a job to the queued status."""
        job = self.store.get_job(job_id)
        if not job:
            return False
            
        if job.transition_to(JobStatus.QUEUED):
            self.store.update_job(job)
            self.event_bus.publish(create_status_event(job_id, "queued"))
            return True
        return False
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Request cancelation for a running or queued job.
        
        Note: Actual cancelation is cooperative and happens in the Runner.
        """
        job = self.store.get_job(job_id)
        if not job:
            return False
            
        # Update store to signal cancelation
        self.store.set_cancel_requested(job_id)
        self.event_bus.publish(create_status_event(job_id, "cancel_requested"))
        
        # If queued but not running, we might mark it as canceled immediately?
        # Better let the executor process it and see if it was canceled.
        return True
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get current job state."""
        return self.store.get_job(job_id)
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 10) -> List[Job]:
        """List recent jobs."""
        return self.store.list_jobs(status, limit)
    
    def run_job(self, job_id: str) -> bool:
        """
        Start execution of a job in the background.
        
        Args:
            job_id: The ID of the job to run
            
        Returns:
            True if job was successfully submitted to the executor
        """
        job = self.store.get_job(job_id)
        if not job:
            logger.error(f"Cannot run non-existent job {job_id}")
            return False
            
        if job.status != JobStatus.QUEUED:
            logger.warning(f"Cannot run job {job_id} in status {job.status}")
            return False
            
        # Submit to thread pool
        self._executor.submit(self._execute_job, job_id)
        return True
    
    def _execute_job(self, job_id: str) -> None:
        """
        Internal worker function to execute a job.
        Runs in a background thread.
        """
        job = self.store.get_job(job_id)
        if not job:
            return
            
        # Check if already canceled before starting
        if self.store.is_cancel_requested(job_id):
            job.transition_to(JobStatus.CANCELED)
            self.store.update_job(job)
            self.event_bus.publish(create_status_event(job_id, "canceled"))
            return

        # Start job
        if not job.transition_to(JobStatus.RUNNING):
            logger.error(f"Failed to transition job {job_id} to RUNNING")
            return
            
        self.store.update_job(job)
        self.event_bus.publish(create_status_event(job_id, "running"))
        
        # Create runner
        runner = Runner(job, self.store, self.event_bus, self.resources)
        
        with self._lock:
            self._active_runners[job_id] = runner
            
        try:
            # Execute with GPU semaphore
            with self.resources.acquire_gpu(job_id):
                success = runner.run()
                
            if success:
                job.transition_to(JobStatus.COMPLETED)
                job.progress = 1.0
            else:
                # Runner handles detailed status internally (failed/canceled)
                pass 
                
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"Unexpected error in job {job_id}: {e}")
            job.fail(ErrorCode.INTERNAL_ERROR, str(e))
        finally:
            with self._lock:
                self._active_runners.pop(job_id, None)
            
            # Sync final state to store
            # Need to reload from store in case runner updated it (like failed/canceled)
            final_job = self.store.get_job(job_id)
            if final_job.status == JobStatus.RUNNING:
                 # If still running but loop exited, something went wrong
                 final_job.fail(ErrorCode.PIPELINE_FAILED, "Pipeline exited without setting final status")
                 self.store.update_job(final_job)
            
            self.event_bus.publish(create_status_event(job_id, final_job.status.value))
    
    def shutdown(self):
        """Shutdown the orchestrator and all executors."""
        self._executor.shutdown(wait=True)
        self.store.close()
