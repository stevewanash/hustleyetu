import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_bills_offline_mock():
    with patch("app.api.bills.supabase_admin", None):
        response = client.get("/api/bills")
        assert response.status_code == 200
        data = response.json()
        assert "bills" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["bills"]) == 2
        assert data["bills"][0]["title"] == "The Finance Bill, 2024"


def test_get_bills_with_supabase_mock():
    mock_bills_query = MagicMock()
    mock_bills_query.eq.return_value = mock_bills_query
    mock_bills_query.order.return_value = mock_bills_query
    mock_bills_query.range.return_value = mock_bills_query
    mock_bills_query.execute.return_value = MagicMock(
        data=[
            {
                "id": "bill-100",
                "title": "Test Bill 100",
                "bill_type": "financial",
                "created_at": "2026-08-09T23:00:00Z",
                "ai_status": "translated"
            }
        ],
        count=1
    )

    mock_tags_query = MagicMock()
    mock_tags_query.in_.return_value = mock_tags_query
    mock_tags_query.execute.return_value = MagicMock(
        data=[
            {"bill_id": "bill-100", "industry_tag": "Transport & Logistics"}
        ]
    )

    mock_supabase = MagicMock()
    def table_router(name):
        if name == "bills":
            mock_t = MagicMock()
            mock_t.select.return_value = mock_bills_query
            return mock_t
        elif name == "bill_tags":
            mock_t = MagicMock()
            mock_t.select.return_value = mock_tags_query
            return mock_t
        return MagicMock()

    mock_supabase.table.side_effect = table_router

    with patch("app.api.bills.supabase_admin", mock_supabase):
        response = client.get("/api/bills?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["bills"]) == 1
        assert data["bills"][0]["id"] == "bill-100"
        assert data["bills"][0]["tags"] == ["Transport & Logistics"]


def test_get_bills_industry_filter_empty():
    mock_supabase = MagicMock()
    mock_tag_query = MagicMock()
    mock_tag_query.eq.return_value = mock_tag_query
    mock_tag_query.execute.return_value = MagicMock(data=[])

    mock_supabase.table.return_value.select.return_value = mock_tag_query

    with patch("app.api.bills.supabase_admin", mock_supabase):
        response = client.get("/api/bills?industry=NonExistentIndustry")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["bills"] == []


def test_get_bill_detail_success():
    mock_supabase = MagicMock()
    
    mock_bills_table = MagicMock()
    mock_bills_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "bill-100",
                "title": "Test Bill 100",
                "bill_type": "financial",
                "ai_summary_en": "English summary here.",
                "ai_summary_sw": "Kiswahili summary here.",
                "regex_extractions": [{"value": "16%"}],
                "source_url": "https://parliament.go.ke/bill.pdf",
                "created_at": "2026-08-09T23:00:00Z"
            }
        ]
    )

    mock_tags_table = MagicMock()
    mock_tags_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"industry_tag": "Transport & Logistics"}]
    )

    def table_router(name):
        if name == "bills":
            return mock_bills_table
        elif name == "bill_tags":
            return mock_tags_table
        return MagicMock()

    mock_supabase.table.side_effect = table_router

    with patch("app.api.bills.supabase_admin", mock_supabase):
        response = client.get("/api/bills/bill-100")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "bill-100"
        assert data["title"] == "Test Bill 100"
        assert data["ai_summary_en"] == "English summary here."
        assert data["tags"] == ["Transport & Logistics"]


def test_get_bill_detail_404():
    mock_supabase = MagicMock()
    mock_bills_table = MagicMock()
    mock_bills_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value = mock_bills_table

    with patch("app.api.bills.supabase_admin", mock_supabase):
        response = client.get("/api/bills/non-existent-bill")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_impact_success():
    mock_supabase = MagicMock()
    mock_cache_table = MagicMock()
    mock_cache_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "impact_data": {
                    "bill_type": "financial",
                    "concise_summary": "Introduces a 2.5% motor vehicle circulation tax based on valuation.",
                    "scenario_persona": {
                        "name": "Mama Njeri",
                        "description": "Transport operator",
                        "metrics": {"vehicle_value": 800000}
                    },
                    "key_figures": ["2.5% Tax rate"],
                    "math_breakdown": ["Annual Cost = KES 800,000 * 2.5% = KES 20,000"],
                    "calculator_formula": "min(max(vehicle_value * 0.025, 5000), 100000)",
                    "sources": ["Section 4"],
                    "risk_level": "MEDIUM",
                    "verified": True
                }
            }
        ]
    )

    mock_bills_table = MagicMock()
    mock_bills_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "bill-100",
                "title": "Finance Bill 2024",
                "bill_type": "financial",
                "source_url": "https://example.com/bill.pdf"
            }
        ]
    )

    def table_router(name):
        if name == "tier_impact_cache":
            return mock_cache_table
        elif name == "bills":
            return mock_bills_table
        return MagicMock()

    mock_supabase.table.side_effect = table_router

    with patch("app.api.impact.supabase_admin", mock_supabase):
        response = client.get("/api/impact/bill-100")
        assert response.status_code == 200
        data = response.json()
        assert data["bill_type"] == "financial"
        assert data["scenario_persona"]["name"] == "Mama Njeri"
        assert data["calculator_formula"] == "min(max(vehicle_value * 0.025, 5000), 100000)"


def test_get_impact_bill_not_found_404():
    mock_supabase = MagicMock()
    mock_cache_table = MagicMock()
    mock_cache_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_bills_table = MagicMock()
    mock_bills_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

    def table_router(name):
        if name == "tier_impact_cache":
            return mock_cache_table
        elif name == "bills":
            return mock_bills_table
        return MagicMock()

    mock_supabase.table.side_effect = table_router

    with patch("app.api.impact.supabase_admin", mock_supabase):
        response = client.get("/api/impact/missing-bill")
        assert response.status_code == 404

        assert "not found" in response.json()["detail"].lower()
