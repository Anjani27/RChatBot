"""Authentication service — password hashing and FastAPI dependencies."""
import hashlib
import os
from fastapi import Header, HTTPException, status
from app.repositories import user_repository as repo


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}.{key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its PBKDF2 hash."""
    try:
        salt_hex, key_hex = hashed.split(".")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return key.hex() == key_hex
    except Exception:
        return False


def get_current_user(authorization: str = Header(None)) -> str:
    """
    FastAPI dependency to extract and authenticate session token.
    Expects format: 'Bearer <session_id>'
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header",
        )

    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError()
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Use 'Bearer <token>'",
        )

    email = repo.get_session_user(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    return email
