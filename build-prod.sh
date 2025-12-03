#!/bin/bash

# Production build script for Render deployment
# This script builds the Docker image with production settings

set -e  # Exit on any error

echo "🚀 Starting production build for Render..."

# Set production environment
export APP_ENV=production
export DOCKER_BUILDKIT=1

# Build Docker image with production settings
echo "📦 Building Docker image with APP_ENV=production..."
docker build \
  --build-arg APP_ENV=production \
  --tag cn-chatbot:production \
  --tag cn-chatbot:latest \
  -f Dockerfile \
  .

echo "✅ Production build completed successfully!"
echo "📋 Image tags: cn-chatbot:production, cn-chatbot:latest"

# Optional: Run basic validation
echo "🔍 Running basic validation..."
if [ -f "requirements.txt" ]; then
  echo "✓ requirements.txt found"
else
  echo "✗ requirements.txt not found"
  exit 1
fi

if [ -d "app" ]; then
  echo "✓ app directory found"
else
  echo "✗ app directory not found"
  exit 1
fi

if [ -f "Dockerfile" ]; then
  echo "✓ Dockerfile found"
else
  echo "✗ Dockerfile not found"
  exit 1
fi

echo "✅ All validations passed!"

