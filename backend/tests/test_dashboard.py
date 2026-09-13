import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_stats_offline_mock():
    with patch("app.api.dashboard.supabase_admin", None):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_feedback" in data
        assert "support_pct" in data
        assert "avg_rating" in data
        assert "top_concerns" in data
        assert data["total_feedback"] == 210
        assert data["support_pct"]["support"] == 19.4


def test_dashboard_stats_offline_mock_by_bill():
    with patch("app.api.dashboard.supabase_admin", None):
        response = client.get("/api/dashboard/stats?bill_id=mock-bill-002")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] == 86
        assert data["support_pct"]["support"] == 30.0
        assert data["avg_rating"] == 2.5


def test_dashboard_stats_with_supabase_data():
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(
        data=[
            {"support": "support", "rating": 4, "concerns": "High registration fee"},
            {"support": "oppose", "rating": 2, "concerns": "Too many penalties"},
            {"support": "oppose", "rating": 1, "concerns": "Daily income disruption"},
            {"support": "neutral", "rating": 3, "concerns": None},
        ]
    )
    mock_supabase.table.return_value.select.return_value = mock_query

    with patch("app.api.dashboard.supabase_admin", mock_supabase):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] == 4
        assert data["support_pct"]["support"] == 25.0
        assert data["support_pct"]["oppose"] == 50.0
        assert data["support_pct"]["neutral"] == 25.0
        assert data["avg_rating"] == 2.5
        assert len(data["top_concerns"]) == 3
        assert "High registration fee" in data["top_concerns"]


def test_dashboard_stats_filter_by_bill_id():
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_eq = MagicMock()
    mock_eq.execute.return_value = MagicMock(
        data=[
            {"support": "support", "rating": 5, "concerns": "Great for SACCOs"},
        ]
    )
    mock_query.eq.return_value = mock_eq
    mock_supabase.table.return_value.select.return_value = mock_query

    with patch("app.api.dashboard.supabase_admin", mock_supabase):
        response = client.get("/api/dashboard/stats?bill_id=550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 200
        data = response.json()
        mock_query.eq.assert_called_once_with("bill_id", "550e8400-e29b-41d4-a716-446655440000")
        assert data["total_feedback"] == 1
        assert data["support_pct"]["support"] == 100.0
        assert data["avg_rating"] == 5.0


def test_dashboard_stats_empty_feedback():
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value = mock_query

    with patch("app.api.dashboard.supabase_admin", mock_supabase):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] == 0
        assert data["support_pct"] == {"support": 0.0, "oppose": 0.0, "neutral": 0.0}
        assert data["avg_rating"] == 0.0
        assert data["top_concerns"] == []


def test_dashboard_stats_concerns_frequency_ranking():
    mock_supabase = MagicMock()
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(
        data=[
            {"support": "oppose", "rating": 1, "concerns": "Daily margin reduction"},
            {"support": "oppose", "rating": 2, "concerns": "Excessive permit fee"},
            {"support": "oppose", "rating": 2, "concerns": "Daily margin reduction"},
            {"support": "support", "rating": 4, "concerns": "Safety helmets"},
            {"support": "oppose", "rating": 1, "concerns": "Excessive permit fee"},
            {"support": "oppose", "rating": 1, "concerns": "Daily margin reduction"},
        ]
    )
    mock_supabase.table.return_value.select.return_value = mock_query

    with patch("app.api.dashboard.supabase_admin", mock_supabase):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] == 6
        # Frequency counts: "Daily margin reduction" (3), "Excessive permit fee" (2), "Safety helmets" (1)
        assert data["top_concerns"] == [
            "Daily margin reduction",
            "Excessive permit fee",
            "Safety helmets",
        ]

