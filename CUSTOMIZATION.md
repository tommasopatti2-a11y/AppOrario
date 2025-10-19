# Customization Guide

## Integrating Your Python Program

### Step 1: Prepare Your Entrypoint

Your program must have a callable entry point that accepts:
- `input_paths: list[str]` - Paths to uploaded Excel files
- `output_dir: str` - Directory where outputs should be written
- `**options` - Additional options passed from frontend

#### Option A: Function-based (Recommended)

Create `my_runner.py`:
```python
def main(input_paths: list[str], output_dir: str, **options):
    """
    Process Excel files and generate outputs.
    
    Args:
        input_paths: List of paths to input .xlsx files
        output_dir: Directory to write output files
        options: Dict of optional parameters from frontend
    
    Returns:
        0 on success, non-zero on failure
    """
    from pathlib import Path
    import pandas as pd
    
    out = Path(output_dir)
    
    # Example: read all inputs and merge
    dfs = []
    for path in input_paths:
        df = pd.read_excel(path)
        dfs.append(df)
    
    merged = pd.concat(dfs, ignore_index=True)
    
    # Write output
    output_file = out / "merged_result.xlsx"
    merged.to_excel(output_file, index=False)
    
    # Optional: write report
    report = out / "report.txt"
    report.write_text(f"Processed {len(input_paths)} files\n")
    
    return 0  # Success

if __name__ == "__main__":
    # For standalone testing
    import sys
    sys.exit(main(["test.xlsx"], "./output"))
```

Set in `.env`:
```
APP_PROGRAM_ENTRYPOINT=my_runner.py:main
```

#### Option B: Subprocess-based

Create `my_runner.py`:
```python
import argparse
import json
import sys
from pathlib import Path

def process(input_paths, output_dir, **options):
    # Your logic here
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True)  # JSON list
    parser.add_argument("--out", required=True)     # Output directory
    parser.add_argument("--options", default="{}")  # JSON dict
    
    args = parser.parse_args()
    inputs = json.loads(args.inputs)
    opts = json.loads(args.options)
    
    try:
        exit_code = process(inputs, args.out, **opts)
        sys.exit(exit_code or 0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

Set in `.env`:
```
APP_PROGRAM_ENTRYPOINT=python my_runner.py
```

### Step 2: Configure Environment

Update `.env`:
```
APP_PROGRAM_ENTRYPOINT=my_runner.py:main
APP_MAX_FILE_SIZE_MB=100
APP_ALLOWED_EXTENSIONS=.xlsx,.xlsm
APP_JOB_TTL_MINUTES=240
```

### Step 3: Test Locally

```bash
# Run backend
python -m uvicorn app.main:app --app-dir backend --reload

# In another terminal, test via curl
curl -F "files=@test.xlsx" http://localhost:8080/upload
# Get session_id

curl -H "Content-Type: application/json" \
  -d '{"session_id":"<SESSION>","options":{}}' \
  http://localhost:8080/run
# Get job_id

curl http://localhost:8080/status/<JOB>
curl http://localhost:8080/logs/<JOB>
curl http://localhost:8080/results/<JOB>
```

---

## Excel Schema Validation

### Enable Schema Checking

Edit `backend/app/validation.py`:
```python
DEFAULT_SCHEMA = {
    "required_sheets": ["Classi", "Studenti"],
    "sheets": {
        "Classi": {
            "required_headers": ["ID", "Nome", "Anno"]
        },
        "Studenti": {
            "required_headers": ["ID", "Nome", "Cognome", "Classe"]
        }
    }
}
```

Now upload will validate:
- File has sheets "Classi" and "Studenti"
- "Classi" sheet has headers: ID, Nome, Anno
- "Studenti" sheet has headers: ID, Nome, Cognome, Classe

If validation fails, upload returns 400 with error message.

### Load Schema from JSON

```python
import json
from pathlib import Path

schema_file = Path("schema.json")
if schema_file.exists():
    DEFAULT_SCHEMA = json.loads(schema_file.read_text())
```

Then use `schema.example.json` as template.

---

## Frontend Customization

### Add Custom Parameters

Edit `frontend/src/App.tsx` in the "Parametri" section:

```tsx
<section style={{border:'1px solid #ddd', padding:16, borderRadius:8, marginBottom:16}}>
  <h2>Parametri</h2>
  
  {/* Existing checkboxes */}
  <label>
    <input 
      type="checkbox" 
      checked={!!options.check_schema} 
      onChange={e=>setOptions((o:any)=>({...o, check_schema: e.target.checked}))} 
    /> 
    Verifica schema
  </label>
  
  {/* Add custom parameter */}
  <div style={{marginTop:8}}>
    <label>Formato output: </label>
    <select value={options.output_format} onChange={e=>setOptions((o:any)=>({...o, output_format: e.target.value}))}>
      <option value="xlsx">Excel (.xlsx)</option>
      <option value="csv">CSV</option>
      <option value="json">JSON</option>
    </select>
  </div>
  
  {/* Another parameter */}
  <div style={{marginTop:8}}>
    <label>Numero righe per batch: </label>
    <input 
      type="number" 
      value={options.batch_size || 1000} 
      onChange={e=>setOptions((o:any)=>({...o, batch_size: parseInt(e.target.value)}))}
      style={{width:100}}
    />
  </div>
</section>
```

These options are passed to your entrypoint as `**options`.

### Change UI Styling

Edit `frontend/src/App.tsx` inline styles or extract to CSS:

```tsx
const styles = {
  container: { fontFamily: 'Inter, system-ui, Arial', maxWidth: 1000, margin: '0 auto', padding: 24 },
  section: { border:'1px solid #ddd', padding:16, borderRadius:8, marginBottom:16 },
  button: { padding: '8px 16px', background: '#007bff', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' },
  // ... more styles
}

// Use: style={styles.section}
```

### Change Polling Interval

Edit `frontend/src/App.tsx`:
```tsx
function startPolling() {
  if (pollRef.current) return
  pollRef.current = window.setInterval(poll, 5000)  // Changed from 2500ms to 5000ms
}
```

### Add Notifications/Toasts

Install a toast library:
```bash
npm install react-toastify
```

Use in `App.tsx`:
```tsx
import { ToastContainer, toast } from 'react-toastify'

// In upload success:
toast.success(`Upload successful: ${data.session_id}`)

// In error:
toast.error(`Upload failed: ${error}`)

// In JSX:
<ToastContainer position="bottom-right" />
```

---

## Backend Customization

### Add Authentication

Create `backend/app/auth.py`:
```python
from fastapi import Depends, HTTPException, Header
from typing import Optional

async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing authorization header")
    
    scheme, token = authorization.split(" ", 1)
    if scheme != "Bearer":
        raise HTTPException(401, "Invalid auth scheme")
    
    # Verify token (e.g., check against env var or database)
    valid_token = "your-secret-token"
    if token != valid_token:
        raise HTTPException(401, "Invalid token")
    
    return token
```

Use in endpoints:
```python
@app.post("/upload")
async def upload(files: list[UploadFile] = File(...), token: str = Depends(verify_token)):
    # Protected endpoint
    ...
```

### Add Rate Limiting

Install:
```bash
pip install slowapi
```

Use:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload")
@limiter.limit("10/minute")
async def upload(request: Request, files: list[UploadFile] = File(...)):
    ...
```

### Add Database Persistence

Install:
```bash
pip install sqlalchemy
```

Create `backend/app/database.py`:
```python
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./jobs.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class JobRecord(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True)
    session_id = Column(String)
    status = Column(String)
    progress = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)
```

Replace in-memory `job_queue.jobs` with database queries.

### Add WebSocket for Real-time Updates

```python
from fastapi import WebSocket

@app.websocket("/ws/status/{job_id}")
async def websocket_status(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            job = job_queue.get(job_id)
            if job:
                await websocket.send_json({
                    "status": job.status,
                    "progress": job.progress,
                    "message": job.message
                })
            await asyncio.sleep(1)
    except Exception:
        await websocket.close()
```

Update frontend to use WebSocket instead of polling.

### Add Email Notifications

Install:
```bash
pip install python-multipart aiosmtplib
```

Create `backend/app/email.py`:
```python
import aiosmtplib
from email.mime.text import MIMEText

async def send_job_complete_email(job_id: str, email: str, status: str):
    msg = MIMEText(f"Job {job_id} completed with status: {status}")
    msg["Subject"] = f"Job {job_id} Complete"
    msg["From"] = "noreply@example.com"
    msg["To"] = email
    
    async with aiosmtplib.SMTP(hostname="localhost") as smtp:
        await smtp.send_message(msg)
```

Call after job completion in `worker.py`.

---

## Docker Customization

### Use Different Base Image

Edit `Dockerfile`:
```dockerfile
# Use Python slim with additional tools
FROM python:3.11-slim AS backend
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```

### Mount Your Runner

Edit `docker-compose.yml`:
```yaml
volumes:
  - ./my_runner.py:/app/my_runner.py:ro
  - ./data:/data
```

### Use Environment File

Create `.env.docker`:
```
APP_PROGRAM_ENTRYPOINT=my_runner.py:main
APP_MAX_FILE_SIZE_MB=200
```

Run:
```bash
docker compose --env-file .env.docker up
```

---

## Monitoring & Logging

### Structured Logging

Edit `backend/app/logging_config.py`:
```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        return json.dumps(log_obj)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
```

### Prometheus Metrics

Add to `backend/app/main.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

uploads = Counter('uploads_total', 'Total uploads')
jobs = Counter('jobs_total', 'Total jobs', ['status'])
job_duration = Histogram('job_duration_seconds', 'Job duration')

@app.post("/upload")
async def upload(...):
    uploads.inc()
    ...

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Performance Tuning

### Increase Worker Threads

Edit `backend/app/worker.py`:
```python
class JobQueue:
    def __init__(self, num_workers=4):
        self.workers = [
            threading.Thread(target=self._worker_loop, daemon=True)
            for _ in range(num_workers)
        ]
    
    def start(self):
        for w in self.workers:
            w.start()
```

### Implement Job Batching

Modify `adapter.py` to process multiple files in parallel:
```python
import concurrent.futures

def run_entrypoint(job: Job) -> int:
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_file, f) for f in input_paths]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    return 0 if all(results) else 1
```

### Cache Results

Add caching layer:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_job_results(job_id: str):
    # Cached results
    ...
```

---

## Troubleshooting Custom Integrations

### Debug Entrypoint

Add verbose logging:
```python
def main(input_paths: list[str], output_dir: str, **options):
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Inputs: {input_paths}")
    logger.debug(f"Output dir: {output_dir}")
    logger.debug(f"Options: {options}")
    
    # Your code...
```

Check `job.log` for debug output.

### Test Entrypoint Standalone

```bash
python my_runner.py --inputs '["test1.xlsx", "test2.xlsx"]' --out ./output --options '{"key":"value"}'
```

### Check Job Status

```bash
curl http://localhost:8080/status/<JOB_ID>
curl http://localhost:8080/logs/<JOB_ID>
```

---

## Next Steps

1. **Customize entrypoint** with your business logic
2. **Configure schema validation** if needed
3. **Add authentication** for production
4. **Deploy** via Docker or Kubernetes
5. **Monitor** with logs and metrics
6. **Scale** horizontally if needed

See `README.md`, `DEPLOYMENT.md`, and `PROJECT_STRUCTURE.md` for more details.
