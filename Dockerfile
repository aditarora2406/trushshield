# TrustShield Dockerfile (Demo-ready for Hugging Face Spaces / Cloud Deployments)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run train.py to ensure fresh baseline models if not bundled
RUN python train.py

# Expose standard port
EXPOSE 7860

# Launch FastAPI app (HF Spaces uses port 7860 by default)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
