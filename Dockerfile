# Use imagem Python 3.11 slim (menor tamanho)
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Variáveis de ambiente Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt e instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copia aplicação
COPY app/ ./app/
COPY banco_dados/ ./banco_dados/
COPY config.py .

# Cria diretórios necessários
RUN mkdir -p logs app/static/uploads

# Define usuário não-root (segurança)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expõe porta
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Comando para iniciar a aplicação com Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "sync", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.app:app"]
