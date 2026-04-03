#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-colleague-company}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

conda env remove -n "${ENV_NAME}" -y >/dev/null 2>&1 || true
conda env create -n "${ENV_NAME}" -f "${ROOT_DIR}/environment.yml"
conda run -n "${ENV_NAME}" pip install -e "${ROOT_DIR}[dev]"

echo "Conda environment ready: ${ENV_NAME}"
echo "Activate with: conda activate ${ENV_NAME}"
