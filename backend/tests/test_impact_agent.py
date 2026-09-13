import json
import pytest
from unittest.mock import patch, MagicMock

from app.agents.impact_agent import (
    compute_financial_impact_analysis,
)
from app.agents.llm_client import GeminiResponse
from app.models.schemas import ImpactResponse, ScenarioPersona, ComplianceActionItem
from app.models.hustle_profiles import HUSTLE_PROFILES


@pytest.fixture
def sample_financial_bill():
    return {
        "id": "bill-101",
        "title": "Finance Bill 2024",
        "bill_type": "financial",
        "ai_summary_en": "Introduces a 2.5% motor vehicle circulation tax based on vehicle value.",
        "regex_extractions": [
            {
                "type": "percentage",
                "value": 2.5,
                "raw": "2.5%",
                "context": "motor vehicle circulation tax at 2.5%",
            }
        ],
    }


@pytest.fixture
def sample_regulatory_bill():
    return {
        "id": "bill-102",
        "title": "Nairobi Boda Boda Permit Regulations 2025",
        "bill_type": "regulatory",
        "ai_summary_en": "Mandates annual county operating permit (KES 3000) and mandatory safety training.",
        "regex_extractions": [
            {
                "type": "currency",
                "value": 3000.0,
                "raw": "3,000 shillings",
                "context": "annual permit fee of KES 3,000",
            }
        ],
    }


@pytest.fixture
def sample_bodaboda_profile():
    return HUSTLE_PROFILES["Transport & Logistics"][0]


def test_compute_financial_impact_financial_bill(sample_financial_bill, sample_bodaboda_profile):
    """Test computing financial impact analysis for a financial bill."""
    mock_impact = ImpactResponse(
        bill_type="financial",
        scenario_persona=ScenarioPersona(
            name="Boda Boda Operator",
            description="Operator of a 150cc commercial motorcycle valued at KES 150,000.",
            metrics={"vehicle_value": 150000.0},
        ),
        concise_summary="Introduces 2.5% motor vehicle tax.",
        key_figures=["2.5% Motor vehicle tax"],
        math_breakdown=["Annual tax: KES 150,000 * 2.5% = KES 3,750"],
        calculator_formula="vehicle_value * 0.025",
        risk_level="MEDIUM",
        verified=True,
        disclaimer="Test disclaimer",
    )

    with patch("app.agents.impact_agent.call_gemini") as mock_call:
        mock_call.return_value = GeminiResponse(
            text="Mock text",
            parsed=mock_impact,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=250.0,
            model_name="gemini-3.5-flash",
        )

        res = compute_financial_impact_analysis(sample_financial_bill, sample_bodaboda_profile)

        assert isinstance(res, ImpactResponse)
        assert res.bill_type == "financial"
        assert res.risk_level == "MEDIUM"
        assert res.scenario_persona.name == "Boda Boda Operator"
        assert res.calculator_formula == "vehicle_value * 0.025"


def test_compute_financial_impact_regulatory_bill(sample_regulatory_bill, sample_bodaboda_profile):
    """Test computing compliance advice for a regulatory bill."""
    mock_impact = ImpactResponse(
        bill_type="regulatory",
        concise_summary="Mandates annual county permit and safety training.",
        regulatory_changes=["Annual county operating permit required"],
        compliance_checklist=[
            ComplianceActionItem(
                action="Obtain annual boda boda operating permit badge",
                deadline="Within 90 days",
                source="Section 3(1)",
            )
        ],
        risk_level="HIGH",
        verified=True,
    )

    with patch("app.agents.impact_agent.call_gemini") as mock_call:
        mock_call.return_value = GeminiResponse(
            text="Mock text",
            parsed=mock_impact,
            prompt_tokens=120,
            completion_tokens=60,
            total_tokens=180,
            latency_ms=300.0,
            model_name="gemini-3.5-flash",
        )

        res = compute_financial_impact_analysis(sample_regulatory_bill, sample_bodaboda_profile)

        assert isinstance(res, ImpactResponse)
        assert res.bill_type == "regulatory"
        assert len(res.compliance_checklist) == 1
        assert res.compliance_checklist[0].source == "Section 3(1)"


def test_compute_financial_impact_call_gemini_exception(sample_financial_bill, sample_bodaboda_profile):
    """Test handling when call_gemini raises an exception."""
    with patch("app.agents.impact_agent.call_gemini", side_effect=RuntimeError("API 403 Forbidden")):
        res = compute_financial_impact_analysis(sample_financial_bill, sample_bodaboda_profile)
        assert isinstance(res, ImpactResponse)
        assert res.bill_type == "financial"
        assert res.risk_level == "MEDIUM"
        assert res.verified is True


def test_compute_financial_impact_text_json_fallback(sample_financial_bill, sample_bodaboda_profile):
    """Test JSON text parsing fallback when response.parsed is None."""
    raw_json = json.dumps({
        "bill_type": "financial",
        "scenario_persona": {
            "name": "Boda Boda Operator",
            "description": "Rider baseline",
            "metrics": {"vehicle_value": 150000.0}
        },
        "concise_summary": "Summary text",
        "key_figures": ["2.5% tax"],
        "math_breakdown": ["Calculation"],
        "calculator_formula": "vehicle_value * 0.025",
        "risk_level": "MEDIUM",
        "verified": True,
        "disclaimer": "JSON text test"
    })
    fenced_text = f"```json\n{raw_json}\n```"

    with patch("app.agents.impact_agent.call_gemini") as mock_call:
        mock_call.return_value = GeminiResponse(
            text=fenced_text,
            parsed=None,
        )

        res = compute_financial_impact_analysis(sample_financial_bill, sample_bodaboda_profile)
        assert isinstance(res, ImpactResponse)
        assert res.bill_type == "financial"
        assert res.risk_level == "MEDIUM"


def test_compute_financial_impact_malformed_json(sample_financial_bill, sample_bodaboda_profile):
    """Test fallback when response.parsed is None and response.text is malformed JSON."""
    with patch("app.agents.impact_agent.call_gemini") as mock_call:
        mock_call.return_value = GeminiResponse(
            text="Invalid JSON String {bad",
            parsed=None,
        )

        res = compute_financial_impact_analysis(sample_financial_bill, sample_bodaboda_profile)
        assert isinstance(res, ImpactResponse)
        assert res.bill_type == "financial"
        assert res.risk_level == "MEDIUM"


def test_compute_financial_impact_fallback(sample_financial_bill, sample_bodaboda_profile):
    """Test fallback response generation when Gemini call fails or returns empty."""
    with patch("app.agents.impact_agent.call_gemini") as mock_call:
        mock_call.return_value = GeminiResponse(text="", parsed=None)

        res = compute_financial_impact_analysis(sample_financial_bill, sample_bodaboda_profile)

        assert isinstance(res, ImpactResponse)
        assert res.bill_type == "financial"
        assert res.verified is True
        assert res.risk_level == "MEDIUM"
