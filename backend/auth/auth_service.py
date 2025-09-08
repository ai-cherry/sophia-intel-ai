"""
Authentication Service for Sophia AI Dashboard
Implements JWT-based authentication with role-based access control
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    id: str
    email: str
    name: str
    role: str
    permissions: list[str]
    is_active: bool = True
    created_at: datetime
    last_login: datetime | None = None

class UserInDB(User):
    hashed_password: str

class LoginCredentials(BaseModel):
    email: str
    password: str

class TokenData(BaseModel):
    token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Role-based permissions
ROLE_PERMISSIONS = {
    "executive": [
        "dashboard:executive:read",
        "dashboard:financial:read",
        "dashboard:strategic:read",
        "analytics:all:read",
        "users:all:read",
        "system:health:read",
    ],
    "manager": [
        "dashboard:team:read",
        "dashboard:projects:read",
        "dashboard:projects:write",
        "analytics:team:read",
        "users:team:read",
        "system:health:read",
    ],
    "analyst": [
        "dashboard:analytics:read",
        "dashboard:public:read",
        "data:anonymized:read",
        "reports:generate",
        "system:health:read",
    ],
    "viewer": ["dashboard:public:read", "system:health:read"],
}

# In-memory user store (replace with database in production)
USERS_DB: dict[str, UserInDB] = {
    "admin@sophia-intel.ai": UserInDB(
        id="admin-001",
        email="admin@sophia-intel.ai",
        name="System Administrator",
        role="executive",
        permissions=ROLE_PERMISSIONS["executive"],
        hashed_password=pwd_context.hash("admin123"),
        created_at=datetime.utcnow(),
    ),
    "ceo@sophia-intel.ai": UserInDB(
        id="ceo-001",
        email="ceo@sophia-intel.ai",
        name="CEO",
        role="executive",
        permissions=ROLE_PERMISSIONS["executive"],
        hashed_password=pwd_context.hash("ceo123"),
        created_at=datetime.utcnow(),
    ),
    "manager@sophia-intel.ai": UserInDB(
        id="mgr-001",
        email="manager@sophia-intel.ai",
        name="Team Manager",
        role="manager",
        permissions=ROLE_PERMISSIONS["manager"],
        hashed_password=pwd_context.hash("manager123"),
        created_at=datetime.utcnow(),
    ),
    "analyst@sophia-intel.ai": UserInDB(
        id="analyst-001",
        email="analyst@sophia-intel.ai",
        name="Data Analyst",
        role="analyst",
        permissions=ROLE_PERMISSIONS["analyst"],
        hashed_password=pwd_context.hash("analyst123"),
        created_at=datetime.utcnow(),
    ),
}

# Refresh token store (replace with database/Redis in production)
REFRESH_TOKENS: dict[str, dict] = {}

class AuthService:
    """Authentication and authorization service"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def get_user(email: str) -> UserInDB | None:
        """Get user by email"""
        return USERS_DB.get(email)

    @staticmethod
    def authenticate_user(email: str, password: str) -> UserInDB | None:
        """Authenticate user with email and password"""
        user = AuthService.get_user(email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: timedelta | None = None
    ) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a refresh token"""
        token_data = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "type": "refresh",
        }
        refresh_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Store refresh token
        REFRESH_TOKENS[refresh_token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        }

        return refresh_token

    @staticmethod
    def verify_token(token: str) -> dict | None:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def verify_refresh_token(refresh_token: str) -> str | None:
        """Verify refresh token and return user_id"""
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("user_id")

            # Check if refresh token exists in store
            if refresh_token not in REFRESH_TOKENS:
                return None

            # Check if token has expired
            token_data = REFRESH_TOKENS[refresh_token]
            if datetime.utcnow() > token_data["expires_at"]:
                # Clean up expired token
                del REFRESH_TOKENS[refresh_token]
                return None

            return user_id

        except jwt.PyJWTError:
            return None

    @staticmethod
    def revoke_refresh_token(refresh_token: str) -> bool:
        """Revoke a refresh token"""
        if refresh_token in REFRESH_TOKENS:
            del REFRESH_TOKENS[refresh_token]
            return True
        return False

    @staticmethod
    def login(credentials: LoginCredentials) -> TokenData:
        """Login user and return tokens"""
        user = AuthService.authenticate_user(credentials.email, credentials.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login
        user.last_login = datetime.utcnow()

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "permissions": user.permissions,
            },
            expires_delta=access_token_expires,
        )

        # Create refresh token
        refresh_token = AuthService.create_refresh_token(user.id)

        return TokenData(
            token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def refresh_access_token(refresh_token_request: RefreshTokenRequest) -> TokenData:
        """Refresh access token using refresh token"""
        user_id = AuthService.verify_refresh_token(refresh_token_request.refresh_token)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Find user by ID
        user = None
        for u in USERS_DB.values():
            if u.id == user_id:
                user = u
                break

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "permissions": user.permissions,
            },
            expires_delta=access_token_expires,
        )

        # Create new refresh token
        AuthService.revoke_refresh_token(refresh_token_request.refresh_token)
        new_refresh_token = AuthService.create_refresh_token(user.id)

        return TokenData(
            token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def logout(refresh_token: str) -> bool:
        """Logout user by revoking refresh token"""
        return AuthService.revoke_refresh_token(refresh_token)

    @staticmethod
    def get_current_user_from_token(token: str) -> User:
        """Get current user from access token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        payload = AuthService.verify_token(token)
        if payload is None:
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Find user by ID
        user = None
        for u in USERS_DB.values():
            if u.id == user_id:
                user = u
                break

        if user is None:
            raise credentials_exception

        return User(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            permissions=user.permissions,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        )

    @staticmethod
    def check_permission(user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user.permissions

    @staticmethod
    def require_permission(user: User, required_permission: str) -> None:
        """Require user to have specific permission"""
        if not AuthService.check_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {required_permission}",
            )
