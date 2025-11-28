# Priority 1: MVP Backend Infrastructure Implementation

This document describes the complete implementation of Priority 1 features for transforming the Receipt Extractor into a production-ready SaaS application.

## Overview

Priority 1 includes:
- ✅ **Database Setup**: PostgreSQL with comprehensive schema
- ✅ **User Management**: Registration, authentication, and authorization
- ✅ **Security Hardening**: JWT tokens, password hashing, rate limiting, input validation

## Architecture

### Database Layer

**Location**: `web-app/backend/database/`

#### Models (`database/models.py`)

1. **User**
   - UUID primary key
   - Email/password authentication
   - Subscription plan tracking
   - Monthly usage counters
   - Timestamps and audit fields

2. **Receipt**
   - JSONB storage for flexible extraction data
   - Indexed fields for searching (store_name, date, total)
   - File metadata and processing status
   - Model tracking and confidence scores

3. **Subscription**
   - Stripe integration fields
   - Subscription status and billing periods
   - Plan tier management

4. **APIKey**
   - Programmatic access tokens
   - Usage tracking and expiration

5. **RefreshToken**
   - JWT refresh token management
   - Device and IP tracking
   - Revocation support

6. **AuditLog**
   - Security and compliance logging
   - Action tracking with metadata
   - IP and user agent capture

#### Database Connection (`database/connection.py`)

- SQLAlchemy engine with connection pooling
- Session management with context managers
- Supports PostgreSQL (production) and SQLite (development)
- Utility functions for token cleanup and usage reset

**Environment Variables**:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/receipt_extractor
SQL_ECHO=false                    # Set to 'true' for SQL query logging
USE_SQLITE=false                  # Set to 'true' for dev SQLite
SERVERLESS=false                  # Set to 'true' for Lambda/serverless
```

### Authentication Layer

**Location**: `web-app/backend/auth/`

#### Password Hashing (`auth/password.py`)

- **Algorithm**: bcrypt with 12 rounds
- **Functions**:
  - `hash_password(password: str) -> str`
  - `verify_password(password: str, hash: str) -> bool`
  - `is_password_strong(password: str) -> tuple[bool, list[str]]`

**Password Requirements**:
- Minimum 8 characters
- Contains uppercase letter
- Contains lowercase letter
- Contains number
- Contains special character

#### JWT Tokens (`auth/jwt_handler.py`)

- **Algorithm**: HS256 (configurable)
- **Access Tokens**: 15-minute lifespan
- **Refresh Tokens**: 30-day lifespan, cryptographically secure

**Functions**:
- `create_access_token(user_id, email, is_admin) -> str`
- `create_refresh_token() -> tuple[str, str]`  # Returns token and hash
- `verify_access_token(token: str) -> Optional[Dict]`
- `verify_refresh_token(token: str, stored_hash: str) -> bool`
- `revoke_refresh_token(db, token: str) -> bool`

**Environment Variables**:
```bash
JWT_SECRET=your-secret-key-here   # MUST be set in production!
```

#### Security Decorators (`auth/decorators.py`)

Flask decorators for protecting routes:

1. **@require_auth**
   - Validates JWT access token
   - Loads user from database
   - Populates Flask's `g` object with user data

2. **@require_admin**
   - Requires admin privileges
   - Must be used with `@require_auth`

3. **@rate_limit(max_requests, window_seconds)**
   - Configurable rate limiting
   - Per-user or per-IP tracking
   - Returns 429 with retry-after header

4. **@require_plan(plan_name)**
   - Enforces subscription tier requirements
   - Plan hierarchy: free < pro < business < enterprise

5. **@check_usage_limit**
   - Enforces monthly processing limits
   - Auto-increments usage counter
   - Returns 429 when limit exceeded

**Default Usage Limits**:
- Free: 50 receipts/month
- Pro: 1,000 receipts/month
- Business: 10,000 receipts/month
- Enterprise: Unlimited

### Validation Layer

**Location**: `web-app/backend/validation/`

#### Pydantic Schemas (`validation/schemas.py`)

Comprehensive input validation for all API endpoints:

1. **UserRegisterSchema**
   - Email validation (with disposable email blocking)
   - Password strength enforcement
   - Optional profile fields

2. **UserLoginSchema**
   - Email and password validation

3. **ReceiptUploadSchema**
   - Model ID format validation
   - File type and size validation

4. **FileUploadValidation**
   - Allowed MIME types: JPEG, PNG, BMP, TIFF
   - Max file size: 10 MB
   - Magic byte verification (TODO)

5. **PaginationParams**
   - Page numbers (min: 1)
   - Per-page limits (1-100)

6. **ReceiptSearchSchema**
   - Search query validation
   - Date range validation
   - Amount range validation

## Database Schema

### Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    plan VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    receipts_processed_month INTEGER DEFAULT 0,
    storage_used_bytes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Receipts table
CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    image_url VARCHAR(512),
    extracted_data JSONB,
    store_name VARCHAR(255),
    total_amount FLOAT,
    transaction_date TIMESTAMP,
    model_used VARCHAR(100) NOT NULL,
    confidence_score FLOAT,
    status VARCHAR(50) DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_receipt_user_id ON receipts(user_id);
CREATE INDEX idx_receipt_created_at ON receipts(created_at);
CREATE INDEX idx_receipt_store_name ON receipts(store_name);
CREATE INDEX idx_receipt_transaction_date ON receipts(transaction_date);
```

### Indexes

All tables include strategic indexes for:
- Primary keys (UUID)
- Foreign keys
- Commonly searched/filtered fields
- Date ranges for analytics

## Security Features

### 1. Authentication & Authorization

- ✅ JWT access tokens (short-lived)
- ✅ JWT refresh tokens (long-lived, revocable)
- ✅ Bcrypt password hashing (12 rounds)
- ✅ Email verification tokens
- ✅ Password reset tokens
- ✅ Role-based access control (user/admin)

### 2. Input Validation

- ✅ Pydantic schemas for all inputs
- ✅ Email validation with disposable domain blocking
- ✅ Password strength requirements
- ✅ File type and size validation
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS prevention (output escaping)

### 3. Rate Limiting

- ✅ Configurable per-endpoint limits
- ✅ Per-user tracking (authenticated requests)
- ✅ Per-IP tracking (unauthenticated requests)
- ✅ Standard HTTP 429 responses
- ✅ Retry-After headers

**Note**: Current implementation uses in-memory storage. For production, migrate to Redis:

```python
# Production rate limiting with Redis
import redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

redis_client = redis.from_url(os.getenv('REDIS_URL'))
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=os.getenv('REDIS_URL')
)
```

### 4. Additional Security Measures

- ✅ CSRF protection (TODO: implement for web forms)
- ✅ Audit logging for all actions
- ✅ Secure session management
- ✅ API key support (hashed storage)

## Usage Examples

### 1. Initialize Database

```python
from database.connection import init_db

# Create all tables
init_db()
```

### 2. Create User with Authentication

```python
from database.connection import get_db_context
from database.models import User
from auth.password import hash_password

with get_db_context() as db:
    user = User(
        email='user@example.com',
        password_hash=hash_password('SecurePass123!'),
        full_name='John Doe',
        plan='free'
    )
    db.add(user)
    db.commit()
```

### 3. Authenticate User

```python
from database.connection import get_db_context
from database.models import User, RefreshToken
from auth.password import verify_password
from auth.jwt_handler import create_access_token, create_refresh_token

def login(email, password):
    with get_db_context() as db:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.password_hash):
            return None

        # Create tokens
        access_token = create_access_token(user.id, user.email, user.is_admin)
        refresh_token, token_hash = create_refresh_token()

        # Store refresh token
        refresh = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(refresh)
        db.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900  # 15 minutes
        }
```

### 4. Protect Flask Routes

```python
from flask import Flask, jsonify, g
from auth.decorators import require_auth, rate_limit, check_usage_limit

app = Flask(__name__)

@app.route('/api/receipts', methods=['POST'])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)  # 10 requests per minute
@check_usage_limit  # Check monthly quota
def create_receipt():
    user_id = g.user_id
    # ... process receipt ...
    return jsonify({'success': True})

@app.route('/api/admin/users', methods=['GET'])
@require_auth
@require_admin
def list_users():
    # Only admins can access
    return jsonify({'users': []})
```

### 5. Validate Input Data

```python
from validation import UserRegisterSchema
from pydantic import ValidationError

try:
    data = UserRegisterSchema(
        email='user@example.com',
        password='SecurePass123!',
        full_name='John Doe'
    )
    # Data is valid and sanitized
    print(data.email)  # user@example.com (lowercase)

except ValidationError as e:
    # Handle validation errors
    print(e.json())
```

## Installation

### Dependencies

```bash
pip install -r requirements.txt
```

**New dependencies added**:
```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0  # PostgreSQL driver
bcrypt>=4.0.0           # Password hashing
pyjwt>=2.8.0            # JWT tokens
pydantic>=2.0.0         # Input validation
python-dotenv>=1.0.0    # Environment variables
```

### Database Setup

```bash
# Install PostgreSQL (if not already installed)
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb receipt_extractor
sudo -u postgres createuser receipt_user -P  # Enter password

# Grant permissions
sudo -u postgres psql receipt_extractor
GRANT ALL PRIVILEGES ON DATABASE receipt_extractor TO receipt_user;
```

### Environment Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://receipt_user:your_password@localhost:5432/receipt_extractor

# JWT
JWT_SECRET=generate-a-secure-random-string-here

# Optional
SQL_ECHO=false
USE_SQLITE=false
```

**Generate secure JWT secret**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Testing

### Unit Tests

```bash
# Run all authentication tests
pytest tests/auth/ -v --cov=auth

# Run database tests
pytest tests/database/ -v --cov=database

# Run validation tests
pytest tests/validation/ -v --cov=validation
```

### Integration Tests

```bash
# Test full authentication flow
pytest tests/integration/test_auth_flow.py -v

# Test protected routes
pytest tests/integration/test_protected_routes.py -v
```

## Migration Guide

### From Current Flask App to Priority 1

1. **Install dependencies**:
   ```bash
   pip install -r requirements-priority1.txt
   ```

2. **Set up database**:
   ```bash
   python -c "from database.connection import init_db; init_db()"
   ```

3. **Update existing routes**:
   - Add `@require_auth` to protected endpoints
   - Add `@rate_limit()` to prevent abuse
   - Use validation schemas for input

4. **Migrate existing data** (if any):
   ```bash
   python scripts/migrate_to_priority1.py
   ```

## Performance Considerations

- **Database Connection Pooling**: Configured via SQLAlchemy
- **Index Strategy**: All FK and frequently queried fields indexed
- **JSONB for Flexibility**: Receipt data stored as JSONB for fast queries
- **Rate Limiting**: Prevents abuse and ensures fair usage

## Security Checklist

- [x] Password hashing with bcrypt
- [x] JWT token-based authentication
- [x] Refresh token rotation
- [x] Input validation with Pydantic
- [x] Rate limiting decorators
- [x] SQL injection prevention (ORM)
- [x] Audit logging
- [ ] CSRF protection (web forms)
- [ ] File upload malware scanning
- [ ] Security headers (HSTS, CSP, etc.)
- [ ] API request signing
- [ ] IP whitelist/blacklist

## Next Steps (Priority 2+)

1. **Stripe Integration**
   - Payment processing
   - Subscription management
   - Webhook handling

2. **Email Service**
   - Email verification
   - Password reset emails
   - Usage alerts

3. **File Storage**
   - S3/MinIO integration
   - Presigned URLs
   - CDN integration

4. **Monitoring**
   - Application metrics
   - Error tracking (Sentry)
   - Performance monitoring

5. **CI/CD**
   - Automated testing
   - Deployment pipelines
   - Database migrations (Alembic)

## Support

For questions or issues:
1. Check this documentation
2. Review code comments
3. Run tests for examples
4. Create an issue in the repository
