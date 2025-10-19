from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Optional

class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"

@dataclass
class Job:
    job_id: str
    session_id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: JobStatus = JobStatus.queued
    progress: int = 0
    message: str = ""
    options: dict = field(default_factory=dict)
    workdir: Path | None = None
    log_path: Path | None = None

@dataclass
class Session:
    session_id: str
    created_at: datetime
    input_dir: Path
