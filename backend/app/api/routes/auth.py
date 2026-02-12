"""
Authentication routes: signup, login.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import Token, LoginRequest, SignupRequest, User as UserSchema
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()


@router.post("/signup", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new user account.
    
    - **email**: Valid email address (unique)
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **company_name**: Optional company name
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == signup_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=signup_data.email,
        hashed_password=get_password_hash(signup_data.password),
        full_name=signup_data.full_name,
        company_name=signup_data.company_name,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Login with email and password.
    
    Returns JWT access token.
    
    - **email**: Registered email address
    - **password**: User password
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(subject=user.id)
    
    return Token(access_token=access_token, token_type="bearer")


# Import here to avoid circular dependency
from app.api.deps import get_current_user

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get current user information (protected route).
    
    Requires: Bearer token in Authorization header
    """
    return current_user

