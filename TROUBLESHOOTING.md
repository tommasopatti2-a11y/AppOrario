# Troubleshooting Guide

## Backend Issues

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Or manually
pip install fastapi uvicorn python-multipart pydantic pydantic-settings
```

---

**Error:** `Address already in use: ('0.0.0.0', 8080)`

**Solution:**
```bash
# Find process using port 8080
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Linux/macOS

# Kill the process
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/macOS

# Or use different port
python -m uvicorn app.main:app --app-dir backend --port 8081
```

---

**Error:** `Python 3.10 or lower`

**Solution:**
```bash
# Check version
python --version

# Need Python 3.11+
# Download from python.org or use package manager
```

---

### Backend crashes on startup

**Error:** `Traceback: ... in config.py`

**Solution:**
```bash
# Check .env file for syntax errors
cat .env

# Verify env var format
APP_PROGRAM_ENTRYPOINT=runner.py:main
APP_MAX_FILE_SIZE_MB=50
# No spaces around =
```

---

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: './data'`

**Solution:**
```bash
# Create data directory
mkdir data

# Or set custom path in .env
APP_OUTPUT_DIR_BASE=/tmp/excel-runner
```

---

### Health check fails

**Error:** `curl: (7) Failed to connect to localhost port 8080`

**Solution:**
```bash
# Verify backend is running
python -m uvicorn app.main:app --app-dir backend --reload

# Check if listening
netstat -ano | findstr :8080

# Try with explicit host
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8080
```

---

### Job stuck in "running"

**Symptoms:** Job status never changes from `running`, no output files

**Solution:**

1. **Check logs:**
   ```bash
   curl http://localhost:8080/logs/<JOB_ID>
   ```

2. **Verify entrypoint works standalone:**
   ```bash
   python runner.py --inputs '["test.xlsx"]' --out ./test_output --options '{}'
   ```

3. **Check worker thread:**
   ```bash
   # Look for worker thread in process list
   ps aux | grep python
   ```

4. **Restart backend:**
   ```bash
   # Kill and restart
   pkill -f uvicorn
   python -m uvicorn app.main:app --app-dir backend --reload
   ```

---

### Upload fails with 400

**Error:** `Estensione non permessa: .xls`

**Solution:**
```bash
# Update allowed extensions in .env
APP_ALLOWED_EXTENSIONS=.xlsx,.xlsm,.xls

# Or in config.py
ALLOWED_EXTENSIONS: list[str] = [".xlsx", ".xlsm", ".xls"]
```

---

### Upload fails with 413

**Error:** `Dimensione totale supera limite: 50 MB`

**Solution:**
```bash
# Increase limit in .env
APP_MAX_FILE_SIZE_MB=200

# Or reduce file size before upload
```

---

### Schema validation fails

**Error:** `Validazione schema fallita per test.xlsx: Fogli mancanti: Classi, Studenti`

**Solution:**

1. **Check Excel file has required sheets:**
   - Open in Excel
   - Verify sheet names match exactly (case-sensitive)

2. **Disable schema validation:**
   ```python
   # In backend/app/validation.py
   DEFAULT_SCHEMA = {
       "required_sheets": [],  # Empty
       "sheets": {}
   }
   ```

3. **Update schema to match your file:**
   ```python
   DEFAULT_SCHEMA = {
       "required_sheets": ["Sheet1"],  # Your sheet names
       "sheets": {
           "Sheet1": {
               "required_headers": ["Col1", "Col2"]  # Your headers
           }
       }
   }
   ```

---

## Frontend Issues

### Frontend won't build

**Error:** `npm: command not found`

**Solution:**
```bash
# Install Node.js 18+
# Download from nodejs.org

# Verify installation
node --version
npm --version
```

---

**Error:** `npm ERR! code ERESOLVE`

**Solution:**
```bash
# Clear cache
npm cache clean --force

# Reinstall
rm -rf node_modules package-lock.json
npm install
```

---

**Error:** `Cannot find module 'react'`

**Solution:**
```bash
cd frontend
npm install
npm run build
```

---

### Frontend won't start dev server

**Error:** `Port 5173 already in use`

**Solution:**
```bash
# Use different port
npm run dev -- --port 5174

# Or kill process using port
lsof -i :5173 | grep node | awk '{print $2}' | xargs kill -9
```

---

**Error:** `VITE v5.x.x  ready in xxx ms`

**But page shows blank or 404**

**Solution:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8080/health
   ```

2. **Check proxy configuration in vite.config.ts:**
   ```typescript
   server: {
     proxy: {
       '/upload': 'http://localhost:8080',
       '/run': 'http://localhost:8080',
       // ... etc
     }
   }
   ```

3. **Check browser console for errors:**
   - Open DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

---

### API calls fail from frontend

**Error:** `CORS error` or `Failed to fetch`

**Solution:**

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8080/health
   ```

2. **Check CORS is enabled in backend:**
   ```python
   # In backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Allow all origins
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Check API base URL in frontend:**
   ```typescript
   // In frontend/src/App.tsx
   const API_BASE = import.meta.env.VITE_API_BASE || ''
   // Should be empty for proxy, or http://localhost:8080 for direct
   ```

---

### Upload button doesn't work

**Symptoms:** Click upload, nothing happens

**Solution:**

1. **Check browser console for errors (F12)**

2. **Verify backend is running:**
   ```bash
   curl http://localhost:8080/health
   ```

3. **Check file is selected:**
   - Make sure files are in the list before clicking upload

4. **Check file size:**
   - File must be < `APP_MAX_FILE_SIZE_MB`

---

### Progress bar stuck at 0%

**Symptoms:** Job runs but progress never updates

**Solution:**

1. **Check polling interval:**
   ```typescript
   // In frontend/src/App.tsx, increase interval
   pollRef.current = window.setInterval(poll, 5000)  // 5 seconds
   ```

2. **Check job status manually:**
   ```bash
   curl http://localhost:8080/status/<JOB_ID>
   ```

3. **Check backend logs:**
   ```bash
   # Look for errors in backend console
   ```

---

## Docker Issues

### Docker build fails

**Error:** `failed to solve with frontend dockerfile.v0`

**Solution:**

1. **Check Docker is running:**
   ```bash
   docker --version
   docker ps
   ```

2. **Check Dockerfile syntax:**
   ```bash
   docker build --no-cache -t excel-runner:latest .
   ```

3. **Check disk space:**
   ```bash
   df -h
   docker system prune  # Clean up unused images
   ```

---

**Error:** `npm: command not found` (during build)

**Solution:**

1. **Ensure Node is in build image:**
   ```dockerfile
   FROM node:20-alpine AS frontend
   ```

2. **Rebuild without cache:**
   ```bash
   docker compose build --no-cache
   ```

---

### Docker container exits immediately

**Error:** Container starts then stops

**Solution:**

1. **Check logs:**
   ```bash
   docker compose logs app
   ```

2. **Check entrypoint:**
   ```bash
   # Verify runner.py exists and is accessible
   docker compose exec app ls -la /app/runner.py
   ```

3. **Check environment:**
   ```bash
   docker compose exec app env | grep APP_
   ```

---

### Can't access app in Docker

**Error:** `Connection refused` when accessing `http://localhost:8080`

**Solution:**

1. **Check container is running:**
   ```bash
   docker compose ps
   ```

2. **Check port mapping:**
   ```bash
   docker compose ps
   # Should show 0.0.0.0:8080->8080/tcp
   ```

3. **Check logs:**
   ```bash
   docker compose logs -f app
   ```

4. **Try direct container IP:**
   ```bash
   docker inspect <container_id> | grep IPAddress
   curl http://<container_ip>:8080/health
   ```

---

### Volume mount not working

**Error:** Files not visible in container

**Solution:**

1. **Check docker-compose.yml:**
   ```yaml
   volumes:
     - ./runner.py:/app/runner.py:ro
     - data:/data
   ```

2. **Verify file exists:**
   ```bash
   ls -la runner.py
   ```

3. **Check permissions:**
   ```bash
   chmod 644 runner.py
   ```

4. **Restart container:**
   ```bash
   docker compose down
   docker compose up
   ```

---

## Job Execution Issues

### Job fails immediately

**Error:** Job status shows `failed` after few seconds

**Solution:**

1. **Check logs:**
   ```bash
   curl http://localhost:8080/logs/<JOB_ID>
   ```

2. **Verify entrypoint exists:**
   ```bash
   ls -la runner.py
   python runner.py --help
   ```

3. **Test entrypoint standalone:**
   ```bash
   python runner.py --inputs '["test.xlsx"]' --out ./test_output --options '{}'
   ```

4. **Check entrypoint path in .env:**
   ```bash
   APP_PROGRAM_ENTRYPOINT=runner.py:main
   # Should match actual file
   ```

---

### Job produces no output files

**Symptoms:** Job succeeds but no files in results

**Solution:**

1. **Check output directory:**
   ```bash
   ls -la data/sessions/<SESSION_ID>/jobs/<JOB_ID>/
   ```

2. **Verify entrypoint writes to output_dir:**
   ```python
   def main(input_paths, output_dir, **options):
       from pathlib import Path
       out = Path(output_dir)
       (out / "result.txt").write_text("test")  # Write something
       return 0
   ```

3. **Check entrypoint logs:**
   ```bash
   curl http://localhost:8080/logs/<JOB_ID>
   ```

---

### Job times out

**Error:** Job runs for hours without completing

**Solution:**

1. **Check if stuck:**
   ```bash
   curl http://localhost:8080/logs/<JOB_ID>
   # Should have recent output
   ```

2. **Increase timeout (if applicable):**
   ```python
   # In adapter.py, add timeout
   proc = subprocess.Popen(..., timeout=3600)  # 1 hour
   ```

3. **Kill stuck job:**
   ```bash
   curl -X DELETE http://localhost:8080/jobs/<JOB_ID>
   ```

---

## Storage & Cleanup Issues

### Disk space fills up

**Symptoms:** Disk full error, can't upload new files

**Solution:**

1. **Check disk usage:**
   ```bash
   df -h
   du -sh data/
   ```

2. **Clean old jobs manually:**
   ```bash
   rm -rf data/sessions/*/jobs/*
   ```

3. **Reduce TTL:**
   ```bash
   APP_JOB_TTL_MINUTES=60  # Clean up after 1 hour
   ```

4. **Archive old results:**
   ```bash
   tar czf archive.tar.gz data/
   rm -rf data/
   ```

---

### Files not cleaned up after TTL

**Symptoms:** Old job files still present after TTL expires

**Solution:**

1. **Check GC thread is running:**
   ```python
   # In worker.py, verify _gc_loop is active
   ```

2. **Restart backend:**
   ```bash
   pkill -f uvicorn
   python -m uvicorn app.main:app --app-dir backend --reload
   ```

3. **Manual cleanup:**
   ```bash
   find data/ -type d -mtime +2 -exec rm -rf {} \;
   ```

---

## Performance Issues

### Backend slow to respond

**Symptoms:** API calls take 5+ seconds

**Solution:**

1. **Check CPU/memory:**
   ```bash
   top  # Linux/macOS
   tasklist  # Windows
   ```

2. **Check disk I/O:**
   ```bash
   iostat  # Linux
   ```

3. **Reduce job queue size:**
   ```python
   # In worker.py, limit concurrent jobs
   ```

4. **Use external queue:**
   - Replace in-memory queue with Redis/RabbitMQ

---

### High memory usage

**Symptoms:** Process uses 1+ GB RAM

**Solution:**

1. **Check job count:**
   ```bash
   curl http://localhost:8080/status/<JOB_ID>
   # Count active jobs
   ```

2. **Reduce TTL to clean up faster:**
   ```bash
   APP_JOB_TTL_MINUTES=30
   ```

3. **Limit concurrent jobs:**
   ```python
   # In worker.py
   MAX_CONCURRENT = 10
   ```

4. **Use database instead of memory:**
   - Replace `job_queue.jobs` dict with SQLite

---

## Network Issues

### Can't reach backend from frontend

**Error:** `Connection refused` or `ECONNREFUSED`

**Solution:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8080/health
   ```

2. **Check firewall:**
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="Excel Runner" dir=in action=allow protocol=tcp localport=8080
   ```

3. **Check network:**
   ```bash
   ping localhost
   netstat -ano | findstr :8080
   ```

---

### Slow uploads

**Symptoms:** Upload takes minutes for small files

**Solution:**

1. **Check network:**
   ```bash
   speedtest-cli
   ```

2. **Check backend load:**
   ```bash
   top
   ```

3. **Increase chunk size (if implemented):**
   - Currently uploads entire file at once

4. **Use CDN for frontend:**
   - Reduce latency for static assets

---

## Security Issues

### Unauthorized access

**Error:** Need to add authentication

**Solution:**

See **CUSTOMIZATION.md** for adding bearer token authentication.

---

### Path traversal vulnerability

**Error:** Can access files outside job directory

**Solution:**

Already protected in `storage.py`:
```python
if not str(target).startswith(str(job.workdir.resolve())):
    raise HTTPException(400, "path non valido")
```

---

## Getting Help

1. **Check logs:**
   ```bash
   curl http://localhost:8080/logs/<JOB_ID>
   docker compose logs -f app
   ```

2. **Check documentation:**
   - README.md - Full overview
   - QUICK_START.md - Setup guide
   - PROJECT_STRUCTURE.md - Architecture
   - CUSTOMIZATION.md - Integration
   - DEPLOYMENT.md - Production

3. **Test manually:**
   ```bash
   curl http://localhost:8080/health
   curl -F "files=@test.xlsx" http://localhost:8080/upload
   ```

4. **Check browser console:**
   - Open DevTools (F12)
   - Check Console and Network tabs

---

## Still Stuck?

1. **Verify all prerequisites:**
   - Python 3.11+
   - Node 18+
   - Port 8080 available

2. **Start fresh:**
   ```bash
   # Clean up
   rm -rf .venv data/ frontend/node_modules frontend/dist
   
   # Reinstall
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   cd frontend && npm install && npm run build
   ```

3. **Run test:**
   ```bash
   python test_e2e.py
   ```

4. **Check all files exist:**
   ```bash
   ls -la backend/app/
   ls -la frontend/src/
   ```

---

**Last Resort:** Delete everything and start over from the repository.
