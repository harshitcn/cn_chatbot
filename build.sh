#!/bin/bash
# Build script for Azure App Service
# This ensures dependencies are installed during deployment

echo "Building application..."
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "Build complete!"

