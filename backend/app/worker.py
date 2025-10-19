from __future__ import annotations
import queue
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
import traceback

from .models import Job, JobStatus
from .config import settings
from .storage import cleanup_dir
from .adapter import run_entrypoint


class JobQueue:
    def __init__(self):
        self.q: queue.Queue[str] = queue.Queue()
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.gc_thread = threading.Thread(target=self._gc_loop, daemon=True)

    def start(self):
        self.worker_thread.start()
        self.gc_thread.start()

    def enqueue(self, job: Job):
        with self.lock:
            self.jobs[job.job_id] = job
        self.q.put(job.job_id)

    def get(self, job_id: str) -> Job | None:
        with self.lock:
            return self.jobs.get(job_id)

    def _worker_loop(self):
        while not self.stop_event.is_set():
            try:
                job_id = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            job = self.get(job_id)
            if not job:
                continue
            try:
                job.status = JobStatus.running
                job.started_at = datetime.utcnow()
                job.progress = 5
                job.message = "Validazione e preparazione"
                # Execute entrypoint
                exit_code = run_entrypoint(job)
                if exit_code == 0:
                    job.status = JobStatus.succeeded
                    job.progress = 100
                    job.message = "Completato"
                else:
                    job.status = JobStatus.failed
                    job.progress = 100
                    job.message = f"Entrypoint exit code {exit_code}"
            except Exception:
                job.status = JobStatus.failed
                job.progress = 100
                job.message = "Errore runtime"
                # append stacktrace to log
                if job.log_path:
                    with open(job.log_path, 'a', encoding='utf-8') as f:
                        f.write("\n" + traceback.format_exc())
            finally:
                job.finished_at = datetime.utcnow()
                self.q.task_done()

    def _gc_loop(self):
        while not self.stop_event.is_set():
            try:
                ttl = timedelta(minutes=settings.JOB_TTL_MINUTES)
                cutoff = datetime.utcnow() - ttl
                with self.lock:
                    old_ids = [jid for jid, j in self.jobs.items() if j.finished_at and j.finished_at < cutoff]
                for jid in old_ids:
                    job = self.jobs.pop(jid, None)
                    if job and job.workdir:
                        cleanup_dir(job.workdir)
                time.sleep(60)
            except Exception:
                time.sleep(60)

job_queue = JobQueue()
