#!/bin/bash
# Post-build script for Azure App Service
# This script runs after Oryx builds the app to ensure dependencies are installed

echo "Running post-build script..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Ensure pip is up to date
python -m pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "Dependencies installed successfully"
else
    echo "WARNING: requirements.txt not found!"
fi

# Verify uvicorn is installed
if python -c "import uvicorn" 2>/dev/null; then
    echo "✓ uvicorn is installed"
else
    echo "✗ uvicorn is NOT installed - installing now..."
    pip install uvicorn[standard]
fi

echo "Post-build script completed"

