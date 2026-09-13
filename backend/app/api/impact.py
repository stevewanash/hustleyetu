import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ImpactResponse
from app.agents.impact_agent import compute_financial_impact_analysis
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/impact", tags=["Impact"])


@router.get("/{bill_id}", response_model=ImpactResponse)
async def get_bill_impact(bill_id: str):
    """
    Retrieves the pre-generated example scenario or compliance checklist guide for a bill.
    Looks up pre-computed impact data from tier_impact_cache (industry='ALL', tier_label='ALL').
    If not cached, generates the impact data on-the-fly and caches it for future calls.
    """
    bill_data = None
    cached_impact = None

    # 1. Check Supabase DB for cached impact
    if supabase_admin:
        try:
            # Query cache table first (<200ms lookup)
            cache_res = (
                supabase_admin.table("tier_impact_cache")
                .select("impact_data")
                .eq("bill_id", bill_id)
                .eq("industry", "ALL")
                .eq("tier_label", "ALL")
                .execute()
            )
            if cache_res.data and len(cache_res.data) > 0:
                cached_impact = cache_res.data[0].get("impact_data")
        except Exception as err:
            logger.warning(f"Error querying tier_impact_cache for bill '{bill_id}': {err}")

        # Fetch bill details for metadata and pdf_url
        try:
            bill_res = (
                supabase_admin.table("bills")
                .select("id, title, bill_type, ai_summary_en, regex_extractions, extracted_text, source_url, pdf_storage_path")
                .eq("id", bill_id)
                .execute()
            )
            if bill_res.data and len(bill_res.data) > 0:
                bill_data = bill_res.data[0]
        except Exception as err:
            logger.error(f"Error querying bill '{bill_id}' from database: {err}")

    # Fallback for offline / mock testing
    if not bill_data and (getattr(settings, "TESTING", False) or bill_id.startswith("mock-")):
        bill_data = {
            "id": bill_id,
            "title": "Mock Legislative Bill 2026",
            "bill_type": "financial",
            "ai_summary_en": "Mock legislative bill summary for testing.",
            "regex_extractions": [],
            "source_url": "https://example.com/mock.pdf",
            "pdf_storage_path": None,
        }

    if not bill_data and not cached_impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill '{bill_id}' not found"
        )

    # 2. If cached impact exists, format and return
    if cached_impact:
        if isinstance(cached_impact, dict):
            # Ensure bill_id and title are attached if available
            if bill_data:
                cached_impact["bill_id"] = bill_data.get("id")
                cached_impact["bill_title"] = bill_data.get("title")
                cached_impact["pdf_url"] = bill_data.get("source_url") or bill_data.get("pdf_storage_path")
            return ImpactResponse(**cached_impact)

    # 3. If cache miss, generate pre-computed scenario and store in cache
    impact_res = compute_financial_impact_analysis(bill_data or {"id": bill_id, "title": "Legislative Bill"})
    if bill_data:
        impact_res.pdf_url = bill_data.get("source_url") or bill_data.get("pdf_storage_path")

    if supabase_admin and bill_data:
        try:
            impact_dict = impact_res.model_dump()
            supabase_admin.table("tier_impact_cache").upsert({
                "bill_id": bill_id,
                "industry": "ALL",
                "tier_label": "ALL",
                "impact_data": impact_dict
            }, on_conflict="bill_id, industry, tier_label").execute()
            logger.info(f"Successfully cached impact scenario for bill '{bill_id}'")
        except Exception as err:
            logger.warning(f"Failed to upsert tier_impact_cache for bill '{bill_id}': {err}")

    return impact_res
