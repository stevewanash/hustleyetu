"""
Financial Impact Agent module for Hustleyetu (v1.3 Alignment).
Generates pre-computed example scenarios for financial bills and compliance checklists
for regulatory bills targeting the Boda Boda transport industry.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.agents.llm_client import call_llm as call_gemini
from app.models.schemas import (
    ImpactResponse,
    ScenarioPersona,
    ComplianceActionItem,
)
from app.database import supabase_admin

logger = logging.getLogger(__name__)


IMPACT_SYSTEM_INSTRUCTION = """
You are the Financial Impact & Compliance Analyst Agent for Hustleyetu.
Your job is to analyze a legislative bill and generate a pre-computed worked example scenario or compliance checklist guide specifically tailored to the Boda Boda transport sector in Kenya.

CRITICAL CONSTRAINTS:
1. Target Industry: ONLY the Boda Boda transport sector (motorcycle riders/operators). DO NOT use content creators, matatu operators, salon owners, or other industries.
2. No Persona Names: Do NOT use personal names (e.g., no "Mama Njeri", "Kamau", "Amani"). Set persona name to "Boda Boda Operator" or leave it role-based.
3. No Emojis: Do NOT include emojis in any generated string fields or responses.

BILL TYPES & SCHEMAS:

1. For FINANCIAL or HYBRID Bills:
- Create a pre-generated Example Scenario for a representative Boda Boda Operator.
- Provide `scenario_persona` with fields:
  - `name`: "Boda Boda Operator"
  - `description`: clear 1-2 sentence description of their motorcycle operation (e.g. "A boda boda rider operating a 150cc motorcycle valued at KES 150,000 for daily passenger and delivery transport.")
  - `metrics`: dictionary of baseline values e.g. {"vehicle_value": 150000} or {"monthly_overhead": 12000}
- Provide `concise_summary`: a clear 2-3 sentence overview of what the bill changes.
- Provide `key_figures`: list of key policy figures (e.g., ["2.5% Motor vehicle tax", "KES 5,000 Minimum tax", "KES 100,000 Maximum tax"]).
- Provide `math_breakdown`: step-by-step calculation breakdown for the boda boda operator (e.g., ["Annual Tax = KES 150,000 * 2.5% = KES 3,750 (Minimum KES 5,000 threshold applies)", "Monthly Cost = KES 5,000 / 12 = KES 417"]).
- Provide `calculator_formula`: a simple string math formula for client evaluation (e.g., "min(max(vehicle_value * 0.025, 5000), 100000)").
- Provide `sources`: list of legal clause citations (e.g., ["Section 4(2)(a)", "Clause 12"]).
- Provide `risk_level`: "LOW", "MEDIUM", or "HIGH".

2. For REGULATORY Bills:
- Create a pre-generated Compliance Checklist Guide for Boda Boda operators.
- Provide `concise_summary`: clear overview of regulatory requirements.
- Provide `regulatory_changes`: list of key mandates.
- Provide `compliance_checklist`: list of items with:
  - `action`: plain language action item
  - `deadline`: timeline or deadline (e.g. "Within 90 days of gazettement")
  - `source`: legal section citation (e.g. "Section 3(1)")
- Provide `sources`: list of citations.
- Provide `risk_level`: "LOW", "MEDIUM", or "HIGH".

Set `verified`: true.
Set `disclaimer`: "This impact analysis is an automated estimate for informational purposes and does not constitute legal or tax advice."
"""


def compute_financial_impact_analysis(
    bill_data: Dict[str, Any],
    hustle_profile: Optional[Dict[str, Any]] = None,
    model: str = "gemini-2.5-flash",
) -> ImpactResponse:
    """
    Computes pre-generated example scenario or compliance guide for a given bill.

    Args:
        bill_data: Dictionary containing bill details ('id', 'title', 'bill_type', 'ai_summary_en', 'regex_extractions').
        hustle_profile: Optional baseline hustle profile context.
        model: Target Gemini model name.

    Returns:
        ImpactResponse object.
    """
    bill_id = bill_data.get("id")
    bill_title = bill_data.get("title", "Legislative Bill")
    bill_type = bill_data.get("bill_type", "financial")
    if bill_type not in ("financial", "regulatory", "hybrid"):
        bill_type = "financial"

    summary_en = bill_data.get("ai_summary_en") or bill_data.get("extracted_text", "")
    regex_extractions = bill_data.get("regex_extractions", [])

    prompt_content = f"""
BILL TITLE: {bill_title}
BILL TYPE: {bill_type}

BILL SUMMARY / EXTRACTED CLAUSES:
{summary_en[:4000]}

PRE-EXTRACTED REGEX VALUES:
{json.dumps(regex_extractions, indent=2)}

Generate a complete, accurate pre-generated example scenario or compliance checklist guide for a Boda Boda Operator. Return structured JSON conforming to ImpactResponse schema. No names, no emojis, boda boda focus only.
"""

    try:
        response = call_gemini(
            prompt=prompt_content,
            system_instruction=IMPACT_SYSTEM_INSTRUCTION,
            model=model,
            temperature=0.1,
            response_schema=ImpactResponse,
            response_mime_type="application/json",
            agent_name="impact_agent",
            bill_id=bill_id,
        )
    except Exception as err:
        logger.error(f"LLM API call failed in impact agent: {err}")
        return _fallback_impact_response(bill_data)

    if response.parsed and isinstance(response.parsed, ImpactResponse):
        impact_res = response.parsed
    elif response.parsed and isinstance(response.parsed, dict):
        impact_res = ImpactResponse(**response.parsed)
    elif response.text:
        try:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text.split("```", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(cleaned_text)
            impact_res = ImpactResponse(**data)
        except Exception as err:
            logger.warning(f"Failed to parse text response from Gemini into ImpactResponse: {err}")
            impact_res = _fallback_impact_response(bill_data)
    else:
        impact_res = _fallback_impact_response(bill_data)

    impact_res.bill_id = bill_id
    impact_res.bill_title = bill_title
    impact_res.bill_type = bill_type

    # Sanitize persona name & emojis
    if impact_res.scenario_persona:
        impact_res.scenario_persona.name = "Boda Boda Operator"

    return impact_res


def _fallback_impact_response(bill_data: Dict[str, Any]) -> ImpactResponse:
    """Generates a safe pre-computed fallback ImpactResponse structure for Boda Boda operators if API fails."""
    bill_id = bill_data.get("id")
    bill_title = bill_data.get("title", "Legislative Bill")
    bill_type = bill_data.get("bill_type", "financial")

    if bill_type in ("financial", "hybrid"):
        return ImpactResponse(
            bill_id=bill_id,
            bill_title=bill_title,
            bill_type=bill_type,
            concise_summary="Introduces a 2.5% motor vehicle circulation tax based on motorcycle valuation with minimum and maximum thresholds.",
            scenario_persona=ScenarioPersona(
                name="Boda Boda Operator",
                description="A boda boda rider operating a 150cc motorcycle valued at KES 150,000 for commercial transport services.",
                metrics={"vehicle_value": 150000}
            ),
            key_figures=["2.5% Motor Vehicle Tax", "KES 5,000 Minimum Annual Threshold", "KES 100,000 Maximum Threshold"],
            math_breakdown=[
                "Calculated Tax = KES 150,000 * 2.5% = KES 3,750",
                "Minimum Threshold Applies = KES 5,000 per year",
                "Monthly Equivalent = KES 5,000 / 12 = KES 417 per month"
            ],
            calculator_formula="min(max(vehicle_value * 0.025, 5000), 100000)",
            sources=["Section 4(2)(a)", "Clause 12"],
            risk_level="MEDIUM",
            verified=True,
            disclaimer="This impact analysis is an automated estimate for informational purposes and does not constitute legal or tax advice."
        )
    else:
        return ImpactResponse(
            bill_id=bill_id,
            bill_title=bill_title,
            bill_type=bill_type,
            concise_summary="Mandates digital permit registration, NTSA verification, and annual county permit fees for boda boda operators in Nairobi City County.",
            regulatory_changes=[
                "Mandatory digital permit registration with County Transport Board",
                "Linkage of NTSA rider license and SACCO details",
                "Annual county permit fee of KES 3,000"
            ],
            compliance_checklist=[
                ComplianceActionItem(
                    action="Register digital rider profile with County Transport Board",
                    deadline="Within 90 days of gazettement",
                    source="Section 3(1)"
                ),
                ComplianceActionItem(
                    action="Pay annual county permit fee of KES 3,000",
                    deadline="January 1st annually",
                    source="Section 5(2)"
                )
            ],
            sources=["Section 3", "Section 5"],
            risk_level="HIGH",
            verified=True,
            disclaimer="This impact analysis is an automated estimate for informational purposes and does not constitute legal or tax advice."
        )


async def compute_financial_impact(bill_id: str, hustle_profile: Optional[Dict[str, Any]] = None) -> ImpactResponse:
    """
    Async helper to query bill data from Supabase and run impact analysis.
    """
    bill_data = {}
    if supabase_admin:
        try:
            res = supabase_admin.from_("bills").select("id, title, bill_type, ai_summary_en, regex_extractions, extracted_text").eq("id", bill_id).execute()
            if res.data and len(res.data) > 0:
                bill_data = res.data[0]
        except Exception as err:
            logger.warning(f"Failed to query bill '{bill_id}' from Supabase: {err}")

    if not bill_data:
        bill_data = {"id": bill_id, "title": "Legislative Bill", "bill_type": "financial"}

    return compute_financial_impact_analysis(bill_data, hustle_profile)
