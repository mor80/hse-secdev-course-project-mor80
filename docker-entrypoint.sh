#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-wishlist_user}"
DB_NAME="${DB_NAME:-wishlist_db}"
SKIP_DB_WAIT="${SKIP_DB_WAIT:-false}"

if [[ "${SKIP_DB_WAIT}" != "true" ]]; then
    echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}/${DB_NAME}..."
    until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; do
        sleep 1
    done
    echo "PostgreSQL is ready!"
else
    echo "Skipping database availability check."
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
