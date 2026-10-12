#!/usr/bin/env bash
# Prepara un clon de CIRCUIT-HACKS para trabajar en local: llama a tools/setup_dev.py, que descarga cada dependencia
# de su fuente original (docs/DEPENDENCIAS.md).  Opciones: las de setup_dev.py (--check, --no-dsptool, --official FICHERO).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
exec "$PY" "$ROOT/tools/setup_dev.py" "$@"
