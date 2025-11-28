"""
Database models for Receipt Extractor SaaS Platform
Implements Priority 1: MVP Backend Infrastructure
"""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Float,
    ForeignKey, Text, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan tiers"""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class User(Base):
    """User model with authentication and subscription info"""
    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)

    # Password Reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Profile
    full_name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)

    # Subscription
    plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)

    # Usage Tracking
    receipts_processed_month = Column(Integer, default=0)
    storage_used_bytes = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Relationships
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_plan', 'plan'),
        Index('idx_user_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', plan='{self.plan}')>"


class Receipt(Base):
    """Receipt extraction records"""
    __tablename__ = "receipts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # File Information
    filename = Column(String(255), nullable=False)
    image_url = Column(String(512), nullable=True)  # S3/storage URL
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Extraction Results
    extracted_data = Column(JSONB, nullable=True)  # Full receipt data as JSON
    store_name = Column(String(255), nullable=True, index=True)  # For searching
    total_amount = Column(Float, nullable=True)  # For analytics
    transaction_date = Column(DateTime, nullable=True, index=True)  # For filtering

    # Processing Metadata
    model_used = Column(String(100), nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Status
    status = Column(String(50), default='processing')  # processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="receipts")

    # Indexes
    __table_args__ = (
        Index('idx_receipt_user_id', 'user_id'),
        Index('idx_receipt_created_at', 'created_at'),
        Index('idx_receipt_store_name', 'store_name'),
        Index('idx_receipt_transaction_date', 'transaction_date'),
        Index('idx_receipt_status', 'status'),
    )

    def __repr__(self):
        return f"<Receipt(id={self.id}, user_id={self.user_id}, store='{self.store_name}')>"


class Subscription(Base):
    """Stripe subscription records"""
    __tablename__ = "subscriptions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Stripe Information
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_price_id = Column(String(255), nullable=True)

    # Subscription Details
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False)

    # Billing
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan}', status='{self.status}')>"


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # API Key
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed key
    key_prefix = Column(String(20), nullable=False)  # First few chars for display
    name = Column(String(255), nullable=True)  # User-friendly name

    # Usage
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, prefix='{self.key_prefix}', user_id={self.user_id})>"


class RefreshToken(Base):
    """JWT refresh tokens for authentication"""
    __tablename__ = "refresh_tokens"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Token
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Metadata
    device_info = Column(String(255), nullable=True)  # User agent, device type
    ip_address = Column(String(45), nullable=True)  # IPv6 support

    # Expiry
    expires_at = Column(DateTime, nullable=False, index=True)

    # Status
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    # Indexes
    __table_args__ = (
        Index('idx_refresh_token_user_id', 'user_id'),
        Index('idx_refresh_token_expires_at', 'expires_at'),
        Index('idx_refresh_token_revoked', 'revoked'),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"


class AuditLog(Base):
    """Audit log for security and compliance"""
    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User (nullable for anonymous actions)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Action Details
    action = Column(String(100), nullable=False, index=True)  # login, logout, create_receipt, etc.
    resource_type = Column(String(100), nullable=True)  # receipt, user, subscription
    resource_id = Column(UUID(as_uuid=True), nullable=True)

    # Request Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Additional Data
    metadata = Column(JSONB, nullable=True)  # Flexible additional info

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_audit_log_user_id', 'user_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
