# Excel Runner - Documentation Index

**Welcome!** This is your guide to the Excel Runner application. Start here to find what you need.

---

## 🚀 I Want To...

### Get Started Quickly
→ **[QUICK_START.md](QUICK_START.md)** (5 minutes)
- Windows setup with PowerShell
- Docker setup
- First test run
- Troubleshooting quick fixes

### Understand the Architecture
→ **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**
- File organization
- Backend components
- Frontend components
- Data flow
- API endpoints
- Security model

### Integrate My Python Program
→ **[CUSTOMIZATION.md](CUSTOMIZATION.md)**
- Prepare your entrypoint
- Configure environment
- Add custom parameters
- Schema validation
- Database integration
- Authentication
- WebSocket support

### Deploy to Production
→ **[DEPLOYMENT.md](DEPLOYMENT.md)**
- Local development setup
- Docker deployment
- Kubernetes deployment
- nginx reverse proxy
- SSL/TLS configuration
- Systemd service
- Monitoring and logging
- Backup and recovery
- Scaling strategies

### Fix a Problem
→ **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
- Backend issues
- Frontend issues
- Docker issues
- Job execution issues
- Storage issues
- Performance issues
- Network issues
- Security issues

### See Full Documentation
→ **[README.md](README.md)**
- Complete feature list
- API contract
- Configuration reference
- Security checklist
- Testing procedures

### Check Project Status
→ **[CHECKLIST.md](CHECKLIST.md)**
- Feature completion status
- Pre-launch checklist
- Acceptance test cases
- Performance targets
- Security checklist
- Deployment checklist

### Get a Quick Overview
→ **[SUMMARY.md](SUMMARY.md)**
- What you have
- Quick start options
- Configuration
- API endpoints
- Workflow diagram
- Next steps

---

## 📚 Documentation Map

```
START HERE
    ↓
QUICK_START.md (5 min setup)
    ↓
    ├─→ Works? → SUMMARY.md (overview)
    │       ↓
    │       ├─→ Understand → PROJECT_STRUCTURE.md
    │       ├─→ Customize → CUSTOMIZATION.md
    │       └─→ Deploy → DEPLOYMENT.md
    │
    └─→ Problem? → TROUBLESHOOTING.md
            ↓
            └─→ Still stuck? → README.md (full docs)
```

---

## 🎯 Common Tasks

| Task | Document | Section |
|------|----------|---------|
| Install and run locally | QUICK_START.md | Option 1-3 |
| Run with Docker | QUICK_START.md | Option 2 |
| Configure environment | README.md | Variabili d'ambiente |
| Integrate Python program | CUSTOMIZATION.md | Integrating Your Python Program |
| Add custom parameters | CUSTOMIZATION.md | Add Custom Parameters |
| Enable schema validation | CUSTOMIZATION.md | Excel Schema Validation |
| Deploy to production | DEPLOYMENT.md | Production Deployment |
| Set up nginx | DEPLOYMENT.md | Reverse Proxy (nginx) |
| Deploy to Kubernetes | DEPLOYMENT.md | Kubernetes Deployment |
| Add authentication | CUSTOMIZATION.md | Add Authentication |
| Add database | CUSTOMIZATION.md | Add Database Persistence |
| Monitor performance | DEPLOYMENT.md | Monitoring |
| Backup data | DEPLOYMENT.md | Backup & Recovery |
| Fix backend issue | TROUBLESHOOTING.md | Backend Issues |
| Fix frontend issue | TROUBLESHOOTING.md | Frontend Issues |
| Fix Docker issue | TROUBLESHOOTING.md | Docker Issues |
| Understand API | README.md | Contratto API |
| Test application | README.md | Testing di accettazione |
| Check completion | CHECKLIST.md | Core Features Implemented |

---

## 📖 Reading Guide by Role

### 👨‍💻 Developer (Local Setup)
1. QUICK_START.md - Get running
2. PROJECT_STRUCTURE.md - Understand code
3. CUSTOMIZATION.md - Modify for your needs
4. TROUBLESHOOTING.md - Fix issues

### 🏗️ DevOps/SRE (Deployment)
1. DEPLOYMENT.md - Production setup
2. DEPLOYMENT.md → Kubernetes - Scale out
3. DEPLOYMENT.md → Monitoring - Observe
4. TROUBLESHOOTING.md - Troubleshoot

### 🔧 Integration Engineer (Custom Program)
1. QUICK_START.md - Get running
2. CUSTOMIZATION.md → Integrating Your Python Program
3. CUSTOMIZATION.md → Frontend Customization
4. README.md → Contratto API

### 📊 Project Manager (Overview)
1. SUMMARY.md - What we have
2. CHECKLIST.md - What's done
3. README.md - Features
4. PROJECT_STRUCTURE.md - Architecture

---

## 🔍 Find Information By Topic

### Setup & Installation
- **Local (Windows):** QUICK_START.md → Option 1
- **Local (Linux/macOS):** QUICK_START.md → Option 3
- **Docker:** QUICK_START.md → Option 2
- **Production:** DEPLOYMENT.md → Production Deployment

### Configuration
- **Environment variables:** README.md → Variabili d'ambiente
- **Schema validation:** CUSTOMIZATION.md → Excel Schema Validation
- **Custom parameters:** CUSTOMIZATION.md → Add Custom Parameters
- **Entrypoint:** CUSTOMIZATION.md → Integrating Your Python Program

### API Reference
- **All endpoints:** README.md → Contratto API
- **Examples:** README.md → Esempi curl
- **Status codes:** TROUBLESHOOTING.md → Job Execution Issues

### Customization
- **Python integration:** CUSTOMIZATION.md → Integrating Your Python Program
- **Frontend:** CUSTOMIZATION.md → Frontend Customization
- **Backend:** CUSTOMIZATION.md → Backend Customization
- **Docker:** CUSTOMIZATION.md → Docker Customization

### Deployment
- **Docker:** DEPLOYMENT.md → Docker (Recommended)
- **Kubernetes:** DEPLOYMENT.md → Kubernetes Deployment
- **nginx:** DEPLOYMENT.md → Reverse Proxy (nginx)
- **SSL/TLS:** DEPLOYMENT.md → SSL/TLS (Let's Encrypt)
- **Monitoring:** DEPLOYMENT.md → Monitoring

### Troubleshooting
- **Backend won't start:** TROUBLESHOOTING.md → Backend Issues
- **Frontend won't build:** TROUBLESHOOTING.md → Frontend Issues
- **Docker fails:** TROUBLESHOOTING.md → Docker Issues
- **Job fails:** TROUBLESHOOTING.md → Job Execution Issues
- **Disk full:** TROUBLESHOOTING.md → Storage & Cleanup Issues

### Performance & Scaling
- **Performance targets:** CHECKLIST.md → Performance Targets
- **Scaling:** DEPLOYMENT.md → Scaling
- **Tuning:** CUSTOMIZATION.md → Performance Tuning

### Security
- **Security features:** SUMMARY.md → Security Features
- **Security checklist:** CHECKLIST.md → Security Checklist
- **HTTPS setup:** DEPLOYMENT.md → SSL/TLS (Let's Encrypt)
- **Authentication:** CUSTOMIZATION.md → Add Authentication

---

## 📋 Quick Reference

### File Locations
```
AppOrario/
├── backend/app/main.py          # API endpoints
├── backend/app/adapter.py       # Entrypoint runner
├── frontend/src/App.tsx         # UI component
├── runner.py                    # Your program (customize)
├── Dockerfile                   # Docker build
├── docker-compose.yml           # Docker Compose
└── .env                         # Configuration (create from .env.example)
```

### Key Commands
```bash
# Backend
python -m uvicorn app.main:app --app-dir backend --reload

# Frontend
cd frontend && npm run dev

# Docker
docker compose up --build

# Test
python test_e2e.py

# Health check
curl http://localhost:8080/health
```

### Environment Variables
```
APP_PROGRAM_ENTRYPOINT=runner.py:main
APP_MAX_FILE_SIZE_MB=50
APP_ALLOWED_EXTENSIONS=.xlsx
APP_JOB_TTL_MINUTES=120
APP_OUTPUT_DIR_BASE=./data
```

### API Endpoints
```
POST   /upload                      # Upload files
POST   /run                         # Start job
GET    /status/{job_id}            # Check status
GET    /logs/{job_id}              # Get logs
GET    /results/{job_id}           # List outputs
GET    /download/{job_id}/{file}   # Download file
GET    /download/{job_id}/all.zip  # Download all
DELETE /jobs/{job_id}              # Delete job
GET    /health                     # Health check
```

---

## ❓ FAQ

**Q: Where do I start?**
A: Read QUICK_START.md (5 minutes), then run locally.

**Q: How do I add my Python program?**
A: See CUSTOMIZATION.md → Integrating Your Python Program

**Q: How do I deploy to production?**
A: See DEPLOYMENT.md → Production Deployment

**Q: How do I add authentication?**
A: See CUSTOMIZATION.md → Add Authentication

**Q: How do I scale to 1000s of jobs?**
A: See DEPLOYMENT.md → Scaling

**Q: Something's broken, help!**
A: See TROUBLESHOOTING.md for your issue

**Q: Is this production-ready?**
A: Yes! See CHECKLIST.md for completion status.

**Q: Can I customize the UI?**
A: Yes! See CUSTOMIZATION.md → Frontend Customization

**Q: Can I add a database?**
A: Yes! See CUSTOMIZATION.md → Add Database Persistence

**Q: Can I add WebSocket?**
A: Yes! See CUSTOMIZATION.md → Add WebSocket for Real-time Updates

---

## 🎓 Learning Path

### Beginner (Just want it to work)
1. QUICK_START.md
2. Run locally
3. Test with sample files
4. Done!

### Intermediate (Want to customize)
1. QUICK_START.md
2. CUSTOMIZATION.md → Integrating Your Python Program
3. Modify runner.py
4. Test
5. Deploy with Docker

### Advanced (Want to scale)
1. All of Intermediate
2. DEPLOYMENT.md → Production Deployment
3. DEPLOYMENT.md → Kubernetes Deployment
4. CUSTOMIZATION.md → Add Database Persistence
5. DEPLOYMENT.md → Monitoring

### Expert (Want to extend)
1. All of Advanced
2. PROJECT_STRUCTURE.md (understand architecture)
3. CUSTOMIZATION.md (all sections)
4. Add authentication, WebSocket, metrics, etc.

---

## 📞 Support Resources

| Resource | Purpose |
|----------|---------|
| QUICK_START.md | Get running in 5 minutes |
| README.md | Full feature documentation |
| PROJECT_STRUCTURE.md | Understand the code |
| CUSTOMIZATION.md | Extend and modify |
| DEPLOYMENT.md | Production setup |
| TROUBLESHOOTING.md | Fix problems |
| CHECKLIST.md | Verify completion |
| SUMMARY.md | Quick overview |

---

## ✅ Before You Start

- [ ] Python 3.11+ installed
- [ ] Node 18+ installed
- [ ] Port 8080 available
- [ ] Read QUICK_START.md
- [ ] Have your Python program ready

---

## 🎉 You're Ready!

Pick your starting point above and dive in. The application is complete and ready to use.

**Most common path:**
1. QUICK_START.md (5 min)
2. Run locally
3. CUSTOMIZATION.md (integrate your program)
4. DEPLOYMENT.md (deploy to production)

**Questions?** Check the relevant guide above.

---

**Happy coding! 🚀**

*Last updated: 2025-10-19*
