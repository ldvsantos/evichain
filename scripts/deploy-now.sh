#!/bin/bash
set -ex
cd /opt/evichain
git fetch --prune
git reset --hard origin/main
source .venv/bin/activate
python -c "import sys; sys.path.insert(0,'.'); import api_server; print('OK')"
sudo systemctl restart evichain
sleep 3
curl -sf http://127.0.0.1/api/health && echo ' HEALTH_OK'
echo '---TITLE---'
curl -s http://127.0.0.1/ | grep '<title>'
echo '---LANDING_CSS---'
curl -sI http://127.0.0.1/landing.css | head -3
