# Fix for ModuleNotFoundError: No module named 'psycopg2'

## Problem Summary

The application was failing to start on Railway deployment with the following error:

```
ModuleNotFoundError: No module named 'psycopg2'
Traceback (most recent call last):
  File "/app/web/backend/app.py", line 85, in <module>
    init_db()
  File "/app/web/backend/database.py", line 138, in init_db
    Base.metadata.create_all(bind=get_engine())
  File "/app/web/backend/database.py", line 90, in get_engine
    _engine = create_engine(DATABASE_URL, **engine_kwargs)
  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/create.py", line 617, in create_engine
    dbapi = dbapi_meth(**dbapi_args)
  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/psycopg2.py", line 696, in import_dbapi
    import psycopg2
ModuleNotFoundError: No module named 'psycopg2'
```

## Root Cause

SQLAlchemy requires the `psycopg2` package to connect to PostgreSQL databases. The package was missing from both:
- `requirements.txt` (used by Railway via nixpacks.toml)
- `requirements-prod.txt` (used by Docker)

## Solution

Added `psycopg2-binary>=2.9.9` to both requirements files and PostgreSQL system libraries to the nixpacks.toml configuration.

### Files Modified

1. **requirements.txt**
   - Added `psycopg2-binary>=2.9.9` in the DATABASE section

2. **requirements-prod.txt**
   - Added `psycopg2-binary>=2.9.9` in the DATABASE section

3. **nixpacks.toml**
   - Added `postgresql` to the nixPkgs list for system-level PostgreSQL client libraries

## Why psycopg2-binary?

We use `psycopg2-binary` instead of `psycopg2` because:

1. **Easier Deployment**: Includes pre-compiled binaries, no C compiler needed
2. **Faster Installation**: No need to compile from source
3. **Cross-platform**: Works on Linux, macOS, and Windows
4. **Production-ready**: Officially recommended for stand-alone applications

## Testing

Verified that:
- `psycopg2-binary` installs successfully
- The package can be imported without errors
- Version installed: 2.9.11

## Expected Result

The application should now start successfully on Railway with PostgreSQL database connections working properly. The health checks should pass and the application should be accessible.

## Verification

After deployment, verify with:
```bash
curl https://your-app.railway.app/api/health
curl https://your-app.railway.app/api/ready
```

Both endpoints should return HTTP 200 status codes.
