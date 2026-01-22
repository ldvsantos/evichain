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
pip install -r requirements.txt

sudo systemctl restart "$SERVICE_NAME"

# healthcheck local (via nginx/app)
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1/api/health" >/dev/null 2>&1; then
    echo "DEPLOY_OK"
    exit 0
  fi
  sleep 1
done

echo "HEALTHCHECK_FAILED" >&2
echo "=== Service Status ==="
sudo systemctl status "$SERVICE_NAME" --no-pager || true
echo "=== Service Logs ==="
sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager || true
exit 1
