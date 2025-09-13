#!/bin/bash
cd ~/sophia-intel-ai
source .venv/bin/activate
export PYTHONPATH=$PWD
echo 'Starting API on port 8003...'
python -m uvicorn app.api.unified_server:app --host 0.0.0.0 --port 8003 --log-level debug
