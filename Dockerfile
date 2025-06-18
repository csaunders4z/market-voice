# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better caching
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Create a non-root user
RUN useradd -m marketuser

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/output && \
    chown -R marketuser:marketuser /app

USER marketuser

# Expose output and logs directories (optional)
VOLUME ["/app/output", "/app/logs"]

# Default command
CMD ["python", "main.py"] 