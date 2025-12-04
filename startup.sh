#!/bin/bash

# Azure App Service startup script
# This script is used by Azure App Service to start the FastAPI application

# Set environment variables for memory optimization
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export TRANSFORMERS_NO_ADVISORY_WARNINGS=1
export PYTHONUNBUFFERED=1

# Get the port from Azure App Service environment variable
# Azure App Service sets PORT automatically
PORT="${PORT:-8000}"

# Start the application
# Using uvicorn with single worker for F1 free tier (1GB memory)
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --timeout-keep-alive 75 \
    --limit-max-requests 1000

