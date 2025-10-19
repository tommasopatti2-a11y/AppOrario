# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- Node 18+

### Setup
```bash
# Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
npm run build
```

### Run
```bash
# Terminal 1: Backend
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Frontend dev server (optional, for hot reload)
cd frontend && npm run dev
```

Access:
- Backend API: `http://localhost:8080`
- Frontend (if dev server): `http://localhost:5173`
- Frontend (if served by backend): `http://localhost:8080`

---

## Docker (Recommended)

### Build
```bash
docker compose build
```

### Run
```bash
docker compose up
```

Access: `http://localhost:8080`

### Configuration
Edit `.env` or `docker-compose.yml`:
```yaml
environment:
  - APP_PROGRAM_ENTRYPOINT=runner.py:main
  - APP_MAX_FILE_SIZE_MB=100
  - APP_JOB_TTL_MINUTES=240
```

### Volumes
- `data:/data` - Persistent storage for uploads and results
- `./runner.py:/app/runner.py:ro` - Mount your entrypoint

### Stop
```bash
docker compose down
```

### Logs
```bash
docker compose logs -f app
```

---

## Production Deployment

### 1. Build Frontend
```bash
cd frontend
npm install
npm run build
# Output: frontend/dist/
```

### 2. Prepare Backend
```bash
# Create production requirements (no dev deps)
pip install -r backend/requirements.txt

# Or use a production server:
pip install gunicorn
```

### 3. Environment
Create `.env` with production values:
```
APP_PROGRAM_ENTRYPOINT=/app/runner.py:main
APP_MAX_FILE_SIZE_MB=100
APP_JOB_TTL_MINUTES=240
APP_OUTPUT_DIR_BASE=/data
APP_FRONTEND_DIST_DIR=/app/frontend_dist
APP_HOST=0.0.0.0
APP_PORT=8080
```

### 4. Run Backend
```bash
# Option A: Uvicorn (single worker)
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8080

# Option B: Gunicorn (multi-worker)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --app-dir backend --bind 0.0.0.0:8080
```

### 5. Reverse Proxy (nginx)
```nginx
upstream backend {
    server localhost:8080;
}

server {
    listen 80;
    server_name example.com;

    # Compression
    gzip on;
    gzip_types text/plain application/json application/javascript;

    # Frontend static files (cached)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://backend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /upload {
        proxy_pass http://backend;
        client_max_body_size 100M;
    }

    location /run {
        proxy_pass http://backend;
    }

    location /status {
        proxy_pass http://backend;
    }

    location /logs {
        proxy_pass http://backend;
    }

    location /results {
        proxy_pass http://backend;
    }

    location /download {
        proxy_pass http://backend;
    }

    location /health {
        proxy_pass http://backend;
    }

    # Fallback to frontend (SPA)
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. SSL/TLS (Let's Encrypt)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d example.com

# Update nginx config
listen 443 ssl http2;
ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Kubernetes Deployment

### Docker Image
```bash
docker build -t myregistry/excel-runner:latest .
docker push myregistry/excel-runner:latest
```

### Deployment YAML
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: excel-runner
spec:
  replicas: 2
  selector:
    matchLabels:
      app: excel-runner
  template:
    metadata:
      labels:
        app: excel-runner
    spec:
      containers:
      - name: app
        image: myregistry/excel-runner:latest
        ports:
        - containerPort: 8080
        env:
        - name: APP_PROGRAM_ENTRYPOINT
          value: runner.py:main
        - name: APP_MAX_FILE_SIZE_MB
          value: "100"
        - name: APP_OUTPUT_DIR_BASE
          value: /data
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: excel-runner-data
---
apiVersion: v1
kind: Service
metadata:
  name: excel-runner
spec:
  selector:
    app: excel-runner
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: excel-runner-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Deploy
```bash
kubectl apply -f deployment.yaml
kubectl get svc excel-runner
```

---

## Systemd Service (Linux)

### Create service file
```bash
sudo nano /etc/systemd/system/excel-runner.service
```

```ini
[Unit]
Description=Excel Runner API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/excel-runner
Environment="APP_PROGRAM_ENTRYPOINT=runner.py:main"
Environment="APP_OUTPUT_DIR_BASE=/var/lib/excel-runner/data"
ExecStart=/opt/excel-runner/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and start
```bash
sudo systemctl daemon-reload
sudo systemctl enable excel-runner
sudo systemctl start excel-runner
sudo systemctl status excel-runner
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:8080/health
# {"status":"ok","version":"0.1.0"}
```

### Logs
```bash
# Docker
docker compose logs -f app

# Systemd
sudo journalctl -u excel-runner -f

# File
tail -f /var/log/excel-runner/app.log
```

### Metrics (optional)
Add Prometheus metrics:
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

upload_counter = Counter('uploads_total', 'Total uploads')
job_duration = Histogram('job_duration_seconds', 'Job execution time')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Backup & Recovery

### Backup Data
```bash
# Docker volume
docker run --rm -v excel-runner_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/data-backup.tar.gz -C /data .

# Or direct filesystem
tar czf data-backup.tar.gz /var/lib/excel-runner/data
```

### Restore Data
```bash
# Docker volume
docker run --rm -v excel-runner_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/data-backup.tar.gz -C /data

# Or direct filesystem
tar xzf data-backup.tar.gz -C /
```

---

## Scaling

### Horizontal Scaling
- Run multiple backend instances behind a load balancer
- Use external job queue (Redis, RabbitMQ) instead of in-memory
- Use shared storage (NFS, S3) for `data/` directory

### Vertical Scaling
- Increase `MAX_FILE_SIZE_MB` for larger uploads
- Increase `JOB_TTL_MINUTES` to keep jobs longer
- Increase worker threads in `worker.py`

### Performance Tuning
- Adjust polling interval in `App.tsx` (currently 2.5s)
- Enable gzip compression in nginx
- Cache static assets (frontend build)
- Use CDN for frontend distribution

---

## Troubleshooting

### Port already in use
```bash
# Find process
lsof -i :8080
# Kill it
kill -9 <PID>
```

### Out of disk space
```bash
# Check usage
df -h /data

# Clean old jobs manually
rm -rf /data/sessions/*/jobs/*
```

### High memory usage
- Reduce `JOB_TTL_MINUTES` to clean up faster
- Implement job result archiving (move to S3)
- Use external queue with persistence

### Slow uploads
- Increase `client_max_body_size` in nginx
- Check network bandwidth
- Consider chunked upload (not implemented)

---

## Security Checklist

- [ ] HTTPS/SSL enabled
- [ ] Firewall rules restrict access
- [ ] Environment variables not in version control
- [ ] Regular backups tested
- [ ] Log rotation configured
- [ ] Rate limiting enabled (nginx)
- [ ] CORS origins restricted (if needed)
- [ ] Input validation enabled (schema validation)
- [ ] Secrets stored securely (not in `.env`)
- [ ] Regular security updates applied
