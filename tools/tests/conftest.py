import sys
from pathlib import Path
import pytest
import os
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Fix: Navigate up 3 levels from tests/ -> tools/ -> project_root
# Structure: project_root/tools/tests/conftest.py
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
# Add web/backend for database and auth imports (backwards compatibility)
sys.path.insert(0, str(project_root / 'web' / 'backend'))

# Export project_root for use in all test modules (fixes Windows path issues)
pytest.project_root = project_root

# Original fixtures
@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Reset all global singletons and module-level caches for test isolation.
    This fixture runs automatically before each test to ensure clean state.
    """
    yield

    # Reset OCR configuration singletons
    try:
        from shared.models.config import reset_ocr_config
        reset_ocr_config()
    except ImportError:
        pass

    # Reset OCR module cache
    try:
        import shared.models.ocr as ocr_module
        ocr_module._ocr_config = None
    except (ImportError, AttributeError):
        pass

    # Reset engine module cache
    try:
        import shared.models.engine as engine_module
        if hasattr(engine_module, '_finetuning_torch'):
            engine_module._finetuning_torch = None
    except (ImportError, AttributeError):
        pass

@pytest.fixture
def sample_receipt_data():
    return {
        "store": {
            "name": "Sample Store",
            "address": "123 Main St, City, State 12345",
            "phone": "(555) 123-4567"
        },
        "date": "2024-01-15",
        "items": [
            {
                "name": "Product A",
                "quantity": 2,
                "unit_price": 5.99,
                "total_price": 11.98
            },
            {
                "name": "Product B",
                "quantity": 1,
                "unit_price": 3.49,
                "total_price": 3.49
            }
        ],
        "totals": {
            "subtotal": 15.47,
            "tax": 1.24,
            "total": 16.71
        },
        "payment_method": "Credit Card",
        "category": "grocery"
    }

@pytest.fixture
def test_data_dir():
    return project_root / 'test_data'

@pytest.fixture
def sample_receipts_dir(test_data_dir):
    return test_data_dir / 'receipts'

@pytest.fixture
def expected_outputs_dir(test_data_dir):
    return test_data_dir / 'expected_outputs'

# Database fixtures
@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite database engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a database session for testing"""
    from database.models import Base

    # Create all tables
    Base.metadata.create_all(db_engine)

    # Create session
    Session = scoped_session(sessionmaker(bind=db_engine))
    session = Session()

    yield session

    # Cleanup
    session.close()
    Session.remove()
    Base.metadata.drop_all(db_engine)

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from database.models import User, SubscriptionPlan

    # Import password hashing - handle both locations
    try:
        from auth.password import hash_password
    except ImportError:
        # Mock hash if module not available
        def hash_password(pwd):
            import bcrypt
            salt = bcrypt.gensalt(rounds=4)  # Use fewer rounds for tests
            return bcrypt.hashpw(pwd.encode('utf-8'), salt).decode('utf-8')

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        full_name="Test User",
        plan=SubscriptionPlan.FREE,
        is_active=True,
        is_admin=False,
        email_verified=True,
        receipts_processed_month=0,
        storage_used_bytes=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user"""
    from database.models import User, SubscriptionPlan

    try:
        from auth.password import hash_password
    except ImportError:
        def hash_password(pwd):
            import bcrypt
            salt = bcrypt.gensalt(rounds=4)
            return bcrypt.hashpw(pwd.encode('utf-8'), salt).decode('utf-8')

    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        full_name="Admin User",
        plan=SubscriptionPlan.ENTERPRISE,
        is_active=True,
        is_admin=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_receipt(db_session, test_user):
    """Create a test receipt"""
    from database.models import Receipt

    receipt = Receipt(
        id=uuid.uuid4(),
        user_id=test_user.id,
        filename="test_receipt.jpg",
        image_url="https://example.com/receipts/test.jpg",
        file_size_bytes=102400,
        mime_type="image/jpeg",
        extracted_data={
            "store_name": "Test Store",
            "total": 25.99,
            "date": "2024-01-15"
        },
        store_name="Test Store",
        total_amount=25.99,
        transaction_date=datetime(2024, 1, 15),
        model_used="easyocr",
        processing_time_seconds=2.5,
        confidence_score=0.95,
        status="completed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    return receipt

@pytest.fixture
def flask_app():
    """Create Flask app for testing"""
    os.environ['TESTING'] = 'true'
    os.environ['USE_SQLITE'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

    # Import app - will be used in app tests
    try:
        from app import app
        app.config['TESTING'] = True
        return app
    except ImportError:
        # Return None if app can't be imported
        return None

@pytest.fixture
def client(flask_app):
    """Create test client"""
    if flask_app:
        return flask_app.test_client()
    return None

@pytest.fixture
def auth_token(test_user):
    """Create authentication token for test user"""
    try:
        from auth.jwt_handler import create_access_token
        return create_access_token(str(test_user.id), test_user.email, test_user.is_admin)
    except ImportError:
        return None

@pytest.fixture
def auth_headers(auth_token):
    """Create authentication headers"""
    if auth_token:
        return {'Authorization': f'Bearer {auth_token}'}
    return {}

@pytest.fixture
def admin_auth_token(test_admin_user):
    """Create authentication token for admin user"""
    try:
        from auth.jwt_handler import create_access_token
        return create_access_token(str(test_admin_user.id), test_admin_user.email, test_admin_user.is_admin)
    except ImportError:
        return None

@pytest.fixture
def admin_auth_headers(admin_auth_token):
    """Create admin authentication headers"""
    if admin_auth_token:
        return {'Authorization': f'Bearer {admin_auth_token}'}
    return {}
