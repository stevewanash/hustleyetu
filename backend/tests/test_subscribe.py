import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def _mock_supabase():
    """Create a MagicMock that simulates the Supabase admin client for subscribe operations."""
    mock = MagicMock()

    # Default upsert response (subscribe)
    mock.table.return_value.upsert.return_value.execute.return_value = MagicMock(
        data=[{"id": "test-subscriber-uuid-001", "phone_hash": "abc123"}]
    )

    # Default select response (status lookup — no row found)
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    # Default update response (unsubscribe)
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "test-subscriber-uuid-001", "is_active": False}]
    )

    return mock


@pytest.fixture(autouse=True)
def enable_testing_mode():
    original_testing = getattr(settings, "TESTING", False)
    settings.TESTING = True
    yield
    settings.TESTING = original_testing


# ==========================================
# POST /api/subscribe tests
# ==========================================

@patch("app.api.subscribe.supabase_admin")
@patch("app.api.subscribe.send_sms")
def test_subscribe_success(mock_sms, mock_db):
    mock_db_instance = _mock_supabase()
    mock_db.__bool__ = lambda self: True
    mock_db.table = mock_db_instance.table

    payload = {
        "phone": "0712345678",
        "industries": ["Transport & Logistics"],
        "language": "en",
        "channels": ["sms"]
    }
    response = client.post("/api/subscribe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "subscriber_id" in data
    assert data["status"] == "subscribed"
    assert data["subscriber_id"] == "test-subscriber-uuid-001"
    mock_sms.assert_called_once()


@patch("app.api.subscribe.supabase_admin")
@patch("app.api.subscribe.send_sms")
def test_subscribe_swahili(mock_sms, mock_db):
    mock_db_instance = _mock_supabase()
    mock_db.__bool__ = lambda self: True
    mock_db.table = mock_db_instance.table

    payload = {
        "phone": "+254712345679",
        "industries": ["Transport & Logistics"],
        "language": "sw",
        "channels": ["sms"]
    }
    response = client.post("/api/subscribe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "subscribed"
    # Verify Swahili confirmation SMS was dispatched
    sms_call = mock_sms.call_args
    assert "Umesajiliwa" in sms_call[0][1]


def test_subscribe_invalid_phone():
    payload = {
        "phone": "invalid-phone-num",
        "industries": ["Transport & Logistics"],
        "language": "en",
        "channels": ["sms"]
    }
    response = client.post("/api/subscribe", json=payload)
    assert response.status_code == 400
    assert "Invalid phone number" in response.json()["detail"]


def test_subscribe_invalid_language():
    """Issue #5: language must be 'en' or 'sw'."""
    payload = {
        "phone": "0712345678",
        "industries": ["Transport & Logistics"],
        "language": "fr",
        "channels": ["sms"]
    }
    response = client.post("/api/subscribe", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_subscribe_invalid_channel():
    """Issue #5: channels must be subset of {'sms', 'whatsapp'}."""
    payload = {
        "phone": "0712345678",
        "industries": ["Transport & Logistics"],
        "language": "en",
        "channels": ["email"]
    }
    response = client.post("/api/subscribe", json=payload)
    assert response.status_code == 422  # Pydantic validation error


# ==========================================
# DELETE /api/subscribe tests
# ==========================================

@patch("app.api.subscribe.supabase_admin")
def test_unsubscribe_query_param(mock_db):
    mock_db_instance = _mock_supabase()
    mock_db.__bool__ = lambda self: True
    mock_db.table = mock_db_instance.table

    response = client.delete("/api/subscribe?phone=0712345678")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsubscribed"


@patch("app.api.subscribe.supabase_admin")
def test_unsubscribe_json_body(mock_db):
    mock_db_instance = _mock_supabase()
    mock_db.__bool__ = lambda self: True
    mock_db.table = mock_db_instance.table

    response = client.request("DELETE", "/api/subscribe", json={"phone": "+254712345678"})
    assert response.status_code == 200
    assert response.json()["status"] == "unsubscribed"


# ==========================================
# GET /api/subscribe/status tests
# ==========================================

@patch("app.api.subscribe.supabase_admin")
def test_get_subscription_status_found(mock_db):
    """Status returns active subscription data when subscriber exists."""
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "is_active": True,
            "industry_tags": ["Transport & Logistics"],
            "preferred_language": "sw",
            "channels": ["sms"]
        }]
    )
    mock_db.table.return_value = mock_table

    response = client.get("/api/subscribe/status?phone=0712345678")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["preferred_language"] == "sw"


@patch("app.api.subscribe.supabase_admin")
def test_get_subscription_status_not_found(mock_db):
    """Status returns inactive default when no subscriber row matches."""
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_db.table.return_value = mock_table

    response = client.get("/api/subscribe/status?phone=0712345678")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@patch("app.api.subscribe.supabase_admin")
def test_get_subscription_status_db_error_returns_503(mock_db):
    """Issue #3: DB errors surface as 503, not silent 'not subscribed'."""
    settings.TESTING = False  # Temporarily disable TESTING to test production path
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("connection timeout")
    mock_db.table.return_value = mock_table

    response = client.get("/api/subscribe/status?phone=0712345678")
    assert response.status_code == 503
    settings.TESTING = True  # Restore
