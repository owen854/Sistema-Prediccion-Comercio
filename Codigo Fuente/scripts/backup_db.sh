#!/usr/bin/env bash
# Respaldo de la base de datos (RNF-14). Uso: bash scripts/backup_db.sh [url]
# La carpeta backups/ no se versiona.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="${1:-${FORECAST_DATABASE_URL:-postgresql://forecast:forecast@localhost:5432/forecast}}"
URL="${URL/postgresql+psycopg/postgresql}"
mkdir -p "$ROOT/backups"
OUT="$ROOT/backups/forecast_$(date +%Y%m%dT%H%M%S).dump"
pg_dump --format=custom --dbname="$URL" --file="$OUT"
echo "Respaldo creado: $OUT"
echo "Restaurar con: pg_restore --clean --dbname=<url> \"$OUT\""
