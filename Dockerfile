# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies, curl for healthcheck, and DejaVu fonts
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && apt-get install -y curl fonts-dejavu-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p templates static

# Copy static files and templates
COPY templates/ templates/
COPY static/ static/

# Expose port (matches app.py port)
EXPOSE 8090

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]