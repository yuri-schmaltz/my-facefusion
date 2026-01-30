"""
Job Runner Adapter
------------------
Adapts the FaceFusion pipeline to the orchestrator execution model.
"""
import os
import logging
import traceback
from typing import Optional, Any

from facefusion.orchestrator.models import Job, JobStatus, StepStatus, ErrorCode
from facefusion.orchestrator.store import JobStore
from facefusion.orchestrator.events import EventBus, create_status_event, create_progress_event, create_log_event
from facefusion.orchestrator.resources import ResourceManager


logger = logging.getLogger(__name__)


class Runner:
    """
    Executes a FaceFusion job and provides lifecycle hooks.
    
    Responsibilities:
    - Setup environment for job
    - Execute the core pipeline
    - Report progress and handle cancelation
    - Manage temporary files and final outputs
    """
    
    def __init__(self, job: Job, store: JobStore, event_bus: EventBus, resources: ResourceManager):
        self.job = job
        self.store = store
        self.event_bus = event_bus
        self.resources = resources
        
    def is_canceled(self) -> bool:
        """Check if cancelation was requested."""
        return self.store.is_cancel_requested(self.job.job_id)
        
    def on_progress(self, progress: float, phase: str = "") -> None:
        """
        Progress callback called by the pipeline.
        With throttling to prevent flooding the event bus.
        """
        import time
        now = time.time()
        
        # Initialize last_update_time if it doesn't exist
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = 0
            
        # Limit updates to ~5 per second (0.2s interval)
        # Always allow progress == 1.0 (completion)
        if progress < 1.0 and (now - self._last_update_time) < 0.2:
            return
            
        self._last_update_time = now
        
        # Calculate global progress with weighting
        from facefusion import state_manager
        current_phase = state_manager.get_item('current_job_phase')
        phase = current_phase or phase  # Prefer state_manager phase if available
        
        global_progress = progress
        if phase == 'analysing':
             global_progress = progress * 0.05
        elif phase == 'extracting':
             global_progress = 0.05 + progress * 0.10
        elif phase == 'processing':
             global_progress = 0.15 + progress * 0.75
        elif phase == 'merging':
             global_progress = 0.90 + progress * 0.10
             
        self.job.update_progress(global_progress)
        self.store.update_progress(self.job.job_id, self.job.progress)
        self.event_bus.publish(create_progress_event(self.job.job_id, self.job.progress, phase))
        
    def log(self, level: str, message: str) -> None:
        """Log a message for the job."""
        self.event_bus.publish(create_log_event(self.job.job_id, level, message))
        
    def run(self) -> bool:
        """
        Execute the FaceFusion pipeline for this job.
        
        Returns:
            True if processing completed successfully
        """
        job_id = self.job.job_id
        config = self.job.config
        
        self.log("info", f"Starting job {job_id}")
        
        try:
            # 1. Validation and Path Normalization
            from facefusion.orchestrator.security import validate_input_path, validate_output_path
            
            try:
                source_paths = config.get('source_paths') or []
                config['source_paths'] = [validate_input_path(p) for p in source_paths]
                config['target_path'] = validate_input_path(config.get('target_path'))
                config['output_path'] = validate_output_path(config.get('output_path'))
            except Exception as e:
                self.job.fail(ErrorCode.PATH_ERROR, str(e))
                self.store.update_job(self.job)
                return False

            # 2. Setup State Manager
            from facefusion import state_manager, logger as ff_logger
            from facefusion.args import apply_args
            
            # Initialize core state with job config
            apply_args(config, state_manager.init_item)
            
            # Attach progress callback to state_manager for workflows to find
            state_manager.set_item('current_job_progress_callback', self.on_progress)
            state_manager.set_item('is_canceled_callback', self.is_canceled)
            
            # 3. Execute Pipeline
            from facefusion.core import process_step_orchestrator
            from facefusion.time_helper import get_current_date_time
            
            # We use the existing process_step but pass our runner context (implicitly via state_manager)
            start_time = float(get_current_date_time().timestamp())
            
            # Update step status
            if self.job.steps:
                self.job.steps[0].status = StepStatus.RUNNING
                self.job.steps[0].started_at = get_current_date_time()
                self.store.update_job(self.job)
            
            # Run the process
            # Note: conditional_process will be called which checks for is_stopping()
            # We need to make sure loop checks runner.is_canceled() too.
            success = process_step_orchestrator(job_id, 0, len(self.job.steps), config)
            
            if self.is_canceled():
                self.log("info", "Job canceled by user")
                self.job.transition_to(JobStatus.CANCELED)
                self.store.update_job(self.job)
                return False
                
            if success:
                self.log("info", "Job completed successfully")
                if self.job.steps:
                    self.job.steps[0].status = StepStatus.COMPLETED
                    self.job.steps[0].completed_at = get_current_date_time()
                    self.job.steps[0].progress = 1.0
                return True
            else:
                self.log("error", "Processing failed")
                self.job.fail(ErrorCode.PIPELINE_FAILED, "Pipeline processing failed")
                if self.job.steps:
                    self.job.steps[0].status = StepStatus.FAILED
                self.store.update_job(self.job)
                return False
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            tb = traceback.format_exc()
            self.log("error", error_msg)
            logger.error(f"Job {job_id} failed: {tb}")
            self.job.fail(ErrorCode.INTERNAL_ERROR, error_msg)
            self.job.metadata['traceback'] = tb
            self.store.update_job(self.job)
            return False
        finally:
            # Cleanup progress callback
            from facefusion import state_manager
            state_manager.set_item('current_job_progress_callback', None)
            state_manager.set_item('is_canceled_callback', None)
            
    def _finalize(self):
        """Cleanup temporary files and generate reports."""
        # TODO: Implement specialized cleanup if needed
        pass
