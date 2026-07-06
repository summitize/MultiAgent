#!/bin/bash
# Startup script for Azure App Service
python -m gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app:app
