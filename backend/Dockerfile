# Usa a imagem oficial do Playwright (inclui Python 3.11)
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Define diretorio de trabalho
WORKDIR /app

# Instala dependencias do sistema para PDF, OCR e Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libpoppler-cpp-dev \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instala dependencias Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala o navegador Chromium do Playwright
RUN playwright install chromium

# Copia o codigo para /app/backend (mantem estrutura de imports)
COPY . ./backend/

# Cria pasta de sessões
RUN mkdir -p /app/sessions

# Variaveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expoe a porta 8000
EXPOSE 8000

# Comando de inicializacao com Xvfb para suportar headless
CMD ["sh", "-c", "xvfb-run --auto-servernum --server-args='-screen 0 1280x1024x24' uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
