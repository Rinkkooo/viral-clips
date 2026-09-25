# Multi-stage production Dockerfile with NVIDIA CUDA & FFmpeg
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY samples/ ./samples/

EXPOSE 8000

CMD ["python3", "-m", "viral_clips.cli", "server", "--host", "0.0.0.0", "--port", "8000"]
