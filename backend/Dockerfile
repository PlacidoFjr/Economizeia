FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend directory
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
# Aumentar timeout e usar retry para problemas de rede
RUN pip install --no-cache-dir --default-timeout=100 --retries=5 -r requirements.txt

# Copy application code from backend directory
COPY backend/ ./

# Expose port (Railway usa variável PORT, mas mantemos 8000 como padrão)
EXPOSE ${PORT:-8000}

# Default command (Railway injeta PORT automaticamente via variável de ambiente)
# Se PORT não estiver definida, usa 8000 como padrão
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"

