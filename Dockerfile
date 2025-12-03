# Use Python 3.11 slim image
FROM python:3.11-slim

# Accept APP_ENV as build argument (default to stage)
ARG APP_ENV=stage

# Set APP_ENV as environment variable
ENV APP_ENV=$APP_ENV

# Set working directory
WORKDIR /app

# Install system dependencies for sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Note: .env files are not copied here for security reasons
# Environment variables should be set in Render's dashboard or via render.yaml
# The app will use environment variables directly (see app/config.py)

# Create cache and data directories for FAISS index
RUN mkdir -p .cache data

# Expose port 8000
EXPOSE 8000

# Run uvicorn server
# Use PORT environment variable if set (for cloud platforms like Render), otherwise use 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

