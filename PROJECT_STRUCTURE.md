# Project Structure

```
AppOrario/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, all endpoints
│   │   ├── config.py                 # Settings from env (pydantic-settings)
│   │   ├── models.py                 # Job, Session, JobStatus dataclasses
│   │   ├── storage.py                # File ops: sanitize, zip, cleanup
│   │   ├── worker.py                 # Job queue, worker thread, TTL GC
│   │   ├── adapter.py                # Run PROGRAM_ENTRYPOINT (func/subprocess)
│   │   ├── validation.py             # Optional Excel schema validation
│   │   └── logging_config.py         # Logging setup
│   ├── requirements.txt              # Python deps
│   └── run_uvicorn.py                # Helper to run uvicorn with reload
│
├── frontend/                         # React + Vite
│   ├── src/
│   │   ├── main.tsx                  # Entry point
│   │   ├── App.tsx                   # Main UI component
│   │   └── vite-env.d.ts             # Vite type definitions
│   ├── index.html                    # HTML template
│   ├── package.json                  # Node deps
│   ├── tsconfig.json                 # TypeScript config
│   ├── vite.config.ts                # Vite config (with API proxy)
│   └── dist/                         # Build output (created by `npm run build`)
│
├── Dockerfile                        # Multi-stage build (frontend + backend)
├── docker-compose.yml                # Docker Compose config
├── start.sh                          # Bash script for local dev (Linux/macOS)
├── start.bat                         # Batch script for local dev (Windows)
│
├── runner.py                         # Example entrypoint (replace with yours)
├── test_e2e.py                       # E2E test script
│
├── .env.example                      # Example env vars (copy to .env)
├── .env.local.example                # Alternative env template
├── .gitignore                        # Git ignore rules
│
├── README.md                         # Full documentation
├── QUICK_START.md                    # Quick start guide (Windows-friendly)
├── PROJECT_STRUCTURE.md              # This file
├── schema.example.json               # Example Excel schema validation config
│
└── data/                             # Local storage (created at runtime)
    └── sessions/
        └── <session_id>/
            ├── inputs/               # Uploaded files
            └── jobs/
                └── <job_id>/
                    ├── job.log       # Job execution log
                    └── <outputs>     # Generated files
```

## Backend Architecture

### Flow
1. **Upload** (`POST /upload`)
   - Receive multipart files
   - Sanitize names, validate extensions, check total size
   - Optional schema validation
   - Save to `data/sessions/<session_id>/inputs/`
   - Return `session_id`

2. **Run** (`POST /run`)
   - Create job with `job_id`
   - Create workdir: `data/sessions/<session_id>/jobs/<job_id>/`
   - Enqueue job to `job_queue`
   - Return `job_id`

3. **Worker Thread** (`worker.py`)
   - Dequeue jobs and execute `adapter.run_entrypoint(job)`
   - Update job status: `queued → running → succeeded|failed`
   - Capture logs to `job.log`
   - GC thread removes jobs older than TTL

4. **Adapter** (`adapter.py`)
   - Import or subprocess the entrypoint
   - Pass `input_paths` (from `inputs/`), `output_dir` (workdir), `**options`
   - Capture stdout/stderr to log
   - Return exit code

5. **Results** (`GET /results/{job_id}`)
   - List all files in workdir
   - Return with download URLs

6. **Download** (`GET /download/{job_id}/{filename}` or `/all.zip`)
   - Serve file or ZIP archive
   - Prevent path traversal

### Key Classes/Functions

- **`Job`** (models.py): Dataclass with id, status, progress, message, timestamps, workdir, log_path
- **`JobQueue`** (worker.py): In-memory queue with worker thread + GC
- **`run_entrypoint`** (adapter.py): Execute entrypoint (function or subprocess)
- **`sanitize_filename`** (storage.py): Remove unsafe chars from filenames
- **`zip_directory`** (storage.py): Create ZIP of workdir (excluding the ZIP itself)
- **`SchemaValidator`** (validation.py): Validate Excel sheets/headers (optional)

## Frontend Architecture

### Components
- **App.tsx**: Main component with state management
  - `files`: Selected files
  - `sessionId`: Current session
  - `jobId`: Current job
  - `status`: Job status (from polling)
  - `logText`: Job logs
  - `results`: Output files list
  - `options`: Optional parameters (JSON)

### Sections
1. **Upload**: Drag&drop + file picker, file list, upload button
2. **Parameters**: Optional checkboxes/selects for entrypoint options
3. **Status**: Progress bar, timestamps, log viewer with polling
4. **Results**: Table of output files, download buttons, ZIP download

### Polling
- `GET /status/{job_id}` every 2.5s
- `GET /logs/{job_id}` every 2.5s
- Stop when job status is `succeeded` or `failed`

## Configuration

### Environment Variables (prefix `APP_`)
- `PROGRAM_ENTRYPOINT`: Path to entrypoint (e.g., `runner.py:main`)
- `MAX_FILE_SIZE_MB`: Max total upload size (default 50)
- `ALLOWED_EXTENSIONS`: Comma-separated list (default `.xlsx`)
- `JOB_TTL_MINUTES`: Job lifetime before cleanup (default 120)
- `OUTPUT_DIR_BASE`: Storage base path (default `./data`)
- `FRONTEND_DIST_DIR`: Path to frontend build (for static serving)
- `HOST`: Server host (default `0.0.0.0`)
- `PORT`: Server port (default `8080`)

### Loading
- From `.env` file (pydantic-settings)
- Environment variables override `.env`
- Defaults in `config.py`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload files → `session_id` |
| POST | `/run` | Start job → `job_id` |
| GET | `/status/{job_id}` | Job status + progress |
| GET | `/logs/{job_id}` | Job logs (text) |
| GET | `/results/{job_id}` | List output files |
| GET | `/download/{job_id}/{filename}` | Download single file |
| GET | `/download/{job_id}/all.zip` | Download all as ZIP |
| DELETE | `/jobs/{job_id}` | Delete job + cleanup |

## Security & Isolation

- **Path Traversal**: Filenames sanitized, download paths validated
- **Session Isolation**: Each upload gets unique `session_id` with dedicated folder
- **Job Isolation**: Each job gets unique `job_id` with dedicated workdir
- **Size Limits**: Total upload size checked before saving
- **Extension Whitelist**: Only allowed extensions accepted
- **TTL Cleanup**: Old jobs auto-deleted after TTL expires
- **CORS**: Enabled for all origins (configurable)

## Deployment

### Local Dev
```bash
# Backend
python -m uvicorn app.main:app --app-dir backend --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

### Docker
```bash
docker compose up --build
```

### Production
- Build frontend: `npm run build`
- Set `APP_FRONTEND_DIST_DIR` to `frontend/dist`
- Run backend with `uvicorn` (or gunicorn for multi-worker)
- Use reverse proxy (nginx) for SSL, compression, caching

## Testing

### Manual
1. Upload `.xlsx` files via UI
2. Click "Esegui"
3. Watch progress and logs
4. Download results

### Automated
```bash
python test_e2e.py
```
Requires backend running on `http://localhost:8080`

## Extending

### Custom Entrypoint
1. Create `my_runner.py` with `main(input_paths, output_dir, **options)`
2. Set `APP_PROGRAM_ENTRYPOINT=my_runner.py:main`
3. Ensure outputs are written to `output_dir`

### Schema Validation
1. Edit `backend/app/validation.py` or load JSON schema
2. Define required sheets and headers
3. Validation runs on upload if enabled

### Authentication
- Add middleware in `main.py` to check bearer token
- Store tokens in env or database

### Persistence
- Replace in-memory `job_queue.jobs` dict with SQLite/PostgreSQL
- Store job metadata for audit trail

### WebSocket/SSE
- Replace polling with Server-Sent Events or WebSocket
- Real-time progress updates without polling interval

## Troubleshooting

### Job stuck in `running`
- Check `job.log` for errors
- Verify entrypoint is working standalone
- Check worker thread is alive

### Files not appearing in results
- Verify entrypoint writes to `output_dir` parameter
- Check file permissions
- Look at `job.log` for errors

### Upload fails with 413
- File size exceeds `MAX_FILE_SIZE_MB`
- Increase limit in `.env`

### Schema validation fails
- Verify required sheets exist in Excel file
- Check header names match exactly (case-sensitive)
- See `schema.example.json` for format

## Performance Notes

- In-memory job queue: suitable for ~100s of concurrent jobs
- For 1000s of jobs, use external queue (Redis, RabbitMQ)
- Frontend polling every 2.5s: adjust in `App.tsx` for lower latency
- ZIP creation on-demand: cache if needed
- Log file grows unbounded: implement rotation if needed
