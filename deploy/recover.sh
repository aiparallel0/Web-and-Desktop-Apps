#!/usr/bin/env bash
# deploy/recover.sh — Bring a broken existing install back to healthy state
# Usage: sudo bash /opt/image-to-text/deploy/recover.sh
# Safe to run on a live install — idempotent, does NOT re-clone the repo.
set -euo pipefail

DEPLOY_ROOT="/opt/image-to-text"
SERVICE="image-to-text"

echo ""
echo "============================================================"
echo "  Image to Text — Recovery"
echo "  Deploy root: ${DEPLOY_ROOT}"
echo "============================================================"
echo ""

if [ ! -d "${DEPLOY_ROOT}" ]; then
    echo "ERROR: ${DEPLOY_ROOT} does not exist. Run deploy/install.sh first."
    exit 1
fi

cd "${DEPLOY_ROOT}"

# ---------------------------------------------------------------------------
# 1. Stop the service gracefully
# ---------------------------------------------------------------------------
echo "[1/7] Stopping service..."
systemctl stop "${SERVICE}" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 2. Fix directory structure
# ---------------------------------------------------------------------------
echo "[2/7] Recreating runtime directories and log files..."
mkdir -p "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"
chmod 755 "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"
for logfile in access.log error.log gunicorn.log; do
    touch "${DEPLOY_ROOT}/logs/${logfile}"
done

# ---------------------------------------------------------------------------
# 3. Ensure .env exists and secrets are set
# ---------------------------------------------------------------------------
echo "[3/7] Checking environment configuration..."
if [ ! -f "${DEPLOY_ROOT}/.env" ]; then
    echo "  .env missing — creating from template..."
    cp "${DEPLOY_ROOT}/.env.production.template" "${DEPLOY_ROOT}/.env"
fi

if grep -qE "^(SECRET_KEY|JWT_SECRET)=.*(CHANGE_ME|REPLACE_ME|REPLACE_WITH_GENERATED)" "${DEPLOY_ROOT}/.env" || \
   grep -qE "^(SECRET_KEY|JWT_SECRET)=$" "${DEPLOY_ROOT}/.env"; then
    echo "  Generating random SECRET_KEY and JWT_SECRET..."
    NEW_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
    NEW_JWT=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${NEW_SECRET}|" "${DEPLOY_ROOT}/.env"
    sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${NEW_JWT}|" "${DEPLOY_ROOT}/.env"
fi

# Ensure USE_SQLITE is true (VPS default — no PostgreSQL)
if ! grep -q "^USE_SQLITE=" "${DEPLOY_ROOT}/.env"; then
    echo "USE_SQLITE=true" >> "${DEPLOY_ROOT}/.env"
else
    sed -i "s|^USE_SQLITE=.*|USE_SQLITE=true|" "${DEPLOY_ROOT}/.env"
fi

# ---------------------------------------------------------------------------
# 4. Fix ownership and permissions
# ---------------------------------------------------------------------------
echo "[4/7] Fixing ownership and permissions..."
chown -R www-data:www-data "${DEPLOY_ROOT}"
chmod 640 "${DEPLOY_ROOT}/.env"
chown www-data:www-data "${DEPLOY_ROOT}/logs/access.log" "${DEPLOY_ROOT}/logs/error.log" "${DEPLOY_ROOT}/logs/gunicorn.log" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 5. Run database migrations
# ---------------------------------------------------------------------------
echo "[5/7] Running database migrations..."
sudo -u www-data "${DEPLOY_ROOT}/venv/bin/python3" -m alembic upgrade head 2>/dev/null || \
    echo "  Alembic migration skipped (SQLite will auto-create on first run)."

# ---------------------------------------------------------------------------
# 6. Reload and restart the systemd service
# ---------------------------------------------------------------------------
echo "[6/7] Reloading and restarting service..."
# Re-install service file in case it was overwritten or lost
if [ -f "${DEPLOY_ROOT}/deploy/systemd/image-to-text.service" ]; then
    install -m 644 \
        "${DEPLOY_ROOT}/deploy/systemd/image-to-text.service" \
        "/etc/systemd/system/${SERVICE}.service"
fi
systemctl daemon-reload
systemctl enable "${SERVICE}"
systemctl start "${SERVICE}"

# ---------------------------------------------------------------------------
# 7. Health check — poll /api/health for up to 30s
# ---------------------------------------------------------------------------
echo "[7/7] Waiting for service to become healthy..."
HTTP_CODE="000"
for i in $(seq 1 30); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:8000/api/health" 2>/dev/null || echo "000")
    if [ "${HTTP_CODE}" = "200" ]; then
        break
    fi
    sleep 1
done

echo ""
echo "============================================================"
if [ "${HTTP_CODE}" = "200" ]; then
    echo "  Recovery complete. Health check: HTTP ${HTTP_CODE}"
    echo "  Service status: $(systemctl is-active ${SERVICE})"
    echo ""
    echo "  Run the full smoke test:"
    echo "    bash ${DEPLOY_ROOT}/deploy/smoke_test.sh image-to-text.fit"
else
    echo "  Health check FAILED (HTTP ${HTTP_CODE})."
    echo "  Service status: $(systemctl is-active ${SERVICE} 2>/dev/null || echo unknown)"
    echo ""
    echo "  Diagnostics:"
    echo "    journalctl -u ${SERVICE} -n 50 --no-pager"
    echo "    cat ${DEPLOY_ROOT}/logs/gunicorn.log"
    exit 1
fi
echo "============================================================"
echo ""
