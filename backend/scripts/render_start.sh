#!/usr/bin/env bash
set -euo pipefail

echo "[render_start] Running database migrations..."
flask --app run.py db upgrade

echo "[render_start] Starting application..."
python run.py
