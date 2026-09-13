import json
import logging
import re
from typing import Optional
from pydantic import BaseModel, Field

from app.agents.llm_client import call_llm as call_gemini
call_llm = call_gemini
from app.database import supabase_admin

logger = logging.getLogger(__name__)


class SwahiliTranslation(BaseModel):
    """Structured output model for Swahili translation."""
    summary_sw: str = Field(
        description="Natural, clear, grammatically correct Swahili translation of the English bill summary."
    )


TRANSLATOR_SYSTEM_INSTRUCTION = """
You are an expert English-to-Swahili translator specializing in legal, financial, and civic technology translation for Kenya.
Your task is to translate an English legislative bill summary into natural, accessible, grammatically correct Swahili.

STRICT CONSTRAINTS:
1. Preserve all legal section/clause citations EXACTLY as written (e.g., "Section 12(1)", "Clause 4", "Schedule 2"). Do NOT translate "Section" or "Clause" if it alters legal section referencing clarity.
2. Preserve all numerical figures, monetary amounts (KES, Ksh), percentages (%), and dates EXACTLY as written.
3. Use clear, modern Swahili that standard citizens and bodaboda riders can easily understand.
4. Maintain paragraph, list, and formatting structure of the original English summary.
5. Provide a structured JSON response matching the SwahiliTranslation schema.
"""


def translate_summary_text(
    summary_en: str,
    bill_id: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Translate an English bill summary to Swahili using Gemini 2.5 Flash.

    Args:
        summary_en: English summary text.
        bill_id: Optional UUID of the bill for usage logging attribution.
        model: Target Gemini model name.

    Returns:
        Translated Swahili text.
    """
    if not summary_en or not summary_en.strip():
        raise ValueError("English summary text is empty or missing.")

    prompt = f"ENGLISH SUMMARY TO TRANSLATE:\n{summary_en}\n\nProvide the complete Swahili translation in the structured JSON format."

    response = call_gemini(
        prompt=prompt,
        system_instruction=TRANSLATOR_SYSTEM_INSTRUCTION,
        model=model,
        temperature=0.1,  # Low temperature for accurate translation
        response_schema=SwahiliTranslation,
        response_mime_type="application/json",
        agent_name="translator",
        bill_id=bill_id,
    )

    if response.parsed and isinstance(response.parsed, SwahiliTranslation):
        swahili_text = response.parsed.summary_sw
    elif response.parsed and isinstance(response.parsed, dict):
        swahili_text = response.parsed.get("summary_sw", "")
    else:
        try:
            data = json.loads(response.text)
            swahili_text = data.get("summary_sw") or response.text
        except Exception:
            swahili_text = response.text or ""

    swahili_text = swahili_text.strip()
    if not swahili_text:
        raise ValueError("Gemini returned empty translation response.")

    # Post-translation sanity check: verify section citations were preserved
    citations = set(re.findall(r'(?:Section|Clause|Schedule|Part)\s+\d+(?:\(\w+\))?', summary_en, re.IGNORECASE))
    missing_citations = [c for c in citations if c not in swahili_text]
    if missing_citations:
        logger.warning(
            f"Swahili translation may have omitted legal citations present in English source: {missing_citations}"
        )

    return swahili_text


def translate_bill(
    bill_id: str,
    force: bool = False,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Fetch a bill's English summary from Supabase, translate it to Swahili, and update the database.

    State Machine Note:
    In Phase 2 baseline, status transitions directly from 'summarized' (or 'verified') to 'translated'.
    If verification was run prior to translation, status still becomes 'translated' while preserving
    verification_score.

    Args:
        bill_id: UUID of the bill in Supabase `bills` table.
        force: If True, re-runs translation even if already translated.
        model: Target Gemini model name.

    Returns:
        Generated Swahili translation text.
    """
    # 1. Fetch bill record with ai_status and ai_summary_sw for idempotency check
    res = supabase_admin.table("bills").select("id, ai_summary_en, ai_summary_sw, ai_status").eq("id", bill_id).execute()
    if not res.data:
        raise ValueError(f"Bill with ID '{bill_id}' not found in database.")

    bill_data = res.data[0]
    ai_status = bill_data.get("ai_status", "")

    # Idempotency check: skip Gemini translation if already translated unless force=True
    if not force and ai_status == "translated":
        logger.info(f"Bill '{bill_id}' is already translated. Skipping Gemini API call.")
        return bill_data.get("ai_summary_sw") or ""

    summary_en = bill_data.get("ai_summary_en")
    if not summary_en:
        raise ValueError(f"Bill '{bill_id}' does not have an English summary (ai_summary_en) to translate.")

    # 2. Run translation logic
    summary_sw = translate_summary_text(summary_en=summary_en, bill_id=bill_id, model=model)

    # 3. Update database with ai_summary_sw and ai_status='translated'
    supabase_admin.table("bills").update({
        "ai_summary_sw": summary_sw,
        "ai_status": "translated",
        "ai_error": None,
    }).eq("id", bill_id).execute()

    logger.info(f"Successfully translated bill {bill_id} summary to Swahili and updated database.")
    return summary_sw


