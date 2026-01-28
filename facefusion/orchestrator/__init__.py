"""
FaceFusion Orchestrator Package
-------------------------------
Provides robust job lifecycle management with:
- SQLite-persistent job store
- Event bus for UI streaming
- Resource management (GPU semaphore, concurrency)
- Cooperative cancelation
- Structured logging
"""
from facefusion.orchestrator.models import Job, Step, RunRequest, JobStatus, StepStatus
from facefusion.orchestrator.store import JobStore
from facefusion.orchestrator.events import EventBus, JobEvent
from facefusion.orchestrator.resources import ResourceManager
from facefusion.orchestrator.orchestrator import Orchestrator

# Singleton orchestrator instance
_orchestrator: 'Orchestrator | None' = None


def get_orchestrator() -> Orchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        import os
        from facefusion import state_manager
        
        # Default jobs path
        jobs_path = state_manager.get_item('jobs_path') or '.jobs'
        db_path = os.path.join(jobs_path, 'orchestrator.db')
        
        store = JobStore(db_path)
        event_bus = EventBus()
        resources = ResourceManager()
        _orchestrator = Orchestrator(store, event_bus, resources)
    
    return _orchestrator


def reset_orchestrator() -> None:
    """Reset the orchestrator (for testing)."""
    global _orchestrator
    _orchestrator = None


__all__ = [
    'Job', 'Step', 'RunRequest', 'JobStatus', 'StepStatus',
    'JobStore', 'EventBus', 'JobEvent', 'ResourceManager', 'Orchestrator',
    'get_orchestrator', 'reset_orchestrator'
]
