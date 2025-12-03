"""
=============================================================================
INTEGRATIONS MODULE - External API Integrations
=============================================================================

This module provides integrations with external AI services.

Components:
- huggingface_api.py: HuggingFace Inference API integration
- encryption.py: Token and credential encryption utilities

=============================================================================
"""

from .huggingface_api import HuggingFaceInference, get_hf_inference
from .encryption import CredentialEncryption, encrypt_token, decrypt_token

__all__ = [
    'HuggingFaceInference',
    'get_hf_inference',
    'CredentialEncryption',
    'encrypt_token',
    'decrypt_token',
]
