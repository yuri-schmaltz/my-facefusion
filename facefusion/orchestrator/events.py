"""
Event Bus for Job Events
-------------------------
Provides real-time event streaming for UI integration via async generators.
"""
import asyncio
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Callable, AsyncIterator
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types of job events."""
    JOB_CREATED = "job_created"
    JOB_QUEUED = "job_queued"
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELED = "job_canceled"
    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    LOG = "log"


@dataclass
class JobEvent:
    """An event related to a job."""
    job_id: str
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON transmission."""
        return {
            'job_id': self.job_id,
            'event_type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
        }


class EventBus:
    """
    Event bus for publishing and subscribing to job events.
    
    Supports both sync callbacks and async generators for SSE/WebSocket.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}  # job_id -> queues
        self._global_subscribers: Set[asyncio.Queue] = set()  # All events
        self._sync_callbacks: Set[Callable[[JobEvent], None]] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for async operations."""
        self._loop = loop
    
    def publish(self, event: JobEvent) -> None:
        """Publish an event to all subscribers."""
        with self._lock:
            # Call sync callbacks
            for callback in self._sync_callbacks:
                try:
                    callback(event)
                except Exception:
                    pass  # Don't let callback errors break publishing
            
            # Push to async queues
            queues = set()
            queues.update(self._global_subscribers)
            if event.job_id in self._subscribers:
                queues.update(self._subscribers[event.job_id])
            
            for queue in queues:
                try:
                    if self._loop:
                        self._loop.call_soon_threadsafe(
                            lambda q=queue, e=event: q.put_nowait(e)
                        )
                    else:
                        queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass  # Drop if queue is full
                except Exception:
                    pass
    
    def add_callback(self, callback: Callable[[JobEvent], None]) -> None:
        """Add a synchronous callback for all events."""
        with self._lock:
            self._sync_callbacks.add(callback)
    
    def remove_callback(self, callback: Callable[[JobEvent], None]) -> None:
        """Remove a synchronous callback."""
        with self._lock:
            self._sync_callbacks.discard(callback)
    
    async def subscribe(self, job_id: Optional[str] = None, max_size: int = 100) -> AsyncIterator[JobEvent]:
        """
        Subscribe to events for a specific job or all jobs.
        
        Usage:
            async for event in event_bus.subscribe("job-123"):
                print(event)
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        
        with self._lock:
            if job_id:
                if job_id not in self._subscribers:
                    self._subscribers[job_id] = set()
                self._subscribers[job_id].add(queue)
            else:
                self._global_subscribers.add(queue)
        
        try:
            while True:
                event = await queue.get()
                yield event
                
                # Stop if terminal event
                if event.event_type in (
                    EventType.JOB_COMPLETED,
                    EventType.JOB_FAILED,
                    EventType.JOB_CANCELED
                ):
                    if job_id and event.job_id == job_id:
                        break
        finally:
            with self._lock:
                if job_id and job_id in self._subscribers:
                    self._subscribers[job_id].discard(queue)
                    if not self._subscribers[job_id]:
                        del self._subscribers[job_id]
                else:
                    self._global_subscribers.discard(queue)
    
    def create_queue(self, job_id: Optional[str] = None, max_size: int = 100) -> asyncio.Queue:
        """Create a queue for receiving events (for manual polling)."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        
        with self._lock:
            if job_id:
                if job_id not in self._subscribers:
                    self._subscribers[job_id] = set()
                self._subscribers[job_id].add(queue)
            else:
                self._global_subscribers.add(queue)
        
        return queue
    
    def remove_queue(self, queue: asyncio.Queue, job_id: Optional[str] = None) -> None:
        """Remove a queue from subscribers."""
        with self._lock:
            if job_id and job_id in self._subscribers:
                self._subscribers[job_id].discard(queue)
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]
            else:
                self._global_subscribers.discard(queue)


# Convenience functions for creating common events
def create_progress_event(job_id: str, progress: float, phase: str = "") -> JobEvent:
    """Create a progress event."""
    return JobEvent(
        job_id=job_id,
        event_type=EventType.JOB_PROGRESS,
        data={'progress': progress, 'phase': phase}
    )


def create_status_event(job_id: str, status: str, message: str = "") -> JobEvent:
    """Create a status change event."""
    event_type_map = {
        'queued': EventType.JOB_QUEUED,
        'running': EventType.JOB_STARTED,
        'completed': EventType.JOB_COMPLETED,
        'failed': EventType.JOB_FAILED,
        'canceled': EventType.JOB_CANCELED,
    }
    return JobEvent(
        job_id=job_id,
        event_type=event_type_map.get(status, EventType.JOB_STARTED),
        data={'status': status, 'message': message}
    )


def create_log_event(job_id: str, level: str, message: str) -> JobEvent:
    """Create a log event."""
    return JobEvent(
        job_id=job_id,
        event_type=EventType.LOG,
        data={'level': level, 'message': message}
    )
