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
    git -C "${DEPLOY_ROOT}" -c safe.directory="${DEPLOY_ROOT}" pull --ff-only
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

# AI engines (Donut, Florence-2, EasyOCR, CRAFT). Adds ~3 GB on disk.
# Set INSTALL_AI=0 to skip on capacity-constrained hosts.
if [ "${INSTALL_AI:-1}" = "1" ]; then
    echo "  Installing AI engine dependencies (set INSTALL_AI=0 to skip)..."
    "${DEPLOY_ROOT}/venv/bin/pip" install -r "${DEPLOY_ROOT}/requirements-prod-ai.txt" \
        || echo "  WARNING: AI deps install failed; only Tesseract will be available."
    # PaddleOCR wheels are flaky on slim Ubuntu — install separately, never fatal.
    "${DEPLOY_ROOT}/venv/bin/pip" install paddleocr paddlepaddle 2>/dev/null \
        || echo "  Note: PaddleOCR install skipped/failed (non-fatal)."
fi

# ---------------------------------------------------------------------------
# 4. Create runtime directories, log files, and .env
# ---------------------------------------------------------------------------
echo "[4/8] Creating runtime directories and configuring environment..."
mkdir -p "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"
chmod 755 "${DEPLOY_ROOT}/logs" "${DEPLOY_ROOT}/uploads"

# Pre-create log files so systemd append: directives never fail on first boot
for logfile in access.log error.log gunicorn.log; do
    touch "${DEPLOY_ROOT}/logs/${logfile}"
done

if [ ! -f "${DEPLOY_ROOT}/.env" ]; then
    echo "  Creating .env from template..."
    cp "${DEPLOY_ROOT}/.env.production.template" "${DEPLOY_ROOT}/.env"
fi

# Auto-generate secrets if placeholders are still present
if grep -qE "^(SECRET_KEY|JWT_SECRET)=.*(CHANGE_ME|REPLACE_ME|REPLACE_WITH_GENERATED)" "${DEPLOY_ROOT}/.env" || \
   grep -qE "^(SECRET_KEY|JWT_SECRET)=$" "${DEPLOY_ROOT}/.env"; then
    echo "  Generating random SECRET_KEY and JWT_SECRET..."
    NEW_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
    NEW_JWT=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${NEW_SECRET}|" "${DEPLOY_ROOT}/.env"
    sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${NEW_JWT}|" "${DEPLOY_ROOT}/.env"
fi

# Ensure USE_SQLITE is set (VPS has no PostgreSQL by default)
if ! grep -q "^USE_SQLITE=" "${DEPLOY_ROOT}/.env"; then
    echo "USE_SQLITE=true" >> "${DEPLOY_ROOT}/.env"
else
    sed -i "s|^USE_SQLITE=.*|USE_SQLITE=true|" "${DEPLOY_ROOT}/.env"
fi

# Set correct ownership and permissions
chown -R www-data:www-data "${DEPLOY_ROOT}"
chmod 640 "${DEPLOY_ROOT}/.env"

# ---------------------------------------------------------------------------
# 5. Database migration
# ---------------------------------------------------------------------------
echo "[5/8] Running database migrations..."
cd "${DEPLOY_ROOT}"
sudo -u www-data "${DEPLOY_ROOT}/venv/bin/python3" -m alembic upgrade head 2>/dev/null || \
    echo "  Alembic migration skipped (SQLite will auto-create on first run)."

# ---------------------------------------------------------------------------
# 6. Install nginx config — HTTP stub first, SSL config after certbot
# ---------------------------------------------------------------------------
echo "[6/8] Installing nginx configuration..."
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"
NGINX_LINK="/etc/nginx/sites-enabled/${DOMAIN}"
HTTP_CONF="${DEPLOY_ROOT}/deploy/nginx/image-to-text.fit.http.conf"
FULL_CONF="${DEPLOY_ROOT}/deploy/nginx/image-to-text.fit.conf"

# Install HTTP-only stub so nginx -t passes before certbot runs
cp "${HTTP_CONF}" "${NGINX_CONF}"
if [ "${DOMAIN}" != "image-to-text.fit" ]; then
    sed -i "s/image-to-text\.fit/${DOMAIN}/g" "${NGINX_CONF}"
fi

if [ ! -L "${NGINX_LINK}" ]; then
    ln -s "${NGINX_CONF}" "${NGINX_LINK}"
fi

# Remove default site if still enabled (leave other sites alone)
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
    # Certbot succeeded — overwrite with the full SSL vhost config
    cp "${FULL_CONF}" "${NGINX_CONF}"
    if [ "${DOMAIN}" != "image-to-text.fit" ]; then
        sed -i "s/image-to-text\.fit/${DOMAIN}/g" "${NGINX_CONF}"
    fi
    nginx -t
    systemctl reload nginx
    echo "  TLS certificate obtained and full SSL config installed."
else
    echo "  certbot failed — DNS may not point here yet. Run manually after DNS:"
    echo "    certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
    echo "  Site will serve HTTP until TLS is configured."
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
# Health poll — wait up to 30s for gunicorn to be ready
# ---------------------------------------------------------------------------
echo "  Waiting for service to become healthy..."
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
echo "  Installation complete."
echo "  Health check (local): HTTP ${HTTP_CODE}"
echo ""
echo "  Next steps:"
echo "    1. Ensure DNS A record for ${DOMAIN} points to this server."
if [ "${HTTP_CODE}" != "200" ]; then
    echo "    2. Edit ${DEPLOY_ROOT}/.env if secrets need updating."
    echo "    3. systemctl restart ${SERVICE}"
fi
echo "    4. bash ${DEPLOY_ROOT}/deploy/smoke_test.sh ${DOMAIN}"
echo "============================================================"
echo ""

