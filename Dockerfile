# Core Box — imagem de produção (versão v1 entregue pelo time)
FROM python:3.11.4-slim-bookworm

ADD . /app
WORKDIR /app

RUN apt-get update && apt-get install -y iputils-ping curl
RUN pip install -r requirements.txt

ENV BOX_AMBIENTE=producao
EXPOSE 8000

CMD gunicorn -b 0.0.0.0:8000 --workers 1 --threads 4 wsgi:app
