import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def enable_testing_mode():
    original_testing = getattr(settings, "TESTING", False)
    settings.TESTING = True
    yield
    settings.TESTING = original_testing


@patch("app.api.webhooks.supabase_admin")
def test_at_delivery_webhook_json(mock_db):
    """Issue 4: Verify DB update call and normalized status mapping for JSON POST."""
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_db.table.return_value = mock_table

    payload = {
        "id": "AT-MSG-12345",
        "status": "Success",
        "phoneNumber": "+254712345678"
    }
    response = client.post("/api/webhooks/at-delivery", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["message_id"] == "AT-MSG-12345"
    assert data["normalized_status"] == "delivered"
    assert data["db_updated"] is True

    # Assert database update call was executed with normalized status
    mock_db.table.assert_called_with("notifications")
    mock_table.update.assert_called_once()
    update_args = mock_table.update.call_args[0][0]
    assert update_args["status"] == "delivered"
    mock_table.update.return_value.eq.assert_called_with("at_message_id", "AT-MSG-12345")


@patch("app.api.webhooks.supabase_admin")
def test_at_delivery_webhook_form_data(mock_db):
    """Issue 4: Verify status mapping for form-encoded POST."""
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_db.table.return_value = mock_table

    form_data = {
        "id": "AT-MSG-67890",
        "status": "DeliveredToTerminal",
        "phoneNumber": "+254712345678"
    }
    response = client.post("/api/webhooks/at-delivery", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["message_id"] == "AT-MSG-67890"
    assert data["normalized_status"] == "delivered"
    assert data["db_updated"] is True


@patch("app.api.webhooks.supabase_admin")
def test_at_delivery_webhook_failure_reason(mock_db):
    """Issue 4: Verify failure status and reason persistence."""
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_db.table.return_value = mock_table

    payload = {
        "id": "AT-MSG-FAILED-99",
        "status": "Rejected",
        "failureReason": "User unreachable"
    }
    response = client.post("/api/webhooks/at-delivery", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["normalized_status"] == "failed"
    
    update_args = mock_table.update.call_args[0][0]
    assert update_args["status"] == "failed"
    assert update_args["failure_reason"] == "User unreachable"


def test_at_delivery_webhook_missing_id():
    payload = {"status": "Success"}
    response = client.post("/api/webhooks/at-delivery", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_at_delivery_webhook_secret_verification():
    """Issue 5: Verify AT_DELIVERY_WEBHOOK_SECRET verification in production mode."""
    settings.TESTING = False
    original_secret = getattr(settings, "AT_DELIVERY_WEBHOOK_SECRET", None)
    settings.AT_DELIVERY_WEBHOOK_SECRET = "at-secret-key-123"

    payload = {"id": "AT-MSG-SEC-01", "status": "Success"}

    # Missing header -> 401
    res_bad = client.post("/api/webhooks/at-delivery", json=payload)
    assert res_bad.status_code == 401

    # Valid secret header -> 200
    res_ok = client.post("/api/webhooks/at-delivery", json=payload, headers={"x-at-webhook-secret": "at-secret-key-123"})
    assert res_ok.status_code == 200

    # Restore settings
    settings.TESTING = True
    settings.AT_DELIVERY_WEBHOOK_SECRET = original_secret
