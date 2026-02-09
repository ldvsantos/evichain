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
#!/bin/bash
set -exuo pipefail

echo "===== [DEPLOY] Iniciando deploy ====="
echo "[DEPLOY] PWD: $(pwd)"
echo "[DEPLOY] SERVICE_NAME=${SERVICE_NAME:-evichain}"
echo "[DEPLOY] REMOTE_DIR=${REMOTE_DIR:-/opt/evichain}"

cd "${REMOTE_DIR:-.}"

echo "[PIP] Atualizando pip e ferramentas..."
python3 -m pip install -U pip setuptools wheel

echo "[PIP] Instalando requirements.txt..."
pip install -r requirements.txt

echo "[PIP] Garantindo gunicorn..."
pip install gunicorn

echo "[FILES] Conteúdo do diretório:"
ls -la

echo "[PYTHON] Testando importação do api_server..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
try:
    import api_server
    print("[IMPORT] ✓ api_server importado com sucesso")
    print(f"[IMPORT] ✓ Flask app: {api_server.app}")
except Exception as e:
    print(f"[ERROR] ✗ Falha ao importar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo "[SERVICE] Reiniciando ${SERVICE_NAME:-evichain}..."
sudo systemctl restart "${SERVICE_NAME:-evichain}"

echo "[SERVICE] Aguardando 3 segundos para ativar..."
sleep 3

echo "[SERVICE] Status:"
sudo systemctl status "${SERVICE_NAME:-evichain}" --no-pager

echo "[SERVICE] Logs recentes:"
sudo journalctl -u "${SERVICE_NAME:-evichain}" -n 20 --no-pager || true

echo "[HEALTHCHECK] Aguardando 2 segundos antes de verificar..."
sleep 2

echo "[HEALTHCHECK] Tentando conectar em http://127.0.0.1/api/health..."
for i in {1..20}; do
  echo "[HEALTHCHECK] Tentativa $i/20..."
  if curl -f --max-time 2 http://127.0.0.1/api/health; then
    echo "[SUCCESS] ✓ Healthcheck passou!"
    exit 0
  fi
  sleep 1
done

echo "[ERROR] ✗ Healthcheck falhou após 20 tentativas"
echo "[DEBUG] Tentando curl com verbose:"
curl -v http://127.0.0.1/api/health || true
echo "[DEBUG] Logs completos do serviço:"
sudo journalctl -u "${SERVICE_NAME:-evichain}" -n 100 --no-pager || true
exit 1
