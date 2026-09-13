import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.llm_client import call_llm as call_gemini
call_llm = call_gemini
from app.database import supabase_admin
from app.models.hustle_profiles import INDUSTRIES

logger = logging.getLogger(__name__)


class BillSummary(BaseModel):
    """Structured Pydantic model for English bill summarization output."""
    summary_en: str = Field(
        description="2–4 paragraphs (roughly 250–450 words) of plain-language English explaining the whole bill for a general reader: what it is, why it was introduced, its main provisions and mechanisms, who is affected broadly, and key timelines/penalties where present. Use paragraph breaks. Do not focus on a single industry."
    )
    implications_citizens: List[str] = Field(
        description="Bullet points detailing direct impact on citizens, consumers, and riders."
    )
    implications_business: List[str] = Field(
        description="Bullet points detailing direct operational and financial impact on businesses and micro-enterprises."
    )
    industry_tags: List[str] = Field(
        description="List of relevant industries selected ONLY from the canonical taxonomy list."
    )
    source_citations: List[str] = Field(
        description="Explicit legal section/clause citations referenced in the summary (e.g., 'Section 42(1)', 'Part III, Clause 8')."
    )
    key_financial_changes: Optional[List[str]] = Field(
        default=None,
        description="Extracted percentages, tax rates, monetary fees, or financial modifications."
    )
    key_regulatory_changes: Optional[List[str]] = Field(
        default=None,
        description="Extracted regulatory requirements, permit mandates, compliance deadlines, or penalties."
    )


SUMMARIZER_SYSTEM_INSTRUCTION = f"""
You are an expert legislative analyst and civic technology assistant for Hustleyetu in Kenya.
Your task is to analyze proposed legislation (bills, acts, county regulations) and generate a clear, objective, plain-language English summary tailored for Kenyan citizens and micro-entrepreneurs.

STRICT CONSTRAINTS:
1. Provide a comprehensive, multi-paragraph English summary (`summary_en`). The `summary_en` MUST be 2–4 paragraphs (roughly 250–450 words), general-purpose, and standalone-readable without sector-specific impact context. Use paragraph breaks between paragraphs.
2. List direct implications for everyday citizens (`implications_citizens`).
3. List direct implications for small businesses and micro-enterprises (`implications_business`).
4. Select industry tags ONLY from this canonical list:
{INDUSTRIES}
Do NOT invent new tag names outside this list. Select 1 to 4 most applicable industries.
5. Include explicit source citations (e.g., "Section 12(b)", "Clause 4", "Schedule 2") in `source_citations`.
6. For financial/hybrid bills, detail tax rates, monetary fees, and duty changes in `key_financial_changes`.
7. For regulatory/hybrid bills, detail compliance obligations, safety permits, and penalties in `key_regulatory_changes`.
8. Maintain absolute fidelity to the source text and regex extractions. Do not fabricate figures.
"""


def summarize_bill_text(
    extracted_text: str,
    regex_extractions: Optional[List[Dict[str, Any]]] = None,
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
    bill_type: str = "financial",
    bill_id: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> BillSummary:
    """
    Generate a structured BillSummary using Gemini 2.5 Flash grounded by RAG chunks and regex extractions.

    Args:
        extracted_text: The full or chunked extracted text of the bill.
        regex_extractions: Pre-extracted regex values (percentages, KES amounts, dates).
        rag_chunks: Retrieved RAG grounding chunks from pgvector.
        bill_type: 'financial', 'regulatory', or 'hybrid'.
        bill_id: Optional UUID of the bill for logging.
        model: Target Gemini model name.

    Returns:
        BillSummary Pydantic object.
    """
    if len(extracted_text) > 100000:
        logger.warning(
            f"Bill text truncated from {len(extracted_text)} to 100000 characters for summarization."
        )

    prompt_content = [
        f"BILL TYPE: {bill_type.upper()}",
        f"EXTRACTED BILL TEXT:\n{extracted_text[:100000]}",
    ]

    if rag_chunks:
        formatted_chunks = "\n---\n".join([
            f"[{c.get('section_ref') or f'Chunk {c.get('chunk_index', i)}'}]:\n{c.get('chunk_text', '')}"
            for i, c in enumerate(rag_chunks)
        ])
        prompt_content.append(f"GROUNDED RAG CHUNKS (KEY PROVISIONS & CITATIONS):\n{formatted_chunks}")

    if regex_extractions:
        prompt_content.append(f"PRE-EXTRACTED REGEX VALUES:\n{regex_extractions}")

    prompt_content.append(
        "Generate a structured summary following the JSON schema, selecting industry tags exclusively from the canonical list."
    )

    full_prompt = "\n\n".join(prompt_content)

    response = call_gemini(
        prompt=full_prompt,
        system_instruction=SUMMARIZER_SYSTEM_INSTRUCTION,
        model=model,
        temperature=0.2,
        response_schema=BillSummary,
        response_mime_type="application/json",
        agent_name="summarizer",
        bill_id=bill_id,
    )

    if response.parsed and isinstance(response.parsed, BillSummary):
        summary = response.parsed
    elif response.parsed and isinstance(response.parsed, dict):
        summary = BillSummary(**response.parsed)
    else:
        # Fallback parsing from text if response.parsed was not populated directly
        try:
            data = json.loads(response.text)
            summary = BillSummary(**data)
        except Exception as e:
            logger.error(f"Failed to parse BillSummary JSON from response text: {e}")
            raise ValueError(f"Gemini response could not be parsed as BillSummary: {response.text}") from e

    # Sanitize industry tags to ensure only valid canonical tags remain
    valid_tags = [tag for tag in summary.industry_tags if tag in INDUSTRIES]
    if not valid_tags:
        logger.warning(
            f"LLM returned no valid canonical industry tags (raw: {summary.industry_tags}). "
            f"Applying default MVP fallback tag 'Transport & Logistics'."
        )
        valid_tags = ["Transport & Logistics"]  # Default fallback tag if none matched canonical list
    summary.industry_tags = valid_tags

    return summary


def summarize_bill(
    bill_id: str,
    force: bool = False,
    model: str = "gemini-2.5-flash",
) -> BillSummary:
    """
    Fetch a bill from Supabase, retrieve grounding RAG chunks, run the Summarization Agent, and update the database.

    Args:
        bill_id: UUID of the bill in Supabase `bills` table.
        force: If True, re-runs summarization even if already summarized.
        model: Gemini model name.

    Returns:
        Generated BillSummary object.
    """
    # 1. Fetch bill record
    res = supabase_admin.table("bills").select("*").eq("id", bill_id).execute()
    if not res.data:
        raise ValueError(f"Bill with ID '{bill_id}' not found in database.")

    bill_data = res.data[0]
    ai_status = bill_data.get("ai_status", "")

    # Idempotency check: skip Gemini API call if already summarized unless force=True
    if not force and ai_status in ("summarized", "translated", "verified"):
        logger.info(f"Bill '{bill_id}' is already processed (ai_status='{ai_status}'). Skipping re-summarization.")
        existing_summary_en = bill_data.get("ai_summary_en") or ""
        existing_tags_res = supabase_admin.table("bill_tags").select("industry_tag").eq("bill_id", bill_id).execute()
        existing_tags = [row["industry_tag"] for row in (existing_tags_res.data or [])]
        return BillSummary(
            summary_en=existing_summary_en,
            implications_citizens=[],
            implications_business=[],
            industry_tags=existing_tags or ["Transport & Logistics"],
            source_citations=[],
        )

    extracted_text = bill_data.get("extracted_text") or ""
    regex_extractions = bill_data.get("regex_extractions") or []
    bill_type = bill_data.get("bill_type") or "financial"

    if not extracted_text:
        raise ValueError(f"Bill '{bill_id}' has no extracted text to summarize.")

    # 2. Retrieve grounded RAG chunks from pgvector
    rag_chunks = []
    try:
        from app.services.embedder import retrieve_relevant_chunks
        rag_chunks = retrieve_relevant_chunks(
            bill_id=bill_id,
            query="key provisions, requirements, compliance mandates, penalties, fees, exemptions, and definitions",
            top_k=10,
        )
        if rag_chunks:
            logger.info(f"Retrieved {len(rag_chunks)} RAG grounding chunks for bill '{bill_id}'.")
    except Exception as rag_err:
        logger.warning(f"RAG retrieval skipped for bill '{bill_id}': {rag_err}")

    # 3. Run summarizer logic with RAG grounding context
    summary = summarize_bill_text(
        extracted_text=extracted_text,
        regex_extractions=regex_extractions,
        rag_chunks=rag_chunks,
        bill_type=bill_type,
        bill_id=bill_id,
        model=model,
    )

    # 3. Update bills table with ai_summary_en and status='summarized'
    supabase_admin.table("bills").update({
        "ai_summary_en": summary.summary_en,
        "ai_status": "summarized",
        "ai_error": None,
    }).eq("id", bill_id).execute()

    # 4. Insert/update bill_tags with transaction error handling
    try:
        supabase_admin.table("bill_tags").delete().eq("bill_id", bill_id).execute()
        tag_rows = [
            {"bill_id": bill_id, "industry_tag": tag, "confidence": 1.00}
            for tag in summary.industry_tags
        ]
        if tag_rows:
            supabase_admin.table("bill_tags").insert(tag_rows).execute()
    except Exception as e:
        logger.error(f"Failed to update bill_tags for bill '{bill_id}': {e}")
        raise

    logger.info(f"Successfully summarized bill {bill_id} and updated database.")
    return summary


