import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

from app.middleware.auth import get_current_user, get_optional_user

test_app = FastAPI()

@test_app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"status": "success", "user_id": user["id"]}

@test_app.get("/optional")
async def optional_route(user: dict = Depends(get_optional_user)):
    if user:
        return {"authenticated": True, "user_id": user["id"]}
    return {"authenticated": False, "user_id": None}

client = TestClient(test_app)

def test_protected_route_unauthorized_missing_header():
    response = client.get("/protected")
    assert response.status_code == 401
    assert "missing" in response.json()["detail"].lower()

def test_protected_route_mock_jwt_testing_mode():
    headers = {"Authorization": "Bearer mock-jwt-token-123"}
    with patch("app.middleware.auth.settings.TESTING", True):
        response = client.get("/protected", headers=headers)
        assert response.status_code == 200
        assert response.json()["user_id"] == "mock-user-uuid-12345"

def test_protected_route_invalid_token():
    headers = {"Authorization": "Bearer invalid-jwt-token"}
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.side_effect = Exception("Invalid token")
    
    with patch("app.middleware.auth.supabase_admin", mock_supabase), \
         patch("app.middleware.auth.settings.TESTING", False):
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

def test_optional_route_unauthenticated():
    response = client.get("/optional")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "user_id": None}

def test_optional_route_authenticated():
    headers = {"Authorization": "Bearer mock-jwt-token-123"}
    with patch("app.middleware.auth.settings.TESTING", True):
        response = client.get("/optional", headers=headers)
        assert response.status_code == 200
        assert response.json()["authenticated"] is True
        assert response.json()["user_id"] == "mock-user-uuid-12345"
