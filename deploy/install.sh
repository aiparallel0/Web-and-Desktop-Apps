#!/usr/bin/env bash
# deploy/install.sh — One-shot VPS bootstrap for image-to-text.fit
# Usage: sudo bash deploy/install.sh [domain]
# Example: sudo bash deploy/install.sh image-to-text.fit
set -euo pipefail

DOMAIN="${1:-image-to-text.fit}"
DEPLOY_ROOT="/opt/image-to-text"
REPO_URL="https://github.com/aiparallel0/Web-and-Desktop-Apps.git"
SERVICE="image-to-text"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@image-to-text.fit}"

echo ""
echo "============================================================"
echo "  Image to Text — VPS Bootstrap"
echo "  Domain: ${DOMAIN}"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# 1. System update + dependencies
# ---------------------------------------------------------------------------
echo "[1/8] Updating system and installing dependencies..."
apt-get update -qq
apt-get install -y -qq \
    git python3 python3-venv python3-pip \
    nginx certbot python3-certbot-nginx \
    tesseract-ocr

# ---------------------------------------------------------------------------
# 2. Clone or update the repo
# ---------------------------------------------------------------------------
echo "[2/8] Cloning repository to ${DEPLOY_ROOT}..."
if [ -d "${DEPLOY_ROOT}/.git" ]; then
    echo "  Repository already exists — pulling latest..."
    git -C "${DEPLOY_ROOT}" pull --ff-only
else
    git clone "${REPO_URL}" "${DEPLOY_ROOT}"
fi

# ---------------------------------------------------------------------------
# 3. Python virtual environment + dependencies
# ---------------------------------------------------------------------------
echo "[3/8] Setting up Python virtual environment..."
if [ ! -d "${DEPLOY_ROOT}/venv" ]; then
    python3 -m venv "${DEPLOY_ROOT}/venv"
fi
"${DEPLOY_ROOT}/venv/bin/pip" install --quiet --upgrade pip
"${DEPLOY_ROOT}/venv/bin/pip" install --quiet -r "${DEPLOY_ROOT}/requirements-prod.txt"

# ---------------------------------------------------------------------------
# 4. Create runtime directories and .env
# ---------------------------------------------------------------------------
echo "[4/8] Creating runtime directories..."
mkdir -p "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"

if [ ! -f "${DEPLOY_ROOT}/.env" ]; then
    echo "  Creating .env from template..."
    cp "${DEPLOY_ROOT}/.env.production.template" "${DEPLOY_ROOT}/.env"
    echo ""
    echo "  IMPORTANT: Edit ${DEPLOY_ROOT}/.env and set:"
    echo "    SECRET_KEY  (run: python3 generate-secrets.py)"
    echo "    JWT_SECRET  (run: python3 generate-secrets.py)"
    echo ""
fi

# ---------------------------------------------------------------------------
# 5. Database migration
# ---------------------------------------------------------------------------
echo "[5/8] Running database migrations..."
cd "${DEPLOY_ROOT}"
"${DEPLOY_ROOT}/venv/bin/python3" -m alembic upgrade head 2>/dev/null || \
    echo "  Alembic migration skipped (SQLite will auto-create on first run)."

# ---------------------------------------------------------------------------
# 6. Install nginx config
# ---------------------------------------------------------------------------
echo "[6/8] Installing nginx configuration..."
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"
NGINX_LINK="/etc/nginx/sites-enabled/${DOMAIN}"

cp "${DEPLOY_ROOT}/deploy/nginx/image-to-text.fit.conf" "${NGINX_CONF}"
# Replace domain if a custom one was passed
if [ "${DOMAIN}" != "image-to-text.fit" ]; then
    sed -i "s/image-to-text\.fit/${DOMAIN}/g" "${NGINX_CONF}"
fi

if [ ! -L "${NGINX_LINK}" ]; then
    ln -s "${NGINX_CONF}" "${NGINX_LINK}"
fi

# Remove default site if still enabled
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    rm -f /etc/nginx/sites-enabled/default
fi

mkdir -p /var/www/certbot
nginx -t
systemctl reload nginx

# ---------------------------------------------------------------------------
# 7. Obtain TLS certificate via certbot
# ---------------------------------------------------------------------------
echo "[7/8] Obtaining TLS certificate..."
if certbot --nginx \
    -d "${DOMAIN}" -d "www.${DOMAIN}" \
    --non-interactive --agree-tos -m "${ADMIN_EMAIL}" \
    --redirect 2>&1; then
    systemctl reload nginx
    echo "  TLS certificate obtained."
else
    echo "  certbot failed — DNS may not point here yet. Run manually after DNS:"
    echo "    certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
fi

# ---------------------------------------------------------------------------
# 8. Install and enable systemd service
# ---------------------------------------------------------------------------
echo "[8/8] Installing systemd service..."
install -m 644 \
    "${DEPLOY_ROOT}/deploy/systemd/image-to-text.service" \
    "/etc/systemd/system/${SERVICE}.service"

# Point service WorkingDirectory / EnvironmentFile at actual location
if [ "${DEPLOY_ROOT}" != "/opt/image-to-text" ]; then
    sed -i "s|/opt/image-to-text|${DEPLOY_ROOT}|g" "/etc/systemd/system/${SERVICE}.service"
fi

systemctl daemon-reload
systemctl enable --now "${SERVICE}"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://127.0.0.1:8000/api/health" 2>/dev/null || echo "000")
echo ""
echo "============================================================"
echo "  Installation complete."
echo "  Health check (local): HTTP ${HTTP_CODE}"
echo ""
echo "  Next steps:"
echo "    1. Ensure DNS A record for ${DOMAIN} points to this server."
echo "    2. Edit ${DEPLOY_ROOT}/.env and set SECRET_KEY + JWT_SECRET."
echo "    3. systemctl restart ${SERVICE}"
echo "    4. bash ${DEPLOY_ROOT}/deploy/smoke_test.sh ${DOMAIN}"
echo "============================================================"
echo ""
