FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Manim, Pycairo, and FFmpeg
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgl1-mesa-dri \
    libglib2.0-0 \
    # Manim's text rendering dependencies
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    # FFmpeg for video stitching
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start FastAPI (use CMD instead of RUN for container startup)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]