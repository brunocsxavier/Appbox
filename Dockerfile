# Core Box — imagem de produção (versão v1 entregue pelo time)
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends iputils-ping curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip "setuptools>=84.2.1" && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y setuptools

COPY . .

ENV BOX_AMBIENTE=producao
EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "wsgi:app"]
