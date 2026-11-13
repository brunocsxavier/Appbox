# ============================================================
# Stage 1 - Builder
# ============================================================

FROM python:3.12-slim AS builder

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/python -m pip install \
        --no-cache-dir \
        --requirement requirements.txt

RUN /opt/venv/bin/python -m pip uninstall -y \
        pip \
        setuptools \
        wheel

# ============================================================
# Stage 2 - Runtime
# ============================================================

FROM python:3.12-slim

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOX_AMBIENTE=producao
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copia somente o virtualenv pronto.
COPY --from=builder /opt/venv /opt/venv

# Copia somente a aplicacao necessaria.
COPY app/ ./app/
COPY config/ ./config/
COPY wsgi.py ./

# Remove ferramentas de packaging globais do runtime.
RUN rm -rf \
    /usr/local/lib/python3.12/site-packages/pip \
    /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
    /usr/local/lib/python3.12/site-packages/setuptools \
    /usr/local/lib/python3.12/site-packages/setuptools-*.dist-info \
    /usr/local/lib/python3.12/site-packages/wheel \
    /usr/local/lib/python3.12/site-packages/wheel-*.dist-info



# Usuario nao-root.
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
