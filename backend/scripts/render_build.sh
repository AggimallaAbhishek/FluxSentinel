#!/usr/bin/env bash
set -euo pipefail

# Ignore any inherited pip config that may enforce hash-locked installs.
export PIP_CONFIG_FILE=/dev/null
export PIP_REQUIRE_HASHES=0
export PIP_NO_CACHE_DIR=1
unset PIP_CONSTRAINT || true
unset PIP_CONSTRAINTS || true

echo "[render_build] Python: $(python --version)"
echo "[render_build] PIP_CONFIG_FILE=${PIP_CONFIG_FILE}"
echo "[render_build] PIP_REQUIRE_HASHES=${PIP_REQUIRE_HASHES}"

python -m pip --isolated install --upgrade pip
python -m pip --isolated install -r requirements.txt
