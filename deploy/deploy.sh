#!/usr/bin/env bash
# Deploy do Core Box na VPS (executado NA EC2, via SSH, pela etapa 8 da esteira).
# Uso: IMAGEM=ghcr.io/<owner>/<repo>:<tag> [GHCR_USER=.. GHCR_TOKEN=..] ./deploy.sh
set -euo pipefail

: "${IMAGEM:?informe IMAGEM=ghcr.io/<owner>/<repo>:<tag>}"
DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "${GHCR_USER:?}" --password-stdin
fi

echo ">> Baixando $IMAGEM"
IMAGEM="$IMAGEM" docker compose -f "$DIR/docker-compose.prod.yml" pull
echo ">> Subindo nova versão"
IMAGEM="$IMAGEM" docker compose -f "$DIR/docker-compose.prod.yml" up -d --remove-orphans

echo ">> Verificando saúde"
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1/health >/dev/null; then
    echo ">> Core Box no ar: $IMAGEM"
    docker image prune -f >/dev/null
    exit 0
  fi
  sleep 2
done
echo "!! Health check falhou — verifique 'docker compose logs'" >&2
exit 1
