# FluxSentinel

AI-powered distributed threat detection and autonomous self-healing network system.

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
