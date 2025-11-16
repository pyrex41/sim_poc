"""Authentication utilities for JWT tokens and password hashing."""
import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from backend.database import (
    get_user_by_username,
    update_user_last_login,
    get_api_key_by_hash,
    update_api_key_last_used
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
# Token expiration: 5 days (7200 minutes) for persistent login
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "7200"))

# Security schemes
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Cookie name
COOKIE_NAME = "access_token"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt."""
    # Convert to bytes and truncate to 72 bytes for bcrypt
    password_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert to bytes and truncate to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user by username and password."""
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user["is_active"]:
        return None
    return user

def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"sk_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage using bcrypt."""
    key_bytes = api_key.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(key_bytes, salt)
    return hashed.decode('utf-8')

def verify_api_key(api_key: str, key_hash: str) -> bool:
    """Verify an API key against its hash using bcrypt."""
    key_bytes = api_key.encode('utf-8')[:72]
    hash_bytes = key_hash.encode('utf-8')
    return bcrypt.checkpw(key_bytes, hash_bytes)

# Dependency for JWT token authentication
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user

# Dependency for API key authentication
async def get_current_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[Dict[str, Any]]:
    """Get current user from API key (optional)."""
    if not api_key:
        return None

    # Try to find API key in database
    # We need to check all API keys and verify the hash
    # This is a simple implementation - for production, consider caching
    from database import get_db

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT ak.*, u.username, u.email, u.is_active as user_is_active, u.is_admin
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.is_active = 1
            """
        ).fetchall()

        for row in rows:
            if verify_api_key(api_key, row["key_hash"]):
                # Check if expired
                if row["expires_at"]:
                    expires_at = datetime.fromisoformat(row["expires_at"])
                    if datetime.utcnow() > expires_at:
                        continue

                # Check if user is active
                if not row["user_is_active"]:
                    continue

                # Update last used timestamp
                update_api_key_last_used(row["key_hash"])

                return {
                    "id": row["user_id"],
                    "username": row["username"],
                    "email": row["email"],
                    "is_active": bool(row["user_is_active"]),
                    "is_admin": bool(row["is_admin"])
                }

    return None

# Combined authentication dependency (accepts either JWT or API key)
async def get_current_user(
    token_user: Optional[Dict[str, Any]] = Depends(lambda: None),
    api_key_user: Optional[Dict[str, Any]] = Depends(get_current_user_from_api_key)
) -> Dict[str, Any]:
    """Get current user from either JWT token or API key."""
    # Try API key first
    if api_key_user:
        return api_key_user

    # Try JWT token
    try:
        from fastapi import Request
        # This is a workaround to get the token from the request
        # In a real implementation, you would use proper dependency injection
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception
    except:
        pass

    # If no authentication method succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide either a Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Simplified combined authentication
async def verify_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    api_key: Optional[str] = Security(api_key_header)
) -> Dict[str, Any]:
    """Verify authentication from cookie, Bearer token, or API key."""

    # Bypass authentication in local development
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    if base_url.startswith("http://localhost") or base_url.startswith("http://127.0.0.1"):
        # Return a mock user for local development
        return {
            "id": 1,
            "username": "dev_user",
            "email": "dev@localhost",
            "is_active": True,
            "is_admin": True,
            "created_at": datetime.utcnow().isoformat()
        }

    # Try cookie first (most common for web UI)
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        payload = decode_access_token(cookie_token)
        if payload:
            username = payload.get("sub")
            if username:
                user = get_user_by_username(username)
                if user and user["is_active"]:
                    update_user_last_login(user["id"])
                    return user

    # Try API key
    if api_key:
        user = await get_current_user_from_api_key(api_key)
        if user:
            return user

    # Try Bearer token
    if credentials:
        user = await get_current_user_from_token(credentials)
        if user:
            # Update last login for token auth
            update_user_last_login(user["id"])
            return user

    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Login required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Admin-only dependency
async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(verify_auth)
) -> Dict[str, Any]:
    """Verify that the current user is an admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
