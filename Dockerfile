# Dockerfile - Container untuk Atrric
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port for API
EXPOSE 8000

# Default command
CMD ["python", "api.py"]