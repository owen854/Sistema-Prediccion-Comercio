# Atajos para Windows (equivalentes al Makefile). Uso:  .\tasks.ps1 <tarea>
#   setup | test | lint | typecheck | api | web | gen-api
param([Parameter(Mandatory = $true)][string]$Tarea)
$ErrorActionPreference = "Stop"
$Backend = Join-Path $PSScriptRoot "backend"
$Frontend = Join-Path $PSScriptRoot "frontend"

switch ($Tarea) {
  "setup" { & (Join-Path $PSScriptRoot "scripts\setup_dev.ps1") }
  "test" {
    Push-Location $Backend; python -m uv run pytest -q -m "not mpi and not cuda"; Pop-Location
    Push-Location $Frontend; npm test; Pop-Location
  }
  "lint" {
    Push-Location $Backend; python -m uv run ruff format --check .; python -m uv run ruff check .; Pop-Location
    Push-Location $Frontend; npm run lint; Pop-Location
  }
  "typecheck" {
    Push-Location $Backend; python -m uv run mypy; Pop-Location
    Push-Location $Frontend; npm run typecheck; Pop-Location
  }
  "api" { Push-Location $Backend; python -m uv run uvicorn forecast_api.main:app --reload; Pop-Location }
  "web" { Push-Location $Frontend; npm run dev; Pop-Location }
  "gen-api" { Push-Location $Frontend; npm run gen:api; Pop-Location }
  default { Write-Error "Tarea desconocida: $Tarea. Opciones: setup, test, lint, typecheck, api, web, gen-api" }
}
