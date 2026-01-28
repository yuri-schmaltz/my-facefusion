import logging
import json
import os
from typing import Optional

class JobContextFilter(logging.Filter):
    """Filter that injects job_id into log records."""
    def __init__(self, job_id: str):
        self.job_id = job_id
    
    def filter(self, record):
        record.job_id = self.job_id
        return True

class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON structures."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "job_id": getattr(record, 'job_id', 'N/A'),
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def configure_root_logger(log_level: str = 'INFO'):
    """Configure the root logger with basic formatting."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_job_logger(job_id: str, log_dir: str) -> logging.Logger:
    """
    Create a logger specifically for a job that writes to a file in log_dir.
    """
    logger = logging.getLogger(f"job.{job_id}")
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{job_id}.json.log")
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(JsonFormatter())
    
    logger.addHandler(handler)
    logger.addFilter(JobContextFilter(job_id))
    
    # Prevent propagation to avoid spamming the main log with raw JSON events from jobs
    # or let it propagate but filter there? 
    # Usually we want job logs isolated to the file, but maybe some info in main log.
    # For now, let's stop propagation.
    logger.propagate = False
    
    return logger
