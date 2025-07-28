# Use official Python image
FROM --platform=linux/amd64 python:3.9-slim-bullseye

# Install system dependencies (required for PyMuPDF) and upgrade packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set the entry point
ENTRYPOINT ["python", "extract_outline.py"]
