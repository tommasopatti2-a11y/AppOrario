from __future__ import annotations
import io
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, PlainTextResponse, ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import Job, JobStatus, Session
from .storage import sanitize_filename, ensure_session_dirs, create_job_dir, total_size, list_files, zip_directory
from .worker import job_queue
from .validation import validator
from .logging_config import logger

ALLOWED_EXTS = set(settings.ALLOWED_EXTENSIONS)
MAX_TOTAL = settings.MAX_FILE_SIZE_MB * 1024 * 1024

app = FastAPI(title="Excel Runner API", default_response_class=ORJSONResponse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Nota: montiamo StaticFiles alla fine del file, dopo aver registrato tutte le API,
# per evitare che le richieste POST/PUT verso "/upload", "/run", ecc. finiscano
# al router statico (che accetta solo GET/HEAD) causando 405.

SESSIONS: dict[str, Session] = {}

@app.on_event("startup")
async def on_startup():
    logger.info(f"Starting Excel Runner API")
    logger.info(f"PROGRAM_ENTRYPOINT: {settings.PROGRAM_ENTRYPOINT}")
    logger.info(f"MAX_FILE_SIZE_MB: {settings.MAX_FILE_SIZE_MB}")
    logger.info(f"ALLOWED_EXTENSIONS: {settings.ALLOWED_EXTENSIONS}")
    logger.info(f"JOB_TTL_MINUTES: {settings.JOB_TTL_MINUTES}")
    import sys
    logger.info(f"PYTHON_EXECUTABLE: {sys.executable}")
    try:
        import pandas as _pd
        logger.info(f"pandas_version: {_pd.__version__}")
    except Exception as _e:
        logger.error(f"pandas_import_error: {_e}")
    job_queue.start()


@app.get("/health")
async def health():
    """Health check endpoint."""
    import sys
    info = {"status": "ok", "version": "0.1.0", "python": sys.executable}
    try:
        import pandas as _pd
        info["pandas_version"] = _pd.__version__
    except Exception as _e:
        info["pandas_error"] = str(_e)
    return info


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "Nessun file caricato")
    exts = []
    total = 0
    session_id = str(uuid.uuid4())
    base, inputs_dir, _jobs = ensure_session_dirs(session_id)
    logger.info(f"Upload session {session_id}: {len(files)} files")

    # Helper: compare uploaded Excel structure against example file if present
    def compare_with_example(fname: str, uploaded_path: Path) -> tuple[bool, str | None]:
        try:
            examples_dir = Path(__file__).resolve().parents[2] / "examples"
            example_path = examples_dir / fname
            if not example_path.exists():
                return True, None  # no example available => skip
            import pandas as pd
            # Compare sheet names
            up_xl = pd.ExcelFile(str(uploaded_path))
            ex_xl = pd.ExcelFile(str(example_path))
            if set(up_xl.sheet_names) != set(ex_xl.sheet_names):
                return False, f"Fogli diversi: {up_xl.sheet_names} vs {ex_xl.sheet_names}"
            # Compare header columns for each sheet
            for sh in ex_xl.sheet_names:
                up_cols = pd.read_excel(str(uploaded_path), sheet_name=sh, nrows=0).columns.tolist()
                ex_cols = pd.read_excel(str(example_path), sheet_name=sh, nrows=0).columns.tolist()
                if up_cols != ex_cols:
                    return False, f"Intestazioni diverse nel foglio '{sh}': {up_cols} vs {ex_cols}"
            return True, None
        except Exception as e:
            # In caso di errore imprevisto nella comparazione, non bloccare l'upload
            logger.warning(f"Example compare skipped for {fname}: {e}")
            return True, None

    for uf in files:
        name = sanitize_filename(uf.filename or "file")
        ext = Path(name).suffix.lower()
        exts.append(ext)
        if ext not in ALLOWED_EXTS:
            logger.warning(f"Upload rejected: invalid extension {ext}")
            raise HTTPException(400, f"Estensione non permessa: {ext}")
        data = await uf.read()
        total += len(data)
        if total > MAX_TOTAL:
            logger.warning(f"Upload rejected: size {total} > {MAX_TOTAL}")
            raise HTTPException(413, f"Dimensione totale supera limite: {settings.MAX_FILE_SIZE_MB} MB")
        file_path = inputs_dir / name
        file_path.write_bytes(data)
        
        # Optional schema validation
        is_valid, error_msg = validator.validate(file_path)
        if not is_valid:
            logger.warning(f"Upload validation failed for {name}: {error_msg}")
            raise HTTPException(400, f"Validazione schema fallita per {name}: {error_msg}")

        # Structural comparison with example file (if present)
        ok, reason = compare_with_example(name, file_path)
        if not ok:
            logger.warning(f"Upload structure mismatch for {name}: {reason}")
            raise HTTPException(status_code=400, detail={
                "bad_file": name,
                "reason": "Verificare il file caricato, la sua struttura differisce da quella prevista",
                "debug": reason,
            })

    SESSIONS[session_id] = Session(session_id=session_id, created_at=datetime.utcnow(), input_dir=inputs_dir)
    logger.info(f"Upload session {session_id} completed: {total} bytes")
    return {"session_id": session_id, "files": [f.filename for f in files], "total_bytes": total}


@app.post("/run")
async def run(body: dict):
    session_id = body.get("session_id")
    options = body.get("options", {})
    if not session_id or session_id not in SESSIONS:
        logger.warning(f"Run rejected: invalid session_id {session_id}")
        raise HTTPException(400, "session_id non valido")
    job_id = str(uuid.uuid4())
    workdir = create_job_dir(session_id, job_id)
    log_path = workdir / "job.log"
    log_path.touch(exist_ok=True)
    job = Job(job_id=job_id, session_id=session_id, created_at=datetime.utcnow(), options=options, workdir=workdir, log_path=log_path)
    job_queue.enqueue(job)
    logger.info(f"Job {job_id} enqueued for session {session_id}")
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def status(job_id: str):
    job = job_queue.get(job_id)
    if not job:
        raise HTTPException(404, "job non trovato")
    return {
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


@app.get("/logs/{job_id}", response_class=PlainTextResponse)
async def logs(job_id: str):
    job = job_queue.get(job_id)
    if not job or not job.log_path:
        raise HTTPException(404, "job non trovato")
    return Path(job.log_path).read_text(encoding="utf-8")


@app.get("/results/{job_id}")
async def results(job_id: str):
    job = job_queue.get(job_id)
    if not job or not job.workdir:
        raise HTTPException(404, "job non trovato")
    files = [f for f in list_files(job.workdir) if not (f["filename"].endswith("_OK.txt") or f["filename"] == "job.log")]
    for f in files:
        f["download_url"] = f"/download/{job_id}/{f['filename']}"
    return files


@app.get("/download/{job_id}/all.zip")
async def download_all(job_id: str):
    job = job_queue.get(job_id)
    if not job or not job.workdir:
        raise HTTPException(404, "job non trovato")
    zip_path = job.workdir / "all.zip"
    zip_directory(job.workdir, zip_path)
    return FileResponse(zip_path, filename=f"results_{job_id}.zip")


@app.get("/download/{job_id}/{filename:path}")
async def download_file(job_id: str, filename: str):
    job = job_queue.get(job_id)
    if not job or not job.workdir:
        raise HTTPException(404, "job non trovato")
    target = (job.workdir / filename).resolve()
    # prevent path traversal
    if not str(target).startswith(str(job.workdir.resolve())):
        raise HTTPException(400, "path non valido")
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "file non trovato")
    return FileResponse(target, filename=target.name)


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = job_queue.get(job_id)
    if not job or not job.workdir:
        raise HTTPException(404, "job non trovato")
    cleanup_dir(job.workdir)
    job.message = "Eliminato"
    job.status = JobStatus.succeeded
    return {"deleted": True}


# Monta gli esempi se esiste la cartella 'examples' nella root del progetto
try:
    EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
    if EXAMPLES_DIR.exists():
        app.mount("/examples", StaticFiles(directory=str(EXAMPLES_DIR), html=False), name="examples")
except Exception:
    pass

# Monta i file statici (frontend) DOPO tutte le rotte API
if settings.FRONTEND_DIST_DIR and Path(settings.FRONTEND_DIST_DIR).exists():
    app.mount("/", StaticFiles(directory=str(settings.FRONTEND_DIST_DIR), html=True), name="static")
