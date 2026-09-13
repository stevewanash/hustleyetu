import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.notifier import send_bill_alerts, send_sms_alert, send_sms
from app.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def enable_testing_mode():
    original_testing = getattr(settings, "TESTING", False)
    settings.TESTING = True
    yield
    settings.TESTING = original_testing


@pytest.mark.asyncio
async def test_send_bill_alerts_mock_fallback():
    """In testing fallback mode with no DB, send_bill_alerts returns result counters."""
    res = await send_bill_alerts("mock-bill-001")
    assert res["bill_id"] == "mock-bill-001"
    assert "subscribers_found" in res
    assert "alerts_sent" in res
    assert "alerts_failed" in res


@pytest.mark.asyncio
@patch("app.database.supabase_admin")
async def test_send_bill_alerts_unprocessed_bill_raises_error(mock_db):
    """Issue 2: Alerts rejected if bill has not been translated/verified."""
    mock_db.__bool__ = lambda self: True
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "bill-123", "title": "Unprocessed Bill", "ai_status": "ingested"}]
    )
    mock_db.table.return_value = mock_table

    with pytest.raises(ValueError) as exc_info:
        await send_bill_alerts("bill-123")
    assert "has not been fully processed" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.database.supabase_admin")
@patch("app.services.notifier.send_sms")
async def test_send_bill_alerts_tag_matching_and_deduplication(mock_sms, mock_db):
    """Issue 3 & 4: Strict tag overlap matching and deduplication skipping."""
    mock_db.__bool__ = lambda self: True

    # Setup mock table responses
    def table_router(name):
        mock_t = MagicMock()
        if name == "bills":
            mock_t.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "bill-transport-1", "title": "Bodaboda Permit Law", "ai_status": "translated"}]
            )
        elif name == "bill_tags":
            mock_t.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"industry_tag": "Transport & Logistics"}]
            )
        elif name == "subscribers":
            mock_t.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {"id": "sub-1", "phone_encrypted": "+254711111111", "preferred_language": "en", "industry_tags": ["Transport & Logistics"]},
                    {"id": "sub-2", "phone_encrypted": "+254722222222", "preferred_language": "sw", "industry_tags": ["Agriculture & Farming"]}
                ]
            )
        elif name == "notifications":
            # sub-1 already notified
            mock_t.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"subscriber_id": "sub-1", "status": "sent"}]
            )
        return mock_t

    mock_db.table.side_effect = table_router

    # First run without force -> sub-1 skipped (dedup), sub-2 tag mismatch -> 0 sent
    res1 = await send_bill_alerts("bill-transport-1", force=False)
    assert res1["subscribers_found"] == 1  # Only sub-1 matches tag
    assert res1["alerts_skipped"] == 1
    assert res1["alerts_sent"] == 0

    # Second run with force=True -> sub-1 notified
    res2 = await send_bill_alerts("bill-transport-1", force=True)
    assert res2["subscribers_found"] == 1
    assert res2["alerts_sent"] == 1
    mock_sms.assert_called_once()


@patch("app.api.admin.send_bill_alerts")
def test_admin_send_alerts_endpoint_auth(mock_send):
    """Issue 1 & 9: Admin endpoint requires valid X-API-Token header."""
    mock_send.return_value = {
        "bill_id": "mock-bill-001",
        "subscribers_found": 0,
        "alerts_sent": 0,
        "alerts_failed": 0,
        "alerts_skipped": 0
    }
    headers = {"X-API-Token": "mock-api-token"}
    response = client.post("/api/admin/send-alerts/mock-bill-001", headers=headers)
    assert response.status_code == 200

    # Test invalid header token rejection
    bad_headers = {"X-API-Token": "wrong-token-value"}
    response_bad = client.post("/api/admin/send-alerts/mock-bill-001", headers=bad_headers)
    assert response_bad.status_code == 401


@patch("app.api.admin.send_bill_alerts")
def test_admin_token_production_bypass_prevention(mock_send):
    """Issue 9 & 13: Verify literal 'mock-api-token' is rejected in production mode."""
    mock_send.return_value = {
        "bill_id": "mock-bill-001",
        "subscribers_found": 0,
        "alerts_sent": 0,
        "alerts_failed": 0,
        "alerts_skipped": 0
    }
    settings.TESTING = False
    original_secret = getattr(settings, "API_SECRET_TOKEN", "prod-secret-key-999")
    settings.API_SECRET_TOKEN = "prod-secret-key-999"

    try:
        # Request with mock token should be rejected in prod mode
        res = client.post("/api/admin/send-alerts/mock-bill-001", headers={"X-API-Token": "mock-api-token"})
        assert res.status_code == 401

        # Request with real token should be accepted
        res_valid = client.post("/api/admin/send-alerts/mock-bill-001", headers={"X-API-Token": "prod-secret-key-999"})
        assert res_valid.status_code == 200
    finally:
        # Restore settings
        settings.TESTING = True
        settings.API_SECRET_TOKEN = original_secret


@pytest.mark.asyncio
async def test_send_sms_alert_mock():
    res = await send_sms_alert("mock-sub-uuid-1", "Test message")
    assert "status" in res


def test_send_sms_normalization():
    """Issue 7: send_sms normalizes raw phone numbers."""
    res = send_sms("0700000000", "Test SMS")
    assert res["status"] == "success"
    assert res["recipients"][0]["number"] == "+254700000000"
