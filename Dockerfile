# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Set working directory
WORKDIR /app

# Install system dependencies (needed for compiling certain python libs if wheels aren't used)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model into the image to avoid runtime OOM on low-memory hosts
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy source code and frontend
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Create folders for uploads and database mounts, set permissions for HF Spaces user
RUN mkdir -p data/uploads chroma_db && chmod -R 777 /app

# Expose port
EXPOSE 7860

# Run FastAPI app using Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
