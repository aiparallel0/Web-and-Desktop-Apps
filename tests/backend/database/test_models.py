"""
Test suite for database models
Tests coverage for web-app/backend/database/models.py
"""
import pytest
import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web-app', 'backend'))

from database.models import (
    Base,
    User,
    Receipt,
    Subscription,
    APIKey,
    RefreshToken,
    AuditLog,
    SubscriptionPlan,
    SubscriptionStatus
)


class TestUserModel:
    """Test the User model"""

    def test_user_creation(self, db_session):
        """Test creating a user with all fields"""
        user = User(
            email="newuser@example.com",
            password_hash="hashed_password",
            full_name="New User",
            company="Test Company",
            plan=SubscriptionPlan.FREE,
            is_active=True,
            is_admin=False,
            email_verified=False
        )

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_email_constraint(self, db_session, test_user):
        """Test that duplicate emails are rejected"""
        duplicate_user = User(
            email=test_user.email,  # Same email
            password_hash="different_hash"
        )

        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_default_values(self, db_session):
        """Test that user default values are set correctly"""
        user = User(
            email="defaults@example.com",
            password_hash="hashed"
        )

        db_session.add(user)
        db_session.commit()

        assert user.plan == SubscriptionPlan.FREE
        assert user.is_active is True
        assert user.is_admin is False
        assert user.email_verified is False
        assert user.receipts_processed_month == 0
        assert user.storage_used_bytes == 0

    def test_user_relationships(self, db_session, test_user):
        """Test that user relationships work"""
        # Add a receipt
        receipt = Receipt(
            user_id=test_user.id,
            filename="test.jpg",
            model_used="easyocr"
        )
        db_session.add(receipt)
        db_session.commit()

        # Verify relationship
        db_session.refresh(test_user)
        assert len(test_user.receipts) == 1
        assert test_user.receipts[0].filename == "test.jpg"

    def test_user_repr(self, db_session, test_user):
        """Test user string representation"""
        repr_str = repr(test_user)

        assert "User" in repr_str
        assert str(test_user.id) in repr_str
        assert test_user.email in repr_str
        assert test_user.plan.value in repr_str

    def test_user_subscription_plan_enum(self, db_session):
        """Test all subscription plan enum values"""
        plans = [
            SubscriptionPlan.FREE,
            SubscriptionPlan.PRO,
            SubscriptionPlan.BUSINESS,
            SubscriptionPlan.ENTERPRISE
        ]

        for plan in plans:
            user = User(
                email=f"{plan.value}@example.com",
                password_hash="hashed",
                plan=plan
            )
            db_session.add(user)

        db_session.commit()

        users = db_session.query(User).filter(User.email.like('%@example.com')).all()
        assert len(users) >= 4

    def test_user_password_reset_fields(self, db_session):
        """Test password reset token and expiry fields"""
        user = User(
            email="reset@example.com",
            password_hash="hashed",
            password_reset_token="reset_token_123",
            password_reset_expires=datetime.utcnow() + timedelta(hours=1)
        )

        db_session.add(user)
        db_session.commit()

        assert user.password_reset_token == "reset_token_123"
        assert user.password_reset_expires > datetime.utcnow()

    def test_user_email_verification_fields(self, db_session):
        """Test email verification fields"""
        user = User(
            email="verify@example.com",
            password_hash="hashed",
            email_verified=False,
            email_verification_token="verify_token_456"
        )

        db_session.add(user)
        db_session.commit()

        assert user.email_verified is False
        assert user.email_verification_token == "verify_token_456"

    def test_user_stripe_customer_id(self, db_session):
        """Test stripe customer ID field"""
        user = User(
            email="stripe@example.com",
            password_hash="hashed",
            stripe_customer_id="cus_123456789"
        )

        db_session.add(user)
        db_session.commit()

        assert user.stripe_customer_id == "cus_123456789"

    def test_user_last_login_tracking(self, db_session, test_user):
        """Test last login timestamp tracking"""
        login_time = datetime.utcnow()
        test_user.last_login_at = login_time
        db_session.commit()

        db_session.refresh(test_user)
        assert test_user.last_login_at is not None


class TestReceiptModel:
    """Test the Receipt model"""

    def test_receipt_creation(self, db_session, test_user):
        """Test creating a receipt"""
        receipt = Receipt(
            user_id=test_user.id,
            filename="receipt.jpg",
            model_used="easyocr",
            extracted_data={"total": 25.99},
            status="completed"
        )

        db_session.add(receipt)
        db_session.commit()

        assert receipt.id is not None
        assert receipt.user_id == test_user.id
        assert receipt.created_at is not None

    def test_receipt_user_foreign_key(self, db_session, test_user):
        """Test receipt user foreign key relationship"""
        receipt = Receipt(
            user_id=test_user.id,
            filename="test.jpg",
            model_used="easyocr"
        )

        db_session.add(receipt)
        db_session.commit()

        # Verify foreign key works
        assert receipt.user.email == test_user.email

    def test_receipt_cascade_delete(self, db_session, test_user):
        """Test that deleting user cascades to receipts"""
        receipt = Receipt(
            user_id=test_user.id,
            filename="cascade_test.jpg",
            model_used="easyocr"
        )

        db_session.add(receipt)
        db_session.commit()

        receipt_id = receipt.id

        # Delete user
        db_session.delete(test_user)
        db_session.commit()

        # Receipt should also be deleted
        deleted_receipt = db_session.query(Receipt).filter(Receipt.id == receipt_id).first()
        assert deleted_receipt is None

    def test_receipt_jsonb_extracted_data(self, db_session, test_user):
        """Test JSONB field for extracted data"""
        complex_data = {
            "store_name": "Test Store",
            "items": [
                {"name": "Item 1", "price": 10.99},
                {"name": "Item 2", "price": 15.50}
            ],
            "total": 26.49,
            "date": "2024-01-15"
        }

        receipt = Receipt(
            user_id=test_user.id,
            filename="complex.jpg",
            model_used="donut",
            extracted_data=complex_data
        )

        db_session.add(receipt)
        db_session.commit()

        # Verify JSONB storage and retrieval
        db_session.refresh(receipt)
        assert receipt.extracted_data["store_name"] == "Test Store"
        assert len(receipt.extracted_data["items"]) == 2
        assert receipt.extracted_data["total"] == 26.49

    def test_receipt_indexes(self, db_session, test_user):
        """Test that receipt indexes are working"""
        # Create multiple receipts
        for i in range(5):
            receipt = Receipt(
                user_id=test_user.id,
                filename=f"receipt_{i}.jpg",
                model_used="easyocr",
                store_name="Test Store",
                status="completed"
            )
            db_session.add(receipt)

        db_session.commit()

        # Query using indexed columns should be fast
        receipts = db_session.query(Receipt).filter(
            Receipt.user_id == test_user.id,
            Receipt.status == "completed"
        ).all()

        assert len(receipts) == 5

    def test_receipt_processing_metadata(self, db_session, test_user):
        """Test receipt processing metadata fields"""
        receipt = Receipt(
            user_id=test_user.id,
            filename="metadata.jpg",
            model_used="donut",
            processing_time_seconds=3.5,
            confidence_score=0.92
        )

        db_session.add(receipt)
        db_session.commit()

        assert receipt.processing_time_seconds == 3.5
        assert receipt.confidence_score == 0.92

    def test_receipt_status_field(self, db_session, test_user):
        """Test receipt status field"""
        statuses = ["processing", "completed", "failed"]

        for status in statuses:
            receipt = Receipt(
                user_id=test_user.id,
                filename=f"{status}.jpg",
                model_used="easyocr",
                status=status
            )
            db_session.add(receipt)

        db_session.commit()

        # Verify all statuses were saved
        for status in statuses:
            receipt = db_session.query(Receipt).filter(
                Receipt.status == status
            ).first()
            assert receipt is not None

    def test_receipt_error_message(self, db_session, test_user):
        """Test receipt error message field"""
        receipt = Receipt(
            user_id=test_user.id,
            filename="failed.jpg",
            model_used="easyocr",
            status="failed",
            error_message="Model loading failed"
        )

        db_session.add(receipt)
        db_session.commit()

        assert receipt.error_message == "Model loading failed"

    def test_receipt_repr(self, db_session, test_receipt):
        """Test receipt string representation"""
        repr_str = repr(test_receipt)

        assert "Receipt" in repr_str
        assert str(test_receipt.id) in repr_str


class TestSubscriptionModel:
    """Test the Subscription model"""

    def test_subscription_creation(self, db_session, test_user):
        """Test creating a subscription"""
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_123456789",
            plan=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE
        )

        db_session.add(subscription)
        db_session.commit()

        assert subscription.id is not None
        assert subscription.stripe_subscription_id == "sub_123456789"

    def test_subscription_status_enum(self, db_session, test_user):
        """Test subscription status enum values"""
        statuses = [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELED,
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.TRIALING
        ]

        for idx, status in enumerate(statuses):
            subscription = Subscription(
                user_id=test_user.id,
                stripe_subscription_id=f"sub_{idx}",
                plan=SubscriptionPlan.PRO,
                status=status
            )
            db_session.add(subscription)

        db_session.commit()

        # Verify all statuses
        subs = db_session.query(Subscription).filter(
            Subscription.user_id == test_user.id
        ).all()
        assert len(subs) == 4

    def test_subscription_unique_stripe_id(self, db_session, test_user):
        """Test that stripe subscription ID is unique"""
        sub1 = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_unique",
            plan=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE
        )
        db_session.add(sub1)
        db_session.commit()

        # Try to create another with same stripe ID
        sub2 = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_unique",
            plan=SubscriptionPlan.BUSINESS,
            status=SubscriptionStatus.ACTIVE
        )
        db_session.add(sub2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_subscription_billing_fields(self, db_session, test_user):
        """Test subscription billing period fields"""
        now = datetime.utcnow()
        period_end = now + timedelta(days=30)

        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_billing",
            plan=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=period_end,
            cancel_at_period_end=False
        )

        db_session.add(subscription)
        db_session.commit()

        assert subscription.current_period_start is not None
        assert subscription.current_period_end > subscription.current_period_start
        assert subscription.cancel_at_period_end is False

    def test_subscription_repr(self, db_session, test_user):
        """Test subscription string representation"""
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_repr",
            plan=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE
        )
        db_session.add(subscription)
        db_session.commit()

        repr_str = repr(subscription)
        assert "Subscription" in repr_str
        assert "pro" in repr_str
        assert "active" in repr_str


class TestAPIKeyModel:
    """Test the APIKey model"""

    def test_api_key_creation(self, db_session, test_user):
        """Test creating an API key"""
        api_key = APIKey(
            user_id=test_user.id,
            key_hash="hashed_key_123",
            key_prefix="sk_test",
            name="Test API Key"
        )

        db_session.add(api_key)
        db_session.commit()

        assert api_key.id is not None
        assert api_key.key_hash == "hashed_key_123"
        assert api_key.key_prefix == "sk_test"

    def test_api_key_hash_storage(self, db_session, test_user):
        """Test that only hash is stored, not actual key"""
        import hashlib

        actual_key = "sk_test_actual_key_12345"
        key_hash = hashlib.sha256(actual_key.encode()).hexdigest()

        api_key = APIKey(
            user_id=test_user.id,
            key_hash=key_hash,
            key_prefix="sk_test",
            name="Hashed Key"
        )

        db_session.add(api_key)
        db_session.commit()

        # Verify only hash is stored
        assert api_key.key_hash == key_hash
        assert actual_key not in api_key.key_hash

    def test_api_key_prefix_display(self, db_session, test_user):
        """Test API key prefix for display purposes"""
        api_key = APIKey(
            user_id=test_user.id,
            key_hash="hash123",
            key_prefix="sk_live_abc",
            name="Live Key"
        )

        db_session.add(api_key)
        db_session.commit()

        # Prefix can be shown to user
        assert api_key.key_prefix == "sk_live_abc"

    def test_api_key_usage_tracking(self, db_session, test_user):
        """Test API key usage tracking"""
        api_key = APIKey(
            user_id=test_user.id,
            key_hash="hash456",
            key_prefix="sk_test",
            usage_count=0
        )

        db_session.add(api_key)
        db_session.commit()

        # Simulate usage
        api_key.usage_count += 1
        api_key.last_used_at = datetime.utcnow()
        db_session.commit()

        db_session.refresh(api_key)
        assert api_key.usage_count == 1
        assert api_key.last_used_at is not None

    def test_api_key_expiry(self, db_session, test_user):
        """Test API key expiration"""
        future_expiry = datetime.utcnow() + timedelta(days=30)

        api_key = APIKey(
            user_id=test_user.id,
            key_hash="hash789",
            key_prefix="sk_test",
            expires_at=future_expiry
        )

        db_session.add(api_key)
        db_session.commit()

        assert api_key.expires_at > datetime.utcnow()

    def test_api_key_repr(self, db_session, test_user):
        """Test API key string representation"""
        api_key = APIKey(
            user_id=test_user.id,
            key_hash="hash_repr",
            key_prefix="sk_test_xyz"
        )
        db_session.add(api_key)
        db_session.commit()

        repr_str = repr(api_key)
        assert "APIKey" in repr_str
        assert "sk_test_xyz" in repr_str


class TestRefreshTokenModel:
    """Test the RefreshToken model"""

    def test_refresh_token_creation(self, db_session, test_user):
        """Test creating a refresh token"""
        expires = datetime.utcnow() + timedelta(days=30)

        refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash="hashed_token_123",
            expires_at=expires,
            device_info="Chrome/MacOS",
            ip_address="192.168.1.1"
        )

        db_session.add(refresh_token)
        db_session.commit()

        assert refresh_token.id is not None
        assert refresh_token.token_hash == "hashed_token_123"

    def test_refresh_token_expiry(self, db_session, test_user):
        """Test refresh token expiration"""
        expires = datetime.utcnow() + timedelta(days=30)

        refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash="hash_expiry",
            expires_at=expires
        )

        db_session.add(refresh_token)
        db_session.commit()

        # Check not expired
        assert refresh_token.expires_at > datetime.utcnow()

    def test_refresh_token_revocation(self, db_session, test_user):
        """Test refresh token revocation"""
        refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash="hash_revoke",
            expires_at=datetime.utcnow() + timedelta(days=30),
            revoked=False
        )

        db_session.add(refresh_token)
        db_session.commit()

        # Revoke token
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        db_session.commit()

        db_session.refresh(refresh_token)
        assert refresh_token.revoked is True
        assert refresh_token.revoked_at is not None

    def test_refresh_token_device_info(self, db_session, test_user):
        """Test refresh token device information"""
        refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash="hash_device",
            expires_at=datetime.utcnow() + timedelta(days=30),
            device_info="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
            ip_address="203.0.113.42"
        )

        db_session.add(refresh_token)
        db_session.commit()

        assert "iPhone" in refresh_token.device_info
        assert refresh_token.ip_address == "203.0.113.42"

    def test_refresh_token_repr(self, db_session, test_user):
        """Test refresh token string representation"""
        refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash="hash_repr",
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(refresh_token)
        db_session.commit()

        repr_str = repr(refresh_token)
        assert "RefreshToken" in repr_str
        assert "revoked=False" in repr_str


class TestAuditLogModel:
    """Test the AuditLog model"""

    def test_audit_log_creation(self, db_session, test_user):
        """Test creating an audit log entry"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="login",
            resource_type="user",
            resource_id=test_user.id,
            ip_address="192.168.1.1",
            success=True
        )

        db_session.add(audit_log)
        db_session.commit()

        assert audit_log.id is not None
        assert audit_log.action == "login"
        assert audit_log.success is True

    def test_audit_log_nullable_user(self, db_session):
        """Test audit log with anonymous/null user"""
        audit_log = AuditLog(
            user_id=None,  # Anonymous action
            action="failed_login_attempt",
            ip_address="203.0.113.42",
            success=False,
            error_message="Invalid credentials"
        )

        db_session.add(audit_log)
        db_session.commit()

        assert audit_log.user_id is None
        assert audit_log.success is False

    def test_audit_log_jsonb_metadata(self, db_session, test_user):
        """Test audit log JSONB metadata field"""
        metadata = {
            "previous_email": "old@example.com",
            "new_email": "new@example.com",
            "changed_fields": ["email", "full_name"]
        }

        audit_log = AuditLog(
            user_id=test_user.id,
            action="update_profile",
            resource_type="user",
            resource_id=test_user.id,
            metadata=metadata,
            success=True
        )

        db_session.add(audit_log)
        db_session.commit()

        # Verify JSONB storage
        db_session.refresh(audit_log)
        assert audit_log.metadata["previous_email"] == "old@example.com"
        assert len(audit_log.metadata["changed_fields"]) == 2

    def test_audit_log_request_metadata(self, db_session, test_user):
        """Test audit log request metadata fields"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="create_receipt",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        db_session.add(audit_log)
        db_session.commit()

        assert audit_log.ip_address == "192.168.1.100"
        assert "Windows" in audit_log.user_agent

    def test_audit_log_error_tracking(self, db_session, test_user):
        """Test audit log error message tracking"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="process_receipt",
            success=False,
            error_message="Model loading failed: out of memory"
        )

        db_session.add(audit_log)
        db_session.commit()

        assert audit_log.success is False
        assert "out of memory" in audit_log.error_message

    def test_audit_log_repr(self, db_session, test_user):
        """Test audit log string representation"""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="test_action"
        )
        db_session.add(audit_log)
        db_session.commit()

        repr_str = repr(audit_log)
        assert "AuditLog" in repr_str
        assert "test_action" in repr_str


class TestModelRelationships:
    """Test relationships between models"""

    def test_user_to_receipts_relationship(self, db_session, test_user):
        """Test one-to-many relationship from User to Receipts"""
        # Create multiple receipts
        for i in range(3):
            receipt = Receipt(
                user_id=test_user.id,
                filename=f"receipt_{i}.jpg",
                model_used="easyocr"
            )
            db_session.add(receipt)

        db_session.commit()
        db_session.refresh(test_user)

        assert len(test_user.receipts) >= 3

    def test_user_to_subscriptions_relationship(self, db_session, test_user):
        """Test one-to-many relationship from User to Subscriptions"""
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_rel_test",
            plan=SubscriptionPlan.PRO,
            status=SubscriptionStatus.ACTIVE
        )
        db_session.add(subscription)
        db_session.commit()

        db_session.refresh(test_user)
        assert len(test_user.subscriptions) >= 1

    def test_user_to_api_keys_relationship(self, db_session, test_user):
        """Test one-to-many relationship from User to APIKeys"""
        api_key = APIKey(
            user_id=test_user.id,
            key_hash="hash_rel",
            key_prefix="sk_test"
        )
        db_session.add(api_key)
        db_session.commit()

        db_session.refresh(test_user)
        assert len(test_user.api_keys) >= 1

    def test_cascade_delete_receipts(self, db_session):
        """Test cascade delete from User to Receipts"""
        from database.models import SubscriptionPlan

        # Create user with receipts
        user = User(
            email="cascade@example.com",
            password_hash="hash",
            plan=SubscriptionPlan.FREE
        )
        db_session.add(user)
        db_session.commit()

        receipt = Receipt(
            user_id=user.id,
            filename="cascade.jpg",
            model_used="easyocr"
        )
        db_session.add(receipt)
        db_session.commit()

        receipt_id = receipt.id

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Receipt should be deleted
        deleted_receipt = db_session.query(Receipt).filter(Receipt.id == receipt_id).first()
        assert deleted_receipt is None
