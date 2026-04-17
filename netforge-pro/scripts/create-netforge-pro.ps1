# ============================================================
#   NETFORGE PRO - Création de la structure du projet
#   Projet : C:\Users\bkabe\Desktop\Projet-NCP\netforge-pro
# ============================================================

$ProjectRoot = "C:\Users\bkabe\Desktop\Projet-NCP\netforge-pro"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   NETFORGE PRO - Création de la structure du projet" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dossier de destination : $ProjectRoot" -ForegroundColor Yellow
Write-Host ""

# --- Création des dossiers ---
$folders = @(
    "$ProjectRoot",
    "$ProjectRoot\docs",
    "$ProjectRoot\src",
    "$ProjectRoot\src\parser_engine",
    "$ProjectRoot\src\rule_engine",
    "$ProjectRoot\src\ai_engine",
    "$ProjectRoot\src\graph_database",
    "$ProjectRoot\src\frontend",
    "$ProjectRoot\src\api_backend",
    "$ProjectRoot\src\security_module",
    "$ProjectRoot\src\correction_engine",
    "$ProjectRoot\src\reporting",
    "$ProjectRoot\src\discovery_engine",
    "$ProjectRoot\src\shared",
    "$ProjectRoot\tests",
    "$ProjectRoot\scripts",
    "$ProjectRoot\docs\skills",
    "$ProjectRoot\docs\skills\ui-ux-pro-max",
    "$ProjectRoot\docs\skills\ui-ux-pro-max\references"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    Write-Host "  OK $folder" -ForegroundColor Green
}

# --- .mcp.json ---
$mcpConfig = '{
  "mcpServers": {
    "magic-21st": {
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest"],
      "env": {
        "TWENTY_FIRST_API_KEY": "COLLE-TA-CLE-API-ICI"
      }
    }
  }
}'
Set-Content -Path "$ProjectRoot\.mcp.json" -Value $mcpConfig -Encoding UTF8
Write-Host "  OK .mcp.json cree" -ForegroundColor Green

# --- .gitignore ---
$gitignore = "__pycache__/
*.pyc
.venv/
venv/
node_modules/
.env
.env.local
.DS_Store
Thumbs.db
*.key
*.pem
.pytest_cache/"
Set-Content -Path "$ProjectRoot\.gitignore" -Value $gitignore -Encoding UTF8
Write-Host "  OK .gitignore cree" -ForegroundColor Green

# --- .env.example ---
$envExample = "# === API BACKEND ===
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=change-me-in-production
DEBUG=true

# === PostgreSQL ===
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=netforge
POSTGRES_USER=netforge
POSTGRES_PASSWORD=changeme

# === Neo4j ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === AI Engine ===
ANTHROPIC_API_KEY=sk-ant-XXXXXXXX
LLM_MODEL=claude-sonnet-4-6"
Set-Content -Path "$ProjectRoot\.env.example" -Value $envExample -Encoding UTF8
Write-Host "  OK .env.example cree" -ForegroundColor Green

# --- README.md ---
$readme = "# NetForge Pro
Network Copilot Platform - Analyse reseau multi-constructeur

## Stack
- Backend  : Python FastAPI
- Frontend : React 18 + TypeScript + React-Flow
- BDD      : PostgreSQL + Neo4j + Redis
"
Set-Content -Path "$ProjectRoot\README.md" -Value $readme -Encoding UTF8
Write-Host "  OK README.md cree" -ForegroundColor Green

# --- Résumé ---
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   PROJET CREE AVEC SUCCES !" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PROCHAINES ETAPES :" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Copie tes PDFs dans :"
Write-Host "     C:\Users\bkabe\Desktop\Projet-NCP\netforge-pro\docs\" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Copie les fichiers du skill (SKILL.md + references/) dans :"
Write-Host "     C:\Users\bkabe\Desktop\Projet-NCP\netforge-pro\docs\skills\ui-ux-pro-max\" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Ouvre .mcp.json et remplace COLLE-TA-CLE-API-ICI par ta cle 21st.dev"
Write-Host ""
Write-Host "  4. Upload le fichier .skill sur Claude.ai -> Parametres -> Skills"
Write-Host ""
Write-Host "  5. Ouvre VS Code avec cette commande :" -ForegroundColor Yellow
Write-Host "     code C:\Users\bkabe\Desktop\Projet-NCP\netforge-pro" -ForegroundColor Cyan
Write-Host ""
