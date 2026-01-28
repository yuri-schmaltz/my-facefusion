"""
Orchestrator Data Models
------------------------
Defines Job, Step, RunRequest and status enums with validation.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    """Job lifecycle states with valid transitions."""
    DRAFTED = "drafted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    
    @staticmethod
    def valid_transitions() -> Dict['JobStatus', List['JobStatus']]:
        """Return valid state transitions."""
        return {
            JobStatus.DRAFTED: [JobStatus.QUEUED],
            JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELED],
            JobStatus.RUNNING: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED],
            JobStatus.COMPLETED: [],  # Terminal
            JobStatus.FAILED: [JobStatus.QUEUED],  # Allow retry
            JobStatus.CANCELED: [],  # Terminal
        }
    
    def can_transition_to(self, new_status: 'JobStatus') -> bool:
        """Check if transition to new_status is valid."""
        return new_status in self.valid_transitions().get(self, [])
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED)


class StepStatus(str, Enum):
    """Step execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ErrorCode(str, Enum):
    """Standardized error codes for diagnosis."""
    SUCCESS = "SUCCESS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    IO_ERROR = "IO_ERROR"
    PATH_ERROR = "PATH_ERROR"
    FFMPEG_ERROR = "FFMPEG_ERROR"
    FFMPEG_TIMEOUT = "FFMPEG_TIMEOUT"
    PIPELINE_FAILED = "PIPELINE_FAILED"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    CUDA_ERROR = "CUDA_ERROR"
    CANCELED = "CANCELED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class Step:
    """A single processing step within a job."""
    index: int
    name: str
    status: StepStatus = StepStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'index': self.index,
            'name': self.name,
            'status': self.status.value,
            'progress': self.progress,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Step':
        """Deserialize from dictionary."""
        return cls(
            index=data['index'],
            name=data['name'],
            status=StepStatus(data['status']),
            progress=data.get('progress', 0.0),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error_message=data.get('error_message'),
        )


@dataclass
class Job:
    """A processing job with lifecycle management."""
    job_id: str
    status: JobStatus = JobStatus.DRAFTED
    progress: float = 0.0
    cancel_requested: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    steps: List[Step] = field(default_factory=list)
    
    # Metadata for provenance
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def transition_to(self, new_status: JobStatus) -> bool:
        """
        Transition to a new status if valid.
        Returns True if transition succeeded.
        """
        if self.status.can_transition_to(new_status):
            self.status = new_status
            if new_status == JobStatus.RUNNING:
                self.started_at = datetime.utcnow()
            elif new_status.is_terminal():
                self.completed_at = datetime.utcnow()
            return True
        return False
    
    def update_progress(self, progress: float) -> None:
        """Update progress (monotonic - won't decrease)."""
        self.progress = max(self.progress, min(1.0, progress))
    
    def fail(self, error_code: ErrorCode, message: str) -> None:
        """Mark job as failed with error details."""
        self.error_code = error_code
        self.error_message = message
        self.transition_to(JobStatus.FAILED)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'progress': self.progress,
            'cancel_requested': self.cancel_requested,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_code': self.error_code.value if self.error_code else None,
            'error_message': self.error_message,
            'config': self.config,
            'steps': [s.to_dict() for s in self.steps],
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Deserialize from dictionary."""
        return cls(
            job_id=data['job_id'],
            status=JobStatus(data['status']),
            progress=data.get('progress', 0.0),
            cancel_requested=data.get('cancel_requested', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error_code=ErrorCode(data['error_code']) if data.get('error_code') else None,
            error_message=data.get('error_message'),
            config=data.get('config', {}),
            steps=[Step.from_dict(s) for s in data.get('steps', [])],
            metadata=data.get('metadata', {}),
        )


@dataclass
class RunRequest:
    """Request to run a processing job."""
    source_paths: List[str]
    target_path: str
    output_path: str
    processors: List[str]
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Optional job ID (auto-generated if not provided)
    job_id: Optional[str] = None
    
    def generate_job_id(self, prefix: str = 'job') -> str:
        """Generate a unique job ID if not provided."""
        if self.job_id:
            return self.job_id
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        short_uuid = str(uuid.uuid4())[:8]
        return f"{prefix}-{timestamp}-{short_uuid}"
    
    def to_config(self) -> Dict[str, Any]:
        """Convert to job configuration dictionary."""
        config = {
            'source_paths': self.source_paths,
            'target_path': self.target_path,
            'output_path': self.output_path,
            'processors': self.processors,
        }
        config.update(self.settings)
        return config
