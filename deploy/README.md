# deploy/README.md

## Path A: Railway one-click

Set these environment variables in the Railway dashboard before deploying:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Generate: `python generate-secrets.py` |
| `JWT_SECRET` | Generate: `python generate-secrets.py` |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `False` |
| `USE_SQLITE` | `true` (until PostgreSQL is added) |

Optional (add later):
- `DATABASE_URL` — Railway auto-sets this when you add a PostgreSQL service.
- `CORS_ORIGINS` — defaults to `https://image-to-text.fit,https://www.image-to-text.fit` in production.

Railway config is already set in `railway.json` (health check at `/api/health`) and `Procfile` (gunicorn bound to `$PORT`).

Custom domain steps:
1. In Railway dashboard, go to Settings → Domains → Add custom domain.
2. Add `image-to-text.fit` and `www.image-to-text.fit`.
3. Create DNS records as shown in the Railway UI (usually A or CNAME).
4. Railway provisions TLS automatically.

Expected outcome: `https://image-to-text.fit/` returns HTTP 200 with the landing page, `/api/health` returns `{"status":"healthy"}`.

---

## Path B: VPS via nginx + systemd

Requirements: Ubuntu 24.04, root access, DNS A record for `image-to-text.fit` pointing to the server.

```
# One-shot install
bash deploy/install.sh image-to-text.fit

# After DNS propagates, verify
bash deploy/smoke_test.sh image-to-text.fit
```

The install script:
1. Installs nginx, certbot, python3, tesseract.
2. Clones the repo to `/opt/image-to-text`.
3. Creates a virtualenv and installs `requirements-prod.txt`.
4. Runs Alembic migrations.
5. Installs `deploy/nginx/image-to-text.fit.conf` and runs certbot for TLS.
6. Installs and enables `deploy/systemd/image-to-text.service` (gunicorn on `127.0.0.1:8000`).

After install, edit `/opt/image-to-text/.env` and set `SECRET_KEY` and `JWT_SECRET`, then:

```
systemctl restart image-to-text
bash /opt/image-to-text/deploy/smoke_test.sh image-to-text.fit
```

To redeploy after a code push:

```
bash /opt/image-to-text/deploy/redeploy.sh
```
