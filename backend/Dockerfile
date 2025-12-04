FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR (otimizado: tudo em uma camada)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip antes de instalar dependências
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements from backend directory (camada separada para cache)
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies (com timeout maior e retry)
# Usando --no-cache-dir para reduzir tamanho da imagem
RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries=10 \
    -r requirements.txt

# Copy application code from backend directory (última camada)
COPY backend/ ./

# Expose port (Railway usa variável PORT, mas mantemos 8000 como padrão)
EXPOSE ${PORT:-8000}

# Default command (Railway injeta PORT automaticamente via variável de ambiente)
# Se PORT não estiver definida, usa 8000 como padrão
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"

