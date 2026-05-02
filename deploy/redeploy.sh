#!/usr/bin/env bash
# deploy/redeploy.sh — Pull latest code and restart the service
# Usage: sudo bash /opt/image-to-text/deploy/redeploy.sh
set -euo pipefail

DEPLOY_ROOT="/opt/image-to-text"
SERVICE="image-to-text"
cd "${DEPLOY_ROOT}"

echo "=== Image to Text — Redeploy ==="

echo "[1/5] Pulling latest code..."
# Pull as www-data so new files land with the correct owner
git -C "${DEPLOY_ROOT}" -c safe.directory="${DEPLOY_ROOT}" pull --ff-only origin main

echo "[2/5] Installing Python dependencies..."
venv/bin/pip install --quiet -r requirements-prod.txt

# AI engines — set INSTALL_AI=0 to skip on capacity-constrained hosts.
if [ "${INSTALL_AI:-1}" = "1" ] && [ -f requirements-prod-ai.txt ]; then
    echo "  Installing AI engine dependencies (INSTALL_AI=0 to skip)..."
    venv/bin/pip install -r requirements-prod-ai.txt \
        || echo "  WARNING: AI deps install failed; only Tesseract will be available."
    venv/bin/pip install paddleocr paddlepaddle 2>/dev/null \
        || echo "  Note: PaddleOCR install skipped/failed (non-fatal)."
fi

echo "[3/5] Running database migrations..."
sudo -u www-data venv/bin/python3 -m alembic upgrade head 2>/dev/null || \
    echo "  Alembic migration skipped."

echo "[4/5] Fixing ownership and permissions..."
chown -R www-data:www-data "${DEPLOY_ROOT}"
chmod 640 "${DEPLOY_ROOT}/.env"
# Ensure log files exist so systemd append: directives never fail
mkdir -p "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"
chmod 755 "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"
for logfile in access.log error.log gunicorn.log; do
    touch "${DEPLOY_ROOT}/logs/${logfile}"
done
chown www-data:www-data "${DEPLOY_ROOT}/logs/access.log" "${DEPLOY_ROOT}/logs/error.log" "${DEPLOY_ROOT}/logs/gunicorn.log" 2>/dev/null || true

echo "[5/5] Restarting service..."
systemctl restart "${SERVICE}"

# Poll /api/health for up to 30s
HTTP_CODE="000"
for i in $(seq 1 30); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:8000/api/health" 2>/dev/null || echo "000")
    if [ "${HTTP_CODE}" = "200" ]; then
        break
    fi
    sleep 1
done

if [ "${HTTP_CODE}" = "200" ]; then
    echo "  Health check passed (HTTP ${HTTP_CODE})."
else
    echo "  Health check FAILED (HTTP ${HTTP_CODE})."
    echo "  Check logs: journalctl -u ${SERVICE} -n 50"
    exit 1
fi

echo ""
echo "Redeploy complete. Service: $(systemctl is-active ${SERVICE})"

