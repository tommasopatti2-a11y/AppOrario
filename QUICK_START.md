# Quick Start (Windows)

## Prerequisites
- Python 3.11+ (check: `python --version`)
- Node 18+ (check: `npm --version`)
- Git (optional, for cloning)

## Option 1: Local Dev (Fastest for development)

### 1. Backend
```powershell
# From project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8080 --reload
```
Backend runs on `http://localhost:8080`

### 2. Frontend (new PowerShell window)
```powershell
cd frontend
npm install
npm run dev
```
Frontend dev server on `http://localhost:5173` (auto-proxies API calls to backend)

### 3. Test
Open `http://localhost:5173` in browser and upload a test `.xlsx` file.

---

## Option 2: Docker (Recommended for production)

### 1. Build & Run
```powershell
docker compose up --build
```
App on `http://localhost:8080` (includes frontend static files)

### 2. Stop
```powershell
docker compose down
```

---

## Option 3: Batch Script (Windows only)
```powershell
.\start.bat
```
Builds frontend, installs deps, starts backend with frontend dist mounted.

---

## Configuration

### Env File
Copy `.env.example` to `.env` and customize:
```
APP_PROGRAM_ENTRYPOINT=runner.py:main
APP_MAX_FILE_SIZE_MB=50
APP_ALLOWED_EXTENSIONS=.xlsx
APP_JOB_TTL_MINUTES=120
```

### Schema Validation (Optional)
Edit `backend/app/validation.py` or load a JSON schema to enforce required sheets/headers.

---

## Testing

### Manual Test
1. Upload 2–3 `.xlsx` files via UI
2. Click "Esegui"
3. Watch progress bar and logs
4. Download results individually or as ZIP

### Automated Test
```powershell
# Requires backend running
python test_e2e.py
```

---

## Troubleshooting

### Port 8080 already in use
```powershell
# Find process using port 8080
netstat -ano | findstr :8080
# Kill it (replace PID)
taskkill /PID <PID> /F
```

### npm install fails
```powershell
npm cache clean --force
npm install
```

### Python venv issues
```powershell
# Remove old venv and recreate
rmdir .venv /s /q
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Check port: `netstat -ano | findstr :8080`
- Check env file: `.env` should not have syntax errors

---

## Next Steps

1. **Customize runner.py** with your actual program logic
2. **Update PROGRAM_ENTRYPOINT** env var to point to your runner
3. **Add schema validation** if needed (see `schema.example.json`)
4. **Deploy** via Docker to production

---

## API Examples

```powershell
# Upload
$files = @(Get-Item "test1.xlsx", "test2.xlsx")
$form = @{}
$files | ForEach-Object { $form[$_.Name] = $_.FullName }
Invoke-WebRequest -Uri "http://localhost:8080/upload" -Form $form

# Run job
$body = @{
    session_id = "<SESSION_ID>"
    options = @{ check_schema = $false; locale = "it" }
} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8080/run" -Method POST -Body $body -ContentType "application/json"

# Check status
Invoke-WebRequest -Uri "http://localhost:8080/status/<JOB_ID>"

# Download ZIP
Invoke-WebRequest -Uri "http://localhost:8080/download/<JOB_ID>/all.zip" -OutFile "results.zip"
```

---

## Support

See `README.md` for full documentation, architecture details, and API contract.
