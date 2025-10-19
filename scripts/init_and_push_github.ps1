param(
  [string]$RepoName
)

$ErrorActionPreference = "Stop"

# Config utente
$GithubUser = "tommasopatti2-a11y"
$GithubEmail = "tommasopatti2@gmail.com"

# Verifica posizione (root progetto)
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $Here
Set-Location $ProjectRoot
Write-Host "Project root: $ProjectRoot"

if (-not $RepoName) {
  $RepoName = Read-Host "Inserisci il nome del repository (es. app-orario)"
}
if (-not $RepoName) { throw "RepoName obbligatorio" }

# Inizializza git (se non già inizializzato)
if (-not (Test-Path ".git")) {
  git init | Out-Null
  git branch -M main | Out-Null
}

# Configura nome/email
$existingName = git config user.name 2>$null
$existingEmail = git config user.email 2>$null
if (-not $existingName) { git config user.name $GithubUser | Out-Null }
if (-not $existingEmail) { git config user.email $GithubEmail | Out-Null }

# Crea .gitignore root se mancante
$rootIgnore = Join-Path $ProjectRoot ".gitignore"
if (-not (Test-Path $rootIgnore)) {
  @"
# Python
.venv/
__pycache__/
*.pyc

# Node/Vite
frontend/node_modules/
frontend/dist/
frontend/.vite/

# Logs/OS
*.log
.DS_Store

# Env
.env
frontend/.env
"@ | Set-Content -NoNewline -Encoding UTF8 $rootIgnore
  Write-Host "Creato .gitignore root"
}

# Aggiungi tutti i file e commit iniziale
# Evita di includere node_modules o dist grazie ai .gitignore
try {
  git add .
  git commit -m "chore: initial commit (frontend+backend, render.yaml, netlify.toml)" | Out-Null
} catch {
  Write-Host "Niente da committare o commit già presente" -ForegroundColor Yellow
}

# Funzione per verificare se gh (GitHub CLI) è disponibile
function Test-Gh {
  try { gh --version | Out-Null; return $true } catch { return $false }
}

$repoFull = "$GithubUser/$RepoName"
$remoteExists = (git remote 2>$null) -contains "origin"

if (Test-Gh) {
  Write-Host "GitHub CLI rilevata. Creo il repo $repoFull e faccio push..." -ForegroundColor Cyan
  # Crea repo se non esiste e imposta remoto origin automaticamente
  # --public: puoi cambiare in --private se preferisci
  gh repo create $repoFull --public --source . --remote origin --push
} else {
  Write-Host "GitHub CLI non trovata. Creo il remoto e faccio push, assicurati di aver creato il repo su GitHub: https://github.com/new" -ForegroundColor Yellow
  if (-not $remoteExists) {
    git remote add origin "https://github.com/$repoFull.git"
  }
  Write-Host "Eseguo push su origin/main..."
  git push -u origin main
}

Write-Host "Completato. Repository: https://github.com/$repoFull" -ForegroundColor Green
