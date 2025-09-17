# Dockerfile for Anchor Insight AI
# Multi-stage build for optimized production image

# Build stage
FROM python:3.12-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Set working directory
WORKDIR /app

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install Python dependencies (skip pyautogui and its macOS dependencies)
RUN pipenv install --system --skip-lock || pip install fastapi uvicorn[standard] openai python-dotenv pydantic-settings httpx Pillow opencv-python numpy ultralytics python-multipart

# Production stage
FROM python:3.12-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY .env.template ./

# Create .env from template if it doesn't exist
RUN if [ ! -f .env ]; then cp .env.template .env; fi

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash anchor && \
    chown -R anchor:anchor /app

USER anchor

# Expose the port the app runs on
EXPOSE 7003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7003/health')" || exit 1

# Run the application
CMD ["python", "-m", "src.main_refactored"]
