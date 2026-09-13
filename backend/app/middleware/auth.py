import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency requiring a valid Supabase JWT Bearer token.
    Raises HTTP 401 Unauthorized if missing or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Test mode mock fallback
    if getattr(settings, "TESTING", False) and token.startswith("mock-jwt-token"):
        return {
            "id": "mock-user-uuid-12345",
            "phone": "+254712345678",
            "email": "mockuser@example.com",
            "role": "authenticated",
            "user_metadata": {}
        }

    if not supabase_admin:
        logger.warning("Supabase admin client unavailable for auth verification")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    try:
        user_response = supabase_admin.auth.get_user(token)
        if not user_response or not getattr(user_response, "user", None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        return {
            "id": getattr(user, "id", None),
            "phone": getattr(user, "phone", None),
            "email": getattr(user, "email", None),
            "role": getattr(user, "role", "authenticated"),
            "user_metadata": getattr(user, "user_metadata", {}) or {}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for optional authentication.
    Returns user dict if valid Bearer token is provided, or None if unauthenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split("Bearer ")[1].strip()
    if not token:
        return None

    # Test mode mock fallback
    if getattr(settings, "TESTING", False) and token.startswith("mock-jwt-token"):
        return {
            "id": "mock-user-uuid-12345",
            "phone": "+254712345678",
            "email": "mockuser@example.com",
            "role": "authenticated",
            "user_metadata": {}
        }

    if not supabase_admin:
        return None

    try:
        user_response = supabase_admin.auth.get_user(token)
        if user_response and getattr(user_response, "user", None):
            user = user_response.user
            return {
                "id": getattr(user, "id", None),
                "phone": getattr(user, "phone", None),
                "email": getattr(user, "email", None),
                "role": getattr(user, "role", "authenticated"),
                "user_metadata": getattr(user, "user_metadata", {}) or {}
            }
    except Exception as e:
        logger.debug(f"Optional user JWT verification failed cleanly: {e}")
        return None

    return None
