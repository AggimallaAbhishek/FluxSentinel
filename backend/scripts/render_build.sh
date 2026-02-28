#!/usr/bin/env bash
set -euo pipefail

echo "[render_build] PIP_REQUIRE_HASHES(before)=${PIP_REQUIRE_HASHES-<unset>}"

# Some hosted environments may set strict hash mode; disable it explicitly for this project.
export PIP_REQUIRE_HASHES=0
export PIP_NO_CACHE_DIR=1

echo "[render_build] Python: $(python --version)"
python -m pip install --upgrade pip
pip install -r requirements.txt
