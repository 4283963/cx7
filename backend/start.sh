#!/bin/bash
cd /Users/kl/Documents/trae_projects2/cx7/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
