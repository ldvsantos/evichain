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
set -euo pipefail

echo "[DEPLOY] Atualizando pip, setuptools e wheel..."
python3 -m pip install -U pip setuptools wheel 2>&1 | tail -10

echo "[DEPLOY] Instalando requirements.txt..."
pip install -r requirements.txt 2>&1 | tail -20

echo "[DEPLOY] Garantindo gunicorn instalado..."
pip install gunicorn 2>&1 | tail -5

echo "[DEPLOY] Verificando arquivos no diretório atual:"
pwd
ls -la | head -20

echo "[DEPLOY] Testando importação do api_server.py..."
python3 -c "import sys; sys.path.insert(0, '.'); import api_server; print('[IMPORT_OK] api_server carregado com sucesso')" 2>&1 || (echo "[ERROR] Falha ao importar api_server"; exit 1)

echo "[DEPLOY] Reiniciando serviço ${SERVICE_NAME}..."
sudo systemctl restart "$SERVICE_NAME"

echo "[DEPLOY] Aguardando 3 segundos para serviço ativar..."
sleep 3

echo "[DEPLOY] Verificando status do serviço:"
sudo systemctl status "$SERVICE_NAME" --no-pager || true

echo "[DEPLOY] Script finalizado com sucesso. Saindo com exit 0."
exit 0
