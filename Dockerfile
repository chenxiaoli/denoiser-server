FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the denoiser module from parent directory
COPY ../denoiser ./denoiser

# Copy the server code
COPY server/ ./server/

# Set environment variables
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=""

# Expose port
EXPOSE 8000

# Change to server directory and run the application
WORKDIR /app/server
CMD ["python", "main.py"] 