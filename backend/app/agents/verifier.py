import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.llm_client import call_llm as call_gemini
call_llm = call_gemini
from app.agents.summarizer import summarize_bill_text
from app.database import supabase_admin

logger = logging.getLogger(__name__)


class DiscrepancyItem(BaseModel):
    """Detailed breakdown of a single numerical or citation discrepancy."""
    claim: str = Field(
        description="The claim from the English summary being audited."
    )
    claim_value: Optional[str] = Field(
        default=None,
        description="The specific numeric, monetary, or percentage value claimed in the summary."
    )
    extracted_value: Optional[str] = Field(
        default=None,
        description="The corresponding regex-extracted value for comparison."
    )
    section_ref: Optional[str] = Field(
        default=None,
        description="Relevant legal section or clause citation if available."
    )
    severity: str = Field(
        default="minor",
        description="Severity level: 'minor', 'major', or 'critical'."
    )


class BoundaryCheckItem(BaseModel):
    """Result of auditing specific boundary or edge conditions."""
    check_type: str = Field(
        description="Type of check: 'min_max_cap', 'threshold_trigger', 'temporal_validity', or 'exemption'."
    )
    description: str = Field(
        description="Description of the specific condition evaluated."
    )
    status: str = Field(
        description="Evaluation status: 'passed', 'flagged', or 'not_applicable'."
    )
    details: Optional[str] = Field(
        default=None,
        description="Explanation or citation details supporting the status."
    )


class VerificationResult(BaseModel):
    """Structured Pydantic model for Verification Agent audit result."""
    verified: bool = Field(
        description="True if all numeric claims, section citations, and provisions in the summary accurately match source text and RAG chunks."
    )
    issues: List[str] = Field(
        default_factory=list,
        description="List of specific discrepancies, hallucinated numbers, unverified citations, or failed boundary checks flagged."
    )
    confidence: float = Field(
        description="Overall verification confidence score between 0.0 and 1.0."
    )
    discrepancies: List[DiscrepancyItem] = Field(
        default_factory=list,
        description="Detailed list of flagged discrepancy items."
    )
    boundary_checks: List[BoundaryCheckItem] = Field(
        default_factory=list,
        description="Audit results for min/max caps, threshold triggers, temporal validity, and exemptions."
    )


VERIFIER_SYSTEM_INSTRUCTION = """
You are a meticulous legal audit assistant for Hustleyetu in Kenya.
Your job is to audit an AI-generated English bill summary against:
1. Pre-extracted regex values (percentages, monetary amounts, fees, dates)
2. Grounded source legislative RAG chunks (provisions, definitions, penalties, schedules)

MANDATORY AUDIT CHECKLIST:
1. NUMERIC & MONETARY FIDELITY: Verify all percentages (%), monetary figures (KES/shillings), and fees match regex and source text.
2. SECTION CITATION INTEGRITY: Verify that all cited sections (e.g. 'Rule 4', 'Section 12', 'Schedule 1') exist in the source chunks and accurately represent what is claimed.
3. HALLUCINATION DETECTION: Flag any fabricated rules, mandates, or provisions not found in the source chunks.
4. BOUNDARY & EDGE CONDITIONS AUDIT:
   - Min/Max Caps: Verify upper/lower monetary or time limits (e.g. maximum fine caps, late fee caps).
   - Threshold Triggers: Verify qualifying thresholds (e.g. vehicle age thresholds, private vs commercial distinction, engine capacity).
   - Temporal Validity: Verify commencement dates, transition grace periods, inspection renewal intervals.
   - Exemptions: Verify explicit exclusions (e.g. military/police vehicles, electric vehicles, diplomatic, agricultural machinery).

SCORING RULES:
- If ALL numeric claims, citations, and boundary conditions match accurately: set verified = True and confidence >= 0.90.
- If minor ambiguities or missing non-critical details exist: set verified = True with confidence between 0.70 and 0.85.
- If major contradictions, false numeric figures, or hallucinated mandates exist: set verified = False and confidence < 0.60.
"""


def verify_summary_claims(
    summary_en: str,
    regex_extractions: Optional[List[Dict[str, Any]]] = None,
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
    extracted_text: Optional[str] = None,
    bill_id: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> VerificationResult:
    """
    Verify numerical claims, section citations, and boundary conditions in an English summary
    against regex-extracted values, source RAG chunks, and full legislative text using Gemini.

    Args:
        summary_en: English summary text to audit.
        regex_extractions: List of regex extraction dicts (percentages, KES amounts, dates).
        rag_chunks: Retrieved RAG grounding chunks from pgvector.
        extracted_text: Full extracted text of the bill for ground-truth cross-checking.
        bill_id: Optional UUID of the bill for usage logging.
        model: Target Gemini model name (default: gemini-2.5-flash).

    Returns:
        VerificationResult Pydantic object.
    """
    if not summary_en or not summary_en.strip():
        raise ValueError("English summary text is empty or missing for verification.")

    if not regex_extractions:
        logger.warning("No regex extractions provided for verification. Audit relies entirely on LLM internal consistency and RAG chunks.")

    prompt_content = [
        f"ENGLISH SUMMARY TO AUDIT:\n{summary_en}",
    ]

    if extracted_text:
        prompt_content.append(f"FULL ORIGINAL LEGISLATIVE TEXT:\n{extracted_text[:100000]}")

    if rag_chunks:
        chunk_lines = []
        for i, c in enumerate(rag_chunks):
            label = c.get('section_ref') or f"Chunk {c.get('chunk_index', i)}"
            chunk_lines.append(f"[{label}]:\n{c.get('chunk_text', '')}")
        formatted_chunks = "\n---\n".join(chunk_lines)
        prompt_content.append(f"HIGHLIGHTED RAG CHUNKS:\n{formatted_chunks}")

    if regex_extractions:
        prompt_content.append(f"REGEX-EXTRACTED VALUES FROM ORIGINAL BILL:\n{regex_extractions}")

    prompt_content.append(
        "Audit every numeric claim, section citation, and boundary condition (caps, thresholds, temporal validity, exemptions) against the original legislative text and highlighted chunks. "
        "Output structured JSON matching the VerificationResult schema."
    )

    full_prompt = "\n\n".join(prompt_content)

    response = call_gemini(
        prompt=full_prompt,
        system_instruction=VERIFIER_SYSTEM_INSTRUCTION,
        model=model,
        temperature=0.1,  # Low temperature for strict audit consistency
        response_schema=VerificationResult,
        response_mime_type="application/json",
        agent_name="verifier",
        bill_id=bill_id,
    )

    if response.parsed and isinstance(response.parsed, VerificationResult):
        result = response.parsed
    elif response.parsed and isinstance(response.parsed, dict):
        result = VerificationResult(**response.parsed)
    else:
        try:
            data = json.loads(response.text)
            result = VerificationResult(**data)
        except Exception as e:
            logger.error(f"Failed to parse VerificationResult JSON from response text: {e}")
            raise ValueError(f"Gemini response could not be parsed as VerificationResult: {response.text}") from e

    # Clamp confidence between 0.0 and 1.0
    result.confidence = max(0.0, min(1.0, float(result.confidence)))
    return result


def verify_bill_claims(
    bill_id: str,
    force: bool = False,
    max_retries: int = 2,
    model: str = "gemini-2.5-flash",
) -> VerificationResult:
    """
    Fetch a bill from Supabase, run the Verification Agent with a max-2-retries feedback loop,
    and update the verification score and ai_status='verified'.

    Args:
        bill_id: UUID of the bill in Supabase `bills` table.
        force: If True, re-runs verification even if already verified.
        max_retries: Maximum number of re-summarization feedback retries if verification fails.
        model: Target Gemini model name.

    Returns:
        VerificationResult object.
    """
    # 1. Fetch bill record
    res = supabase_admin.table("bills").select("id, extracted_text, ai_summary_en, regex_extractions, ai_status, bill_type, verification_score").eq("id", bill_id).execute()
    if not res.data:
        raise ValueError(f"Bill with ID '{bill_id}' not found in database.")

    bill_data = res.data[0]
    ai_status = bill_data.get("ai_status", "")

    # Idempotency check: skip verification if already verified/translated unless force=True
    if not force and ai_status in ("verified", "translated"):
        logger.info(f"Bill '{bill_id}' is already verified (ai_status='{ai_status}'). Skipping Gemini API call.")
        existing_score = bill_data.get("verification_score") or 1.00
        return VerificationResult(
            verified=True,
            issues=[],
            confidence=float(existing_score),
            discrepancies=[],
        )

    summary_en = bill_data.get("ai_summary_en")
    regex_extractions = bill_data.get("regex_extractions") or []

    if not summary_en:
        raise ValueError(f"Bill '{bill_id}' does not have an English summary to verify.")

    result: Optional[VerificationResult] = None

    # 2. Retrieve grounded RAG chunks for verification
    rag_chunks = []
    try:
        from app.services.embedder import retrieve_relevant_chunks
        rag_chunks = retrieve_relevant_chunks(
            bill_id=bill_id,
            query="penalties, fees, exemptions, threshold criteria, effective dates, section citations, requirements, licensing, salvage",
            top_k=12,
        )
        if rag_chunks:
            logger.info(f"Retrieved {len(rag_chunks)} RAG chunks for verification of bill '{bill_id}'.")
    except Exception as rag_err:
        logger.warning(f"RAG retrieval skipped during verification for bill '{bill_id}': {rag_err}")

    # 3. Feedback loop: verify summary and retry summarizer if verification fails (up to max_retries)
    for retry in range(max_retries + 1):
        result = verify_summary_claims(
            summary_en=summary_en,
            regex_extractions=regex_extractions,
            rag_chunks=rag_chunks,
            extracted_text=bill_data.get("extracted_text") or "",
            bill_id=bill_id,
            model=model,
        )

        if result.verified or retry >= max_retries:
            if not result.verified:
                logger.warning(
                    f"Bill '{bill_id}' verification failed after {retry + 1} attempts. "
                    f"Storing bill with verification_score={result.confidence} and issues={result.issues}."
                )
            break

        logger.info(
            f"Verification attempt {retry + 1}/{max_retries + 1} failed for bill '{bill_id}' with issues: {result.issues}. "
            f"Triggering re-summarization feedback loop..."
        )
        try:
            revised_summary = summarize_bill_text(
                extracted_text=bill_data.get("extracted_text") or "",
                regex_extractions=regex_extractions,
                rag_chunks=rag_chunks,
                bill_type=bill_data.get("bill_type") or "financial",
                bill_id=bill_id,
                model=model,
            )
            summary_en = revised_summary.summary_en
            # Update database with revised summary before re-verifying
            supabase_admin.table("bills").update({
                "ai_summary_en": summary_en,
                "ai_status": "summarized",
            }).eq("id", bill_id).execute()
        except Exception as e:
            logger.error(f"Failed to re-summarize bill '{bill_id}' during verification retry loop: {e}")
            break

    if result is None:
        raise RuntimeError(f"Verification loop failed to produce a result for bill '{bill_id}'.")

    # 3. Update verification score and set ai_status in database
    new_status = "verified" if result.verified else "failed"
    supabase_admin.table("bills").update({
        "verification_score": round(result.confidence, 2),
        "ai_status": new_status,
        "ai_error": None if result.verified else f"Verification failed after retries: {result.issues}",
    }).eq("id", bill_id).execute()

    logger.info(f"Successfully verified bill {bill_id}. Verified={result.verified}, Score={result.confidence}, Status={new_status}")
    return result


