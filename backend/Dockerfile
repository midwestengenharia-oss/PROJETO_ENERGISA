# Usa a imagem oficial do Playwright com Python
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Define diretorio de trabalho
WORKDIR /app

# Instala dependencias do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala o navegador Chromium para Playwright
RUN playwright install chromium

# Copia o codigo para /app/backend (mantem estrutura de imports)
COPY . ./backend/

# Copia .env da raiz se existir (sera montado via volume ou env do docker-compose)
# O arquivo .env deve estar na raiz do projeto

# Cria pasta de sessoes do Playwright
RUN mkdir -p /app/backend/sessions

# Variaveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expoe a porta 8000
EXPOSE 8000

# Comando de inicializacao com Xvfb (monitor virtual)
CMD xvfb-run --auto-servernum --server-args="-screen 0 1280x1024x24" \
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
