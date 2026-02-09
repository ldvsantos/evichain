# GitHub Actions Build & Release

Este repositório está configurado com GitHub Actions para construir e fazer release automático de executáveis.

## ⚙️ Workflows Disponíveis

### 1. **Deploy to GitHub Pages** (`deploy.yml`)
- **Trigger**: Push na branch `main`
- **Ação**: Faz deploy automático da landing page para GitHub Pages
- **URL**: https://ldvsantos.github.io/evichain/
- **Status**: ✅ Ativo

### 2. **Build & Release Executável** (`build-release.yml`)
- **Trigger**: Criar uma nova **Release** no GitHub
- **Target OS**: Windows (pode ser expandido para macOS/Linux)
- **Output**: Executáveis `*.exe`, `*.msi`, `*.zip` anexados na release
- **Status**: ✅ Configurado

## 📦 Como Criar um Release com Executável

### Passo 1: Na branch `main`, faça um commit com a versão
```bash
git add .
git commit -m "v1.0.0: Release versão 1.0.0"
git push origin main
```

### Passo 2: Criar a Release no GitHub
1. Acesse https://github.com/ldvsantos/evichain/releases
2. Clique em **Draft a new release**
3. Preencha os campos:
   - **Tag version**: `v1.0.0` (siga [Semantic Versioning](https://semver.org/))
   - **Title**: `EviChain v1.0.0`
   - **Description**: Descreva as mudanças
4. Marque **This is a pre-release** se for beta
5. Clique em **Publish release**

### Passo 3: Acompanhe o Build
1. Vá para **Actions** no repositório
2. Procure por **Build & Release Executável**
3. Acompanhe o progresso em tempo real

### Passo 4: Download do Executável
Assim que o build terminar:
1. Volte para a **Release** criada
2. Procure em **Assets** pelos arquivos:
   - `EviChain-*.exe` — Instalador Windows
   - `EviChain-*.msi` — Setup Windows
   - `EviChain-*.zip` — Portable ZIP

## 🔧 Customizar o Build

Se você tiver um projeto **Electron** ou **Next.js**, atualize o `package.json`:

```json
{
  "scripts": {
    "build": "your-build-command",
    "electron-builder": "electron-builder --win -p always"
  },
  "build": {
    "appId": "com.evichain.app",
    "productName": "EviChain",
    "directories": {
      "output": "dist",
      "buildResources": "assets"
    },
    "win": {
      "target": ["exe", "msi", "zip"]
    }
  }
}
```

## 📋 Checklist para Release

- [ ] Todos os testes passam localmente
- [ ] Versão atualizada no `package.json`
- [ ] `README.md` atualizado
- [ ] Commit feito na `main`
- [ ] Push para origin
- [ ] Release criada no GitHub
- [ ] Workflow completou com sucesso
- [ ] Executáveis disponíveis em Assets

## 🐛 Troubleshooting

### Build falha
- Verifique os logs em **Actions > Build & Release Executável > {run} > logs**
- Certifique-se de que `npm install` e `npm run build` funcionam localmente
- Valide o `package.json` com: `npm list`

### Executáveis não aparecem na Release
- Ajuste os paths em `.github/workflows/build-release.yml`:
  ```yml
  files: |
    dist/**/*.exe
    dist/**/*.msi
    release/**/*.exe
  ```

### Permissão negada no push
- Verifique as secrets configuradas no repositório
- Git token precisa de permissão `contents:write`

## 📖 Documentação Oficial
- [GitHub Actions](https://docs.github.com/en/actions)
- [GitHub Pages](https://pages.github.com/)
- [Semantic Versioning](https://semver.org/)
- [Electron Builder](https://www.electron.build/)
