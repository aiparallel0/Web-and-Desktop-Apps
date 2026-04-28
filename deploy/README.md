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
sudo bash deploy/install.sh image-to-text.fit

# After DNS propagates, verify
bash deploy/smoke_test.sh image-to-text.fit
```

The install script:
1. Installs nginx, certbot, python3, tesseract.
2. Clones the repo to `/opt/image-to-text`.
3. Creates a virtualenv and installs `requirements-prod.txt`.
4. Creates runtime dirs, log files, and auto-generates `SECRET_KEY`/`JWT_SECRET` if needed.
5. Runs Alembic migrations.
6. Installs an HTTP-only nginx stub, runs certbot for TLS, then installs the full SSL vhost.
7. Installs and enables `deploy/systemd/image-to-text.service` (gunicorn on `127.0.0.1:8000` as `www-data`).

The service runs as `www-data`. All files under `/opt/image-to-text` are owned by `www-data`.

To redeploy after a code push:

```
sudo bash /opt/image-to-text/deploy/redeploy.sh
```

---

## Recovering a downed site

If the site is down on an existing install (e.g. after a server reboot, bad deploy, or
permission corruption), run the recovery script as root:

```
sudo bash /opt/image-to-text/deploy/recover.sh
```

The script is idempotent and safe to run multiple times. It:
1. Stops the service.
2. Recreates `logs/` and `uploads/` directories and pre-creates log files.
3. Ensures `.env` exists and auto-generates secrets if placeholders are still present.
4. Fixes ownership (`chown -R www-data:www-data`) and permissions (`chmod 640 .env`).
5. Runs Alembic migrations.
6. Reinstalls the systemd unit file, reloads daemon, and starts the service.
7. Polls `http://127.0.0.1:8000/api/health` for up to 30 seconds and reports the result.

After recovery, run the full smoke test:

```
bash /opt/image-to-text/deploy/smoke_test.sh image-to-text.fit
```

