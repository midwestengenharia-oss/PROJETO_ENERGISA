# Usa imagem Python oficial
FROM python:3.11-slim

# Define diretorio de trabalho
WORKDIR /app

# Instala dependencias do sistema para PDF e OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo para /app/backend (mantem estrutura de imports)
COPY . ./backend/

# Variaveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expoe a porta 8000
EXPOSE 8000

# Comando de inicializacao
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
