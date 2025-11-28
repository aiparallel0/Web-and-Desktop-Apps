"""
Pydantic validation schemas for API input validation
Implements Priority 1: Security Hardening - Input Validation
"""
from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import Optional, List
from datetime import datetime
import re


class UserRegisterSchema(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User's email address")
    password: constr(min_length=8, max_length=128) = Field(..., description="User's password")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    company: Optional[str] = Field(None, max_length=255, description="Company name")

    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError('Password must contain at least one special character')

        return v

    @validator('email')
    def email_not_disposable(cls, v):
        """Block common disposable email domains"""
        disposable_domains = [
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'mailinator.com', 'throwaway.email'
        ]

        domain = v.split('@')[1].lower()
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses are not allowed')

        return v.lower()


class UserLoginSchema(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, max_length=128, description="User's password")


class RefreshTokenSchema(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequestSchema(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetSchema(BaseModel):
    """Schema for password reset"""
    token: str = Field(..., description="Password reset token")
    new_password: constr(min_length=8, max_length=128) = Field(..., description="New password")

    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')

        return v


class ReceiptUploadSchema(BaseModel):
    """Schema for receipt upload"""
    model_id: Optional[str] = Field(None, max_length=100, description="Model to use for extraction")

    @validator('model_id')
    def validate_model_id(cls, v):
        """Validate model ID format"""
        if v is None:
            return v

        # Allow alphanumeric, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid model ID format')

        return v


class ReceiptUpdateSchema(BaseModel):
    """Schema for receipt update"""
    extracted_data: Optional[dict] = Field(None, description="Updated extraction data")
    status: Optional[str] = Field(None, description="Receipt status")

    @validator('status')
    def validate_status(cls, v):
        """Validate status values"""
        if v is None:
            return v

        valid_statuses = ['processing', 'completed', 'failed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')

        return v


class APIKeyCreateSchema(BaseModel):
    """Schema for creating API key"""
    name: str = Field(..., min_length=1, max_length=255, description="API key name")

    @validator('name')
    def validate_name(cls, v):
        """Validate API key name"""
        # Remove extra whitespace
        v = ' '.join(v.split())

        if len(v) < 1:
            raise ValueError('Name cannot be empty')

        return v


class FileUploadValidation:
    """Validation for file uploads"""

    # Allowed image MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/bmp',
        'image/tiff',
        'image/tif'
    }

    # Maximum file size (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @classmethod
    def validate_image(cls, file_size: int, mime_type: str) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded image file

        Args:
            file_size: Size of file in bytes
            mime_type: MIME type of file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size > cls.MAX_FILE_SIZE:
            return False, f'File size exceeds maximum of {cls.MAX_FILE_SIZE // (1024*1024)}MB'

        if mime_type not in cls.ALLOWED_MIME_TYPES:
            return False, f'Invalid file type. Allowed types: {", ".join(cls.ALLOWED_MIME_TYPES)}'

        return True, None


class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page number"""
        return (self.page - 1) * self.per_page


class DateRangeFilter(BaseModel):
    """Schema for date range filtering"""
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    @validator('end_date')
    def end_after_start(cls, v, values):
        """Validate end date is after start date"""
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')

        return v


class ReceiptSearchSchema(BaseModel):
    """Schema for receipt search"""
    query: Optional[str] = Field(None, max_length=255, description="Search query")
    store_name: Optional[str] = Field(None, max_length=255, description="Filter by store name")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum total amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum total amount")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    @validator('max_amount')
    def max_after_min(cls, v, values):
        """Validate max amount is greater than min amount"""
        if v and values.get('min_amount') and v < values['min_amount']:
            raise ValueError('Maximum amount must be greater than minimum amount')

        return v
