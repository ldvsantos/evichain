#!/usr/bin/env bash
set -euo pipefail

# Script de deploy (rodar a cada atualização)
# - git pull
# - pip install -r
# - restart service

REMOTE_DIR="${REMOTE_DIR:-/opt/evichain}"
SERVICE_NAME="${SERVICE_NAME:-evichain}"
BRANCH="${BRANCH:-main}"

cd "$REMOTE_DIR"

git fetch --prune

git checkout "$BRANCH"

# Força atualização descartando mudanças locais
git reset --hard origin/"$BRANCH"

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
# Garante que o pip está atualizado
python3 -m pip install -U pip setuptools wheel
pip install -r requirements.txt

# Força instalação do gunicorn se não estiver no requirements (embora devasse estar)
pip install gunicorn

echo "=== Verificando arquivos ==="
ls -la

echo "=== Reiniciando serviço ==="
sudo systemctl restart "$SERVICE_NAME"

echo "=== Aguardando serviço subir (Healthcheck) ==="
# healthcheck local
for i in $(seq 1 30); do
  # Tenta curl e captura output para debug se falhar
  if curl -v --max-time 2 "http://127.0.0.1/api/health" > /tmp/healthcheck.log 2>&1; then
    echo "DEPLOY_OK: Healthcheck passou!"
    exit 0
  fi
  echo "Tentativa $i falhou. Aguardando..."
  sleep 1
done

echo "HEALTHCHECK_FAILED" >&2
echo "=== Último erro do curl ==="
cat /tmp/healthcheck.log || true
echo "=== Logs do serviço (últimas 100 linhas) ==="
sudo journalctl -u "$SERVICE_NAME" -n 100 --no-pager
exit 1
