# FluxSentinel

AI-powered distributed threat detection & autonomous self-healing network system.

## Structure
- `backend/`: Flask API, ML inference, mitigation engine, Redis integration, Docker setup.
- `frontend/`: React + Tailwind real-time monitoring dashboard.

## Quick Start
1. Backend
   - `cd backend`
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `python run.py`
2. Frontend
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## Render Deployment Notes

If Render build fails with hash mismatch errors from pip, use the repository build script:

- Root directory: `backend`
- Build command: `./scripts/render_build.sh`
- Start command: `python run.py`
- Health check path: `/api/health`

This script explicitly sets:
- `PIP_REQUIRE_HASHES=0`
- `PIP_NO_CACHE_DIR=1`

Required Render environment variables:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `MODEL_PATH=app/ml/model.pkl`
- `CORS_ALLOWED_ORIGINS`
- `PYTHON_VERSION=3.13.7`

## Jenkins + Docker CI/CD

### Jenkins Pipeline
- Pipeline file: `Jenkinsfile` (repo root)
- Builds backend Docker image from `./backend`
- Runs backend tests in container
- Pushes image to Docker Hub
- Optionally triggers Render deploy hook

### Jenkins Credentials
Create these credentials in Jenkins:
- `dockerhub-creds` (Username with password): Docker Hub username/password
- `render-deploy-hook` (Secret text): Render deploy hook URL

### Jenkins Job Setup
1. New item -> Pipeline
2. Pipeline script from SCM
3. SCM: Git, Repository: your GitHub repo
4. Branch: `main`
5. Script Path: `Jenkinsfile`

### Docker Access Fix for Jenkins Host
If Jenkins cannot talk to Docker daemon, run on Jenkins host:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart docker
sudo systemctl restart jenkins
```

If using macOS agent, ensure Docker Desktop is running and Jenkins user/session has Docker CLI access.

### First Pipeline Run
- Run once with `TRIGGER_RENDER_DEPLOY=false`
- After Docker push is confirmed, run again with `TRIGGER_RENDER_DEPLOY=true`
