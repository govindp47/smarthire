"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # Subject (user_id)
    exp: int  # Expiration time


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class SignupRequest(BaseModel):
    """Signup request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    company_name: str | None = Field(None, max_length=255)
