# Core Box - imagem de producao
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOX_AMBIENTE=producao

WORKDIR /app

# Instala primeiro as dependencias para aproveitar o cache do Docker.
COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --requirement requirements.txt

# Copia somente o necessario para executar a aplicacao.
COPY app/ ./app/
COPY config/ ./config/
COPY wsgi.py ./

# Usuario sem privilegios para executar a aplicacao.
RUN groupadd --system app \
    && useradd \
        --system \
        --gid app \
        --home-dir /app \
        --no-create-home \
        app \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "wsgi:app"]
