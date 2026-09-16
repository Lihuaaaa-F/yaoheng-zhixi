#!/usr/bin/env bash
# Resolve the single project interpreter. Every entry point (bootstrap, start,
# stop, verify, probes, scenario generation) must use this same order:
# PHARMA_PYTHON → project venv (either layout) → system python.
app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "${PHARMA_PYTHON:-}" ]; then
  echo "$PHARMA_PYTHON"
elif [ -x "$app_dir/.venv/bin/python" ]; then
  echo "$app_dir/.venv/bin/python"
elif [ -x "$app_dir/.venv/Scripts/python.exe" ]; then
  echo "$app_dir/.venv/Scripts/python.exe"
else
  echo python
fi
