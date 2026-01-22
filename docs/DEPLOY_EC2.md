# Deploy na EC2 (AWS)

Este projeto roda como:
- **gunicorn** (Flask) em `127.0.0.1:8000`
- **nginx** na porta `80` fazendo proxy reverso
- **systemd** com o serviço `evichain`

## 1) Primeira instalação na EC2

Pré-requisitos:
- EC2 Ubuntu 24.04
- Security Group com **porta 22** liberada para seu IP

Passos:
1. Gere uma deploy key na EC2 e cadastre no GitHub (Deploy keys, leitura).
2. Clone o repositório no servidor em `/opt/evichain`.
3. Rode o setup:

```bash
cd /opt/evichain
REPO_URL=git@github.com:ldvsantos/evichain_poc-.git \
REMOTE_DIR=/opt/evichain \
SERVICE_NAME=evichain \
APP_PORT=8000 \
APP_USER=ubuntu \
bash scripts/ec2_setup.sh
```

Após isso, valide:
- `systemctl status evichain --no-pager`
- `curl -fsS http://127.0.0.1/api/health`

## 2) Liberar acesso público

No Security Group da instância:
- Liberar **porta 80 (HTTP)** para `0.0.0.0/0` (e `::/0` se usar IPv6)

Teste:
- `http://<IP_PUBLICO>/`
- `http://<IP_PUBLICO>/api/health`

## 3) Atualizações (deploy incremental)

### Opção A: Windows (deploy.cmd)

- Copie `scripts/deploy-config.ps1.example` para `scripts/deploy-config.ps1` e ajuste.
- Rode `deploy.cmd`.

O script:
- faz `git pull/rebase` local + `git push`
- na EC2 faz `git pull` + `pip install -r requirements.txt` + restart + healthcheck

### Opção B: GitHub Actions

Use `.github/workflows/deploy-ec2.yml` e configure os secrets:
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_PRIVATE_KEY`
- `EC2_SSH_PORT` (opcional)
- `EC2_REMOTE_DIR` (opcional, default `/opt/evichain`)
- `EC2_SERVICE_NAME` (opcional, default `evichain`)
- `EC2_APP_PORT` (opcional, default `8000`)
- `EC2_APP_USER` (opcional, default = `EC2_USER`)
