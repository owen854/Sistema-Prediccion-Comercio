# Prepara el entorno de desarrollo en Windows (frontend y backend en modo secuencial).
# Uso, desde "Codigo Fuente":  powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
# Lo paralelo (OpenMP, MPI) y PostgreSQL van en WSL: scripts/setup_wsl_hpc.sh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "== 1/3 uv (gestor de entornos de Python)" -ForegroundColor Yellow
python -m uv --version
if (-not $?) { python -m pip install --user uv }

Write-Host "== 2/3 Backend: dependencias y pruebas" -ForegroundColor Yellow
Push-Location (Join-Path $Root "backend")
python -m uv sync
python -m uv run pytest -q -m "not mpi and not cuda" -p no:warnings
Pop-Location

Write-Host "== 3/3 Frontend: dependencias y pruebas" -ForegroundColor Yellow
Push-Location (Join-Path $Root "frontend")
if (-not (Test-Path ".env.local")) { Copy-Item ".env.example" ".env.local" }
npm ci
npm test
Pop-Location

Write-Host "Listo. API: tasks.ps1 api   |   Web: tasks.ps1 web" -ForegroundColor Green
