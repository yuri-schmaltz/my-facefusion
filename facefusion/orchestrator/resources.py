"""
Resource Management
-------------------
Controls concurrency for GPU, CPU, and I/O resources to prevent contention.
"""
import os
import threading
from contextlib import contextmanager
from typing import Optional
from dataclasses import dataclass


@dataclass
class ResourceLimits:
    """Configuration for resource limits."""
    max_gpu_jobs: int = 1  # Only 1 GPU job at a time by default
    max_cpu_workers: int = 4  # Thread pool size for CPU work
    max_ffmpeg_processes: int = 2  # Limit concurrent FFmpeg
    gpu_timeout_seconds: float = 3600.0  # 1 hour max GPU wait


class ResourceManager:
    """
    Manages resource acquisition for jobs.
    
    Prevents resource contention by:
    - Limiting concurrent GPU jobs (default: 1)
    - Controlling FFmpeg process count
    - Managing thread pool sizes
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        
        # GPU semaphore - controls GPU-heavy operations
        self._gpu_semaphore = threading.Semaphore(self.limits.max_gpu_jobs)
        
        # FFmpeg semaphore - limits concurrent encoding
        self._ffmpeg_semaphore = threading.Semaphore(self.limits.max_ffmpeg_processes)
        
        # Track active resources per job
        self._job_resources: dict = {}  # job_id -> set of resource names
        self._lock = threading.RLock()
    
    @contextmanager
    def acquire_gpu(self, job_id: str, timeout: Optional[float] = None):
        """
        Acquire GPU resource for a job.
        
        Args:
            job_id: The job requesting GPU
            timeout: Max seconds to wait (None = use default)
        
        Raises:
            TimeoutError: If timeout exceeded waiting for GPU
        """
        timeout = timeout or self.limits.gpu_timeout_seconds
        acquired = self._gpu_semaphore.acquire(timeout=timeout)
        
        if not acquired:
            raise TimeoutError(f"Timeout waiting for GPU resource for job {job_id}")
        
        with self._lock:
            if job_id not in self._job_resources:
                self._job_resources[job_id] = set()
            self._job_resources[job_id].add('gpu')
        
        try:
            yield
        finally:
            with self._lock:
                if job_id in self._job_resources:
                    self._job_resources[job_id].discard('gpu')
            self._gpu_semaphore.release()
    
    @contextmanager
    def acquire_ffmpeg(self, job_id: str, timeout: float = 60.0):
        """
        Acquire FFmpeg resource for encoding operations.
        
        Args:
            job_id: The job requesting FFmpeg
            timeout: Max seconds to wait
        """
        acquired = self._ffmpeg_semaphore.acquire(timeout=timeout)
        
        if not acquired:
            raise TimeoutError(f"Timeout waiting for FFmpeg resource for job {job_id}")
        
        with self._lock:
            if job_id not in self._job_resources:
                self._job_resources[job_id] = set()
            self._job_resources[job_id].add('ffmpeg')
        
        try:
            yield
        finally:
            with self._lock:
                if job_id in self._job_resources:
                    self._job_resources[job_id].discard('ffmpeg')
            self._ffmpeg_semaphore.release()
    
    def release_all(self, job_id: str) -> None:
        """Release all resources held by a job (for cleanup on error/cancel)."""
        with self._lock:
            if job_id in self._job_resources:
                resources = self._job_resources.pop(job_id, set())
                for resource in resources:
                    if resource == 'gpu':
                        self._gpu_semaphore.release()
                    elif resource == 'ffmpeg':
                        self._ffmpeg_semaphore.release()
    
    def get_cpu_worker_count(self) -> int:
        """Get recommended CPU worker count for ThreadPoolExecutor."""
        # Use configured limit or CPU count, whichever is smaller
        cpu_count = os.cpu_count() or 4
        return min(self.limits.max_cpu_workers, cpu_count)
    
    def get_status(self) -> dict:
        """Get current resource utilization status."""
        with self._lock:
            # Semaphore doesn't expose count directly, so we track manually
            gpu_available = self._gpu_semaphore._value if hasattr(self._gpu_semaphore, '_value') else 'unknown'
            ffmpeg_available = self._ffmpeg_semaphore._value if hasattr(self._ffmpeg_semaphore, '_value') else 'unknown'
            
            return {
                'gpu': {
                    'max': self.limits.max_gpu_jobs,
                    'available': gpu_available,
                },
                'ffmpeg': {
                    'max': self.limits.max_ffmpeg_processes,
                    'available': ffmpeg_available,
                },
                'cpu_workers': self.get_cpu_worker_count(),
                'active_jobs': list(self._job_resources.keys()),
            }
