#!/usr/bin/env bash
# Install SATANA Web UI dependencies (PEP 668–safe virtualenv).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${ROOT}/.venv-web"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "Install venv support, then re-run:" >&2
  echo "  sudo apt install python3-venv python3-pip" >&2
  exit 1
fi

python3 -m venv "${VENV}"
# shellcheck source=/dev/null
source "${VENV}/bin/activate"
pip install --upgrade pip
pip install -r "${ROOT}/requirements-web.txt"

cat <<EOF

Done. Activate the venv and start the web UI:

  source "${VENV}/bin/activate"
  sudo -E ./satana-web

Or without activating (sudo keeps venv on PATH if you use -E):

  sudo "${VENV}/bin/python3" satana.py web

EOF
