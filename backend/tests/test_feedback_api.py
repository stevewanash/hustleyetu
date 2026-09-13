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


def make_feedback_mock(existing_feedback_data=None, insert_error=None):
    """Helper creating a table-router mock of correct chain depth for bills and feedback tables."""
    mock_db = MagicMock()
    mock_db.__bool__ = lambda self: True

    def table_router(name):
        mock_t = MagicMock()
        if name == "bills":
            # bill_check chain: select("id").eq("id", bill_id).execute()
            mock_t.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "mock-bill-001"}]
            )
        elif name == "feedback":
            # existing_res chain: select("id").eq("bill_id", ...).eq("user_id", ...).execute()
            select_chain = mock_t.select.return_value.eq.return_value.eq.return_value
            select_chain.execute.return_value = MagicMock(data=existing_feedback_data or [])

            # insert chain: insert(data).execute()
            if insert_error:
                mock_t.insert.return_value.execute.side_effect = insert_error
            else:
                mock_t.insert.return_value.execute.return_value = MagicMock(
                    data=[{"id": "fb-uuid-12345", "created_at": "2026-08-13T12:00:00Z"}]
                )
        return mock_t

    mock_db.table.side_effect = table_router
    return mock_db


def test_submit_feedback_unauthorized():
    """Unauthenticated feedback submission returns 401."""
    payload = {
        "bill_id": "mock-bill-001",
        "support": "support",
        "rating": 5,
        "concerns": "No concerns"
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 401


def test_submit_feedback_authorized_success():
    """Issue 6 Fix: Authorized feedback submission with table-router mock returning 201."""
    mock_db = make_feedback_mock(existing_feedback_data=[])
    with patch("app.api.feedback.supabase_admin", mock_db):
        payload = {
            "bill_id": "mock-bill-001",
            "support": "support",
            "rating": 4,
            "concerns": "Fuel costs will increase"
        }
        headers = {"Authorization": "Bearer mock-jwt-token-12345"}
        response = client.post("/api/feedback", json=payload, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert data["id"] == "fb-uuid-12345"


def test_submit_feedback_duplicate_precheck_409():
    """Issue 1 & 6 Fix: Pre-check duplicate detection returns 409 Conflict."""
    mock_db = make_feedback_mock(existing_feedback_data=[{"id": "fb-existing-id"}])
    with patch("app.api.feedback.supabase_admin", mock_db):
        payload = {
            "bill_id": "mock-bill-001",
            "support": "oppose",
            "rating": 2,
            "concerns": "Duplicate submission"
        }
        headers = {"Authorization": "Bearer mock-jwt-token-12345"}
        response = client.post("/api/feedback", json=payload, headers=headers)
        assert response.status_code == 409
        assert "already submitted feedback" in response.json()["detail"]


def test_submit_feedback_duplicate_23505_fallback_409():
    """Issue 1, 2 & 6 Fix: Database 23505 unique constraint violation on insert returns 409 Conflict."""
    db_err = Exception("duplicate key value violates unique constraint 'unique_bill_user_feedback' (code: 23505)")
    setattr(db_err, "code", "23505")
    mock_db = make_feedback_mock(existing_feedback_data=[], insert_error=db_err)
    with patch("app.api.feedback.supabase_admin", mock_db):
        payload = {
            "bill_id": "mock-bill-001",
            "support": "neutral",
            "rating": 3
        }
        headers = {"Authorization": "Bearer mock-jwt-token-12345"}
        response = client.post("/api/feedback", json=payload, headers=headers)
        assert response.status_code == 409
        assert "already submitted feedback" in response.json()["detail"]


def test_submit_feedback_invalid_support():
    payload = {
        "bill_id": "mock-bill-001",
        "support": "invalid-stance",
        "rating": 4
    }
    headers = {"Authorization": "Bearer mock-jwt-token-12345"}
    response = client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Support field must be" in response.json()["detail"]


def test_submit_feedback_invalid_rating():
    payload = {
        "bill_id": "mock-bill-001",
        "support": "oppose",
        "rating": 10
    }
    headers = {"Authorization": "Bearer mock-jwt-token-12345"}
    response = client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Rating must be an integer" in response.json()["detail"]


def test_submit_feedback_invalid_bill_id_uuid():
    """Issue 3: Malformed bill_id string returns 400 Bad Request."""
    payload = {
        "bill_id": "not-a-valid-uuid-string",
        "support": "support",
        "rating": 4
    }
    headers = {"Authorization": "Bearer mock-jwt-token-12345"}
    response = client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Invalid bill_id format" in response.json()["detail"]
