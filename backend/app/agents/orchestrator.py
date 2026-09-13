"""
DAG Orchestrator module for Hustleyetu.
Manages the end-to-end bill processing pipeline: Extraction -> Regex -> Summarization -> Verification -> Translation.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional

from app.agents.summarizer import summarize_bill
from app.agents.verifier import verify_bill_claims
from app.agents.translator import translate_bill
from app.agents.impact_agent import compute_financial_impact_analysis
from app.utils.regex_extractor import extract_financial_values
from app.database import supabase_admin

logger = logging.getLogger(__name__)


@dataclass
class PipelineState:
    """Dataclass holding execution metrics and status for a bill pipeline run."""
    bill_id: str
    status: str = "pending"  # pending, extracted, embedded, summarized, verified, translated, failed
    step_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    updated_at: Optional[str] = None


def run_pipeline(bill_id: str, force: bool = False) -> PipelineState:
    """
    Executes the full DAG pipeline for a bill:
    1. Regex Extraction (from pre-extracted bill text in database)
    2. Structural Chunking & Vector Embedding (pgvector bill_chunks table)
    3. Summarization Agent (grounded by RAG chunks)
    4. Verification Agent (multi-dimensional audit + checklist + feedback loop)
    5. Translation Agent (English -> Swahili)
    6. Pre-generation & Caching of Impact Scenario / Compliance Guide

    Args:
        bill_id: ID of the bill to process in Supabase.
        force: If True, re-runs all stages regardless of current ai_status.

    Returns:
        PipelineState dataclass instance.
    """
    state = PipelineState(
        bill_id=bill_id,
        updated_at=datetime.now(timezone.utc).isoformat()
    )

    logger.info(f"Starting DAG pipeline run for bill_id: {bill_id} (force={force})")

    # 1. Fetch bill record from Supabase
    bill = None
    if supabase_admin:
        try:
            res = supabase_admin.from_("bills").select("*").eq("id", bill_id).execute()
            if res.data and len(res.data) > 0:
                bill = res.data[0]
        except Exception as e:
            logger.error(f"Error fetching bill {bill_id} from Supabase: {e}")

        if not bill:
            state.status = "failed"
            state.error_message = f"Bill with id '{bill_id}' not found in database."
            logger.error(state.error_message)
            return state
    else:
        # Offline/testing mode fallback when supabase_admin is explicitly None
        bill = {
            "id": bill_id,
            "title": "Mock Bill (offline fallback)",
            "extracted_text": "Sample text for bill testing.",
            "ai_status": "ingested",
            "regex_extractions": [],
        }

    current_status = bill.get("ai_status", "ingested")
    extracted_text = bill.get("extracted_text", "")

    try:
        # Step 1: Regex Extraction
        existing_regex = bill.get("regex_extractions")

        if force or not existing_regex or current_status == "ingested":
            logger.info(f"Pipeline Stage 1 [Regex Extraction] executing for bill_id: {bill_id}")
            if not extracted_text:
                logger.warning(f"No extracted_text for bill {bill_id}; skipping regex extraction.")
                state.step_results["regex_extraction"] = {
                    "status": "skipped",
                    "reason": "no extracted text"
                }
            else:
                regex_results = extract_financial_values(extracted_text)

                if supabase_admin:
                    supabase_admin.from_("bills").update({
                        "regex_extractions": regex_results,
                        "ai_status": "extracted"
                    }).eq("id", bill_id).execute()

                state.step_results["regex_extraction"] = {
                    "count": len(regex_results),
                    "status": "success"
                }
                state.status = "extracted"
        else:
            logger.info(f"Pipeline Stage 1 [Regex Extraction] skipped (already extracted)")
            state.step_results["regex_extraction"] = {"status": "skipped"}
            state.status = "extracted"

        # Step 2: Vector Embedding & Chunking
        logger.info(f"Pipeline Stage 2 [Vector Chunking & Embedding] executing for bill_id: {bill_id}")
        if extracted_text:
            try:
                from app.services.embedder import embed_and_store_bill_chunks
                stored_chunks = embed_and_store_bill_chunks(bill_id=bill_id, extracted_text=extracted_text, force=force)
                state.step_results["embedding"] = {
                    "chunks_count": len(stored_chunks),
                    "status": "success"
                }
                state.status = "embedded"
            except Exception as emb_err:
                logger.error(f"Embedding stage encountered issue for bill {bill_id}: {emb_err}")
                state.step_results["embedding"] = {"status": "error", "error": str(emb_err)}
        else:
            state.step_results["embedding"] = {"status": "skipped", "reason": "no extracted text"}

        # Step 3: Summarization Agent (RAG Grounded)
        logger.info(f"Pipeline Stage 3 [Summarization] executing for bill_id: {bill_id}")
        sum_res = summarize_bill(bill_id, force=force)
        if isinstance(sum_res, dict) and sum_res.get("status") == "error":
            logger.error(f"Summarization failed for bill {bill_id}; aborting pipeline.")
            state.status = "failed"
            state.error_message = f"Summarization failed: {sum_res.get('error', 'unknown error')}"
            _update_failed_status_in_db(bill_id)
            return state

        state.step_results["summarization"] = (
            sum_res.model_dump() if hasattr(sum_res, "model_dump")
            else (sum_res if isinstance(sum_res, dict) else {"summary_en": str(sum_res)})
        )
        state.status = "summarized"

        # Step 4: Verification Agent (RAG Grounded + Checklist)
        logger.info(f"Pipeline Stage 4 [Verification] executing for bill_id: {bill_id}")
        ver_res = verify_bill_claims(bill_id, force=force)
        if isinstance(ver_res, dict) and ver_res.get("status") == "error":
            logger.error(f"Verification failed for bill {bill_id}; aborting pipeline.")
            state.status = "failed"
            state.error_message = f"Verification failed: {ver_res.get('error', 'unknown error')}"
            _update_failed_status_in_db(bill_id)
            return state

        is_verified = (
            ver_res.verified if hasattr(ver_res, "verified")
            else (ver_res.get("verified", False) if isinstance(ver_res, dict) else False)
        )
        if not is_verified:
            issues = (
                ver_res.issues if hasattr(ver_res, "issues")
                else (ver_res.get("issues", []) if isinstance(ver_res, dict) else [])
            )
            logger.error(f"Verification audit failed for bill {bill_id} with issues: {issues}; aborting pipeline.")
            state.status = "failed"
            state.error_message = f"Verification audit failed: {issues}"
            _update_failed_status_in_db(bill_id)
            return state

        state.step_results["verification"] = (
            ver_res.model_dump() if hasattr(ver_res, "model_dump")
            else (ver_res if isinstance(ver_res, dict) else {"verified": True})
        )
        state.status = "verified"

        # Step 5: Translation Agent
        logger.info(f"Pipeline Stage 5 [Translation] executing for bill_id: {bill_id}")
        trans_res = translate_bill(bill_id, force=force)
        if isinstance(trans_res, dict) and trans_res.get("status") == "error":
            logger.error(f"Translation failed for bill {bill_id}; aborting pipeline.")
            state.status = "failed"
            state.error_message = f"Translation failed: {trans_res.get('error', 'unknown error')}"
            _update_failed_status_in_db(bill_id)
            return state

        state.step_results["translation"] = (
            trans_res.model_dump() if hasattr(trans_res, "model_dump")
            else (trans_res if isinstance(trans_res, dict) else {"summary_sw": str(trans_res)})
        )
        state.status = "translated"

        # Step 6: Pre-generate & cache impact scenario/compliance guide
        logger.info(f"Pipeline Stage 6 [Impact Cache Pre-generation] executing for bill_id: {bill_id}")
        if supabase_admin:
            try:
                bill_record = {
                    "id": bill_id,
                    "title": bill.get("title", ""),
                    "bill_type": bill.get("bill_type", "financial"),
                    "extracted_text": extracted_text[:4000],
                    "source_url": bill.get("source_url", ""),
                }
                impact_res = compute_financial_impact_analysis(bill_record)
                impact_dict = impact_res.model_dump()
                supabase_admin.table("tier_impact_cache").upsert({
                    "bill_id": bill_id,
                    "industry": "ALL",
                    "tier_label": "ALL",
                    "impact_data": impact_dict
                }, on_conflict="bill_id, industry, tier_label").execute()
                state.step_results["impact_cache"] = {"status": "success"}
                logger.info(f"Pre-generated impact scenario cached in tier_impact_cache for bill {bill_id}.")
            except Exception as imp_err:
                logger.warning(f"Impact pre-generation encountered non-fatal issue for bill {bill_id}: {imp_err}")
                state.step_results["impact_cache"] = {"status": "error", "error": str(imp_err)}

        state.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"DAG pipeline run completed successfully for bill_id: {bill_id} with status: {state.status}")
        return state

    except Exception as e:
        logger.error(f"Pipeline failure for bill_id {bill_id}: {e}", exc_info=True)
        state.status = "failed"
        state.error_message = str(e)
        state.updated_at = datetime.now(timezone.utc).isoformat()
        _update_failed_status_in_db(bill_id)
        return state


def _update_failed_status_in_db(bill_id: str) -> None:
    """Helper function to set bill ai_status to 'failed' in Supabase."""
    if supabase_admin:
        try:
            supabase_admin.from_("bills").update({
                "ai_status": "failed"
            }).eq("id", bill_id).execute()
        except Exception as db_err:
            logger.error(f"Failed to update bill status to 'failed' in Supabase: {db_err}")


async def run_pipeline_async(bill_id: str, force: bool = False) -> PipelineState:
    """Async wrapper around run_pipeline using thread pool to avoid blocking the event loop."""
    return await asyncio.to_thread(run_pipeline, bill_id, force=force)
