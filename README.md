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
- Start command: `bash ./scripts/render_start.sh`
- Health check path: `/api/health`

For existing Render services (non-blueprint), set these in Render Dashboard -> Service -> Settings -> Build & Deploy:
- Root Directory: `backend`
- Build Command: `bash ./scripts/render_build.sh`
- Start Command: `bash ./scripts/render_start.sh`

After deploy, verify deep health:
- `GET /api/health/deep` (checks DB + Redis)

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

If your stage view still shows old stages (for example `docker buildx ...`), the job is still using an old inline script. Switch to `Pipeline script from SCM`.

### Jenkins-in-Docker Setup (Fix for `docker: not found`)
Use this when Jenkins itself is running as a Docker container on your laptop.

1. From repo root: `cd infra/jenkins`
2. Start Jenkins with Docker CLI installed:
   - `docker compose up -d --build`
3. Open Jenkins: `http://localhost:8080`
4. In Jenkins, run this to verify Docker is available:
   - `docker version`

This setup mounts host Docker socket (`/var/run/docker.sock`) and includes Docker CLI in Jenkins container, so pipeline `docker build/push` commands work.

### First Pipeline Run
- Run once with `TRIGGER_RENDER_DEPLOY=false`
- After Docker push is confirmed, run again with `TRIGGER_RENDER_DEPLOY=true`
