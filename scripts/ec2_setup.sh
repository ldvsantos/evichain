#!/usr/bin/env bash
set -euo pipefail

# Script de setup (executar 1 vez na EC2)
# - Instala deps
# - Clona repo
# - Cria venv
# - Cria systemd service + nginx

APP_USER="${APP_USER:-ubuntu}"
REMOTE_DIR="${REMOTE_DIR:-/opt/evichain}"
REPO_URL="${REPO_URL:-}"
SERVICE_NAME="${SERVICE_NAME:-evichain}"
APP_PORT="${APP_PORT:-8000}"

if [[ -z "$REPO_URL" ]]; then
  echo "REPO_URL é obrigatório" >&2
  exit 1
fi

sudo apt update
sudo apt -y install python3-venv python3-pip nginx git

if [[ ! -d "$REMOTE_DIR/.git" ]]; then
  sudo mkdir -p "$REMOTE_DIR"
  sudo chown -R "$APP_USER:$APP_USER" "$REMOTE_DIR"
  git clone "$REPO_URL" "$REMOTE_DIR"
fi

cd "$REMOTE_DIR"

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# .env (se não existir)
if [[ ! -f "$REMOTE_DIR/.env" ]]; then
  cat > "$REMOTE_DIR/.env" <<EOF
FLASK_HOST=127.0.0.1
PORT=$APP_PORT
# OPENAI_API_KEY=
EOF
  chmod 600 "$REMOTE_DIR/.env" || true
fi

# systemd
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=EviChain API
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${REMOTE_DIR}
EnvironmentFile=${REMOTE_DIR}/.env
ExecStart=${REMOTE_DIR}/.venv/bin/gunicorn wsgi:app --bind 127.0.0.1:${APP_PORT} --workers 2 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"

# nginx
sudo tee "/etc/nginx/sites-available/${SERVICE_NAME}" > /dev/null <<EOF
server {
  listen 80;
  server_name _;

  location / {
    proxy_pass http://127.0.0.1:${APP_PORT};
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
EOF

sudo ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
sudo nginx -t
sudo systemctl restart nginx

echo "SETUP_OK"