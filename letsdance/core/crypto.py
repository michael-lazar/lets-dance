from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from django.utils import timezone


def load_private_key(key: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key))


def load_public_key(key: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(key))


def generate_private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


def dump_private_key(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()


def dump_public_key(key: Ed25519PublicKey) -> str:
    return key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def verify_signature(signature: str, key: str, data: bytes) -> bool:
    public_key = load_public_key(key)
    try:
        public_key.verify(bytes.fromhex(signature), data)
    except InvalidSignature:
        return False
    else:
        return True


def get_valid_public_key_endings() -> tuple[str, str]:
    now = timezone.now()
    return f"ed{now.year}", f"ed{now.year + 1}"


def validate_public_key(key: str) -> bool:
    return key.endswith(get_valid_public_key_endings())
