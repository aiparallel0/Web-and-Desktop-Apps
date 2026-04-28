#!/usr/bin/env bash
# deploy/redeploy.sh — Pull latest code and restart the service
# Usage: sudo bash /opt/image-to-text/deploy/redeploy.sh
set -euo pipefail

DEPLOY_ROOT="/opt/image-to-text"
SERVICE="image-to-text"
cd "${DEPLOY_ROOT}"

echo "=== Image to Text — Redeploy ==="

echo "[1/4] Pulling latest code..."
git pull --ff-only origin main

echo "[2/4] Installing Python dependencies..."
venv/bin/pip install --quiet -r requirements-prod.txt

echo "[3/4] Running database migrations..."
venv/bin/python3 -m alembic upgrade head 2>/dev/null || \
    echo "  Alembic migration skipped."

echo "[4/4] Restarting service..."
systemctl restart "${SERVICE}"

sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://127.0.0.1:8000/api/health" 2>/dev/null || echo "000")
if [ "${HTTP_CODE}" = "200" ]; then
    echo "  Health check passed (HTTP ${HTTP_CODE})."
else
    echo "  Health check FAILED (HTTP ${HTTP_CODE})."
    echo "  Check logs: journalctl -u ${SERVICE} -n 50"
    exit 1
fi

echo ""
echo "Redeploy complete. Service: $(systemctl is-active ${SERVICE})"
