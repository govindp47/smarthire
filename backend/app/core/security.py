"""
Security utilities: password hashing, JWT tokens.
"""
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Optional
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # max 72 bytes kind of error
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")



def _normalize_password(password: str) -> str:
    # optional but safe: protects against unicode edge cases
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(_normalize_password(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(_normalize_password(password))


def create_access_token(subject: str | UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Subject (usually user_id)
        expires_delta: Token expiration time (default: from settings)
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject)  # Convert UUID to string
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
