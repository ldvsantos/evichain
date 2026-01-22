param(
  [Parameter(Mandatory = $false)]
  [Alias('Host')]
  [string]$Server = '3.15.2.17',

  [Parameter(Mandatory = $false)]
  [string]$User = 'ubuntu',

  [Parameter(Mandatory = $false)]
  [string]$KeyPath = "$env:USERPROFILE\.ssh\evichain.pem",

  [Parameter(Mandatory = $false)]
  [int]$SshPort = 22,

  [Parameter(Mandatory = $false)]
  [int]$SshConnectTimeoutSeconds = 15,

  [Parameter(Mandatory = $false)]
  [string]$RemoteDir = '/opt/evichain',

  [Parameter(Mandatory = $false)]
  [string]$Service = 'evichain',

  [Parameter(Mandatory = $false)]
  [string]$Branch = '',

  [Parameter(Mandatory = $false)]
  [switch]$Init,

  [Parameter(Mandatory = $false)]
  [switch]$SkipGit,

  [Parameter(Mandatory = $false)]
  [switch]$AllowDirty,

  [Parameter(Mandatory = $false)]
  [switch]$AutoCommit,

  [Parameter(Mandatory = $false)]
  [string]$CommitMessage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
  Write-Host "ERRO: $Message" -ForegroundColor Red
  exit 1
}

function ConvertToSshRepoUrl([string]$Url) {
  if (-not $Url) { return $Url }
  if ($Url -match '^git@') { return $Url }

  # https://github.com/owner/repo.git  ->  git@github.com:owner/repo.git
  if ($Url -match '^https://github\.com/(?<owner>[^/]+)/(?<repo>[^/]+?)(?:\.git)?$') {
    return "git@github.com:$($Matches['owner'])/$($Matches['repo']).git"
  }

  return $Url
}

function TestTcpPort {
  param(
    [Parameter(Mandatory = $true)][string]$ComputerName,
    [Parameter(Mandatory = $true)][int]$Port,
    [Parameter(Mandatory = $false)][int]$TimeoutMs = 1500
  )

  $tnc = Get-Command Test-NetConnection -ErrorAction SilentlyContinue
  if ($null -ne $tnc) {
    try {
      $r = Test-NetConnection -ComputerName $ComputerName -Port $Port -WarningAction SilentlyContinue
      return [bool]$r.TcpTestSucceeded
    } catch {
      return $false
    }
  }

  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $client.BeginConnect($ComputerName, $Port, $null, $null)
    $ok = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
    if (-not $ok) { return $false }
    $client.EndConnect($async)
    return $true
  } catch {
    return $false
  } finally {
    try { $client.Close() } catch {}
  }
}

# Em PowerShell 7+, alguns comandos nativos escrevendo em stderr podem virar erro.
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
  $global:PSNativeCommandUseErrorActionPreference = $false
}

# Carrega config local opcional (não versionada)
$configPath = Join-Path $PSScriptRoot 'deploy-config.ps1'
if (Test-Path $configPath) {
  try {
    $cfg = . $configPath
    if ($cfg -is [hashtable]) {
      if ($cfg.ContainsKey('Host'))      { $Server = [string]$cfg['Host'] }
      if ($cfg.ContainsKey('User'))      { $User = [string]$cfg['User'] }
      if ($cfg.ContainsKey('KeyPath'))   { $KeyPath = [string]$cfg['KeyPath'] }
      if ($cfg.ContainsKey('SshPort'))   { $SshPort = [int]$cfg['SshPort'] }
      if ($cfg.ContainsKey('RemoteDir')) { $RemoteDir = [string]$cfg['RemoteDir'] }
      if ($cfg.ContainsKey('Service'))   { $Service = [string]$cfg['Service'] }
      if ($cfg.ContainsKey('Branch'))    { $Branch = [string]$cfg['Branch'] }
      if ($cfg.ContainsKey('AppPort'))   { $script:AppPort = [int]$cfg['AppPort'] }
    }
  } catch {
    Fail ("Falha ao carregar ${configPath}: " + $_.Exception.Message)
  }
}

if (-not (Get-Variable -Name AppPort -Scope Script -ErrorAction SilentlyContinue)) {
  $script:AppPort = 8000
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Fallback: se a chave existir no root do repo
if (-not (Test-Path $KeyPath)) {
  $localKey = Join-Path $repoRoot 'evichain.pem'
  if (Test-Path $localKey) {
    Write-Host "AVISO: usando chave local em '$localKey'" -ForegroundColor Yellow
    $KeyPath = $localKey
  }
}

if (-not (Test-Path $KeyPath)) {
  Fail "Chave SSH não encontrada. Ajuste KeyPath (ou crie scripts/deploy-config.ps1)."
}

foreach ($cmd in @('ssh', 'scp')) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Fail "Comando não encontrado no PATH: $cmd (instale OpenSSH client)"
  }
}

Push-Location $repoRoot
try {
  Write-Host "Testando conectividade SSH: ${Server}:$SshPort ..." -ForegroundColor DarkGray
  $timeoutMs = [Math]::Max(1000, $SshConnectTimeoutSeconds * 1000)
  if (-not (TestTcpPort -ComputerName $Server -Port $SshPort -TimeoutMs $timeoutMs)) {
    Fail "Não foi possível conectar em ${Server}:$SshPort (TCP). Verifique Security Group (porta 22 para seu IP)."
  }

  if (-not $SkipGit) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      Fail 'Git não encontrado. Instale o Git ou rode com -SkipGit.'
    }

    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail 'Esta pasta não parece ser um repositório Git.' }

    $statusPorcelain = git status --porcelain
    if ($statusPorcelain) {
      if ($AutoCommit) {
        if (-not $CommitMessage) {
          $CommitMessage = Read-Host 'Digite a mensagem do commit (obrigatório)'
        }
        if (-not $CommitMessage -or -not $CommitMessage.Trim()) {
          Fail 'Mensagem de commit vazia. Cancelando.'
        }
        git add -A
        if ($LASTEXITCODE -ne 0) { Fail 'git add falhou' }
        git commit -m $CommitMessage
        if ($LASTEXITCODE -ne 0) { Fail 'git commit falhou' }
      } elseif (-not $AllowDirty) {
        Fail "Há alterações locais não commitadas. Use -AutoCommit ou faça commit manualmente.\n\n$statusPorcelain"
      }
    }

    git fetch --prune
    if ($LASTEXITCODE -ne 0) { Fail 'git fetch falhou' }

    $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if (-not $Branch -or -not $Branch.Trim()) {
      $Branch = $currentBranch
    }

    if ($currentBranch -ne $Branch) {
      Fail "Branch atual é '$currentBranch', mas deploy está configurado para '$Branch'."
    }

    git pull --rebase
    if ($LASTEXITCODE -ne 0) { Fail 'git pull --rebase falhou' }

    git push
    if ($LASTEXITCODE -ne 0) { Fail 'git push falhou' }
  }

  $repoUrl = (git remote get-url origin).Trim()
  if (-not $repoUrl) { Fail 'Não foi possível detectar o remote origin.' }

  $repoSshUrl = ConvertToSshRepoUrl $repoUrl
  if (-not $repoSshUrl) { Fail 'Não foi possível detectar o remote origin (SSH).' }

  if ($Init) {
    Write-Host "Deploy remoto: SETUP (primeira vez)" -ForegroundColor Cyan
  } else {
    Write-Host "Deploy remoto: deploy incremental" -ForegroundColor Cyan
  }

  $remoteScript = @'
set -euo pipefail

REMOTE_DIR="__REMOTE_DIR__"
BRANCH="__BRANCH__"
SERVICE_NAME="__SERVICE__"
REPO_URL="__REPO_URL__"
APP_USER="__APP_USER__"
APP_PORT="__APP_PORT__"
FORCE_SETUP="__FORCE_SETUP__"

if [ ! -d "$REMOTE_DIR/.git" ]; then
  sudo mkdir -p "$REMOTE_DIR"
  sudo chown -R "$APP_USER:$APP_USER" "$REMOTE_DIR"
  git clone "$REPO_URL" "$REMOTE_DIR"
fi

cd "$REMOTE_DIR"

git remote set-url origin "$REPO_URL" || true

git fetch --prune
git checkout "$BRANCH"
git pull --rebase origin "$BRANCH"

if [ "$FORCE_SETUP" = "1" ] || [ ! -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
  REPO_URL="$REPO_URL" REMOTE_DIR="$REMOTE_DIR" SERVICE_NAME="$SERVICE_NAME" APP_PORT="$APP_PORT" APP_USER="$APP_USER" bash scripts/ec2_setup.sh
else
  REMOTE_DIR="$REMOTE_DIR" SERVICE_NAME="$SERVICE_NAME" BRANCH="$BRANCH" bash scripts/ec2_deploy.sh
fi

# Healthcheck via localhost (nginx)
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1/api/health >/dev/null 2>&1; then
    echo DEPLOY_OK
    exit 0
  fi
  sleep 0.5
 done

echo HEALTHCHECK_FAILED
exit 1
'@

  $remoteScript = $remoteScript.Replace('__REMOTE_DIR__', $RemoteDir)
  $remoteScript = $remoteScript.Replace('__BRANCH__', $Branch)
  $remoteScript = $remoteScript.Replace('__SERVICE__', $Service)
  $remoteScript = $remoteScript.Replace('__REPO_URL__', $repoSshUrl)
  $remoteScript = $remoteScript.Replace('__APP_USER__', $User)
  $remoteScript = $remoteScript.Replace('__APP_PORT__', [string]$script:AppPort)
  $remoteScript = $remoteScript.Replace('__FORCE_SETUP__', $(if ($Init) { '1' } else { '0' }))

  # Normaliza quebras de linha para LF
  $remoteScriptContent = ($remoteScript -replace "`r`n", "`n") -replace "`r", ""

  $remoteScriptContent | & ssh -p $SshPort -o ConnectTimeout=$SshConnectTimeoutSeconds -o StrictHostKeyChecking=no -i $KeyPath "${User}@${Server}" "sudo bash -s"
  if ($LASTEXITCODE -ne 0) { Fail 'Deploy remoto falhou (veja logs acima)' }

  Write-Host "DEPLOY FINALIZADO: http://$Server/" -ForegroundColor Green
}
finally {
  Pop-Location
}
