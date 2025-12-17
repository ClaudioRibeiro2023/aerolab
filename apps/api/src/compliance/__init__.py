"""
Módulo de Compliance - LGPD/GDPR e Segurança.
"""

from .gdpr import (
    GDPRCompliance,
    PIIDetector,
    ConsentType,
    DataCategory,
    Consent,
    DataSubjectRequest,
    AuditLog,
    get_gdpr_compliance,
)

from .encryption import (
    EncryptionService,
    KeyManager,
    EncryptedData,
    encrypt_field,
    decrypt_field,
    get_encryption_service,
)

__all__ = [
    # GDPR/LGPD
    "GDPRCompliance",
    "PIIDetector",
    "ConsentType",
    "DataCategory",
    "Consent",
    "DataSubjectRequest",
    "AuditLog",
    "get_gdpr_compliance",
    # Encryption
    "EncryptionService",
    "KeyManager",
    "EncryptedData",
    "encrypt_field",
    "decrypt_field",
    "get_encryption_service",
]
