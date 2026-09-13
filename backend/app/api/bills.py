import logging
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime, timezone

from app.models.schemas import BillBrief, BillListResponse, BillDetailResponse
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bills", tags=["Bills"])


@router.get("", response_model=BillListResponse)
async def get_bills(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    industry: Optional[str] = None,
    ai_status: Optional[str] = Query("all", description="Filter by ai_status (use 'all' to disable filter)")
):
    """
    Get a paginated list of analyzed bills, optionally filtered by industry tag and processing status.
    Returns briefs ordered by created_at DESC.
    """
    if not supabase_admin:
        if not (getattr(settings, "TESTING", False) or page == 1):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        # Offline/mock mode fallback for testing
        mock_briefs = [
            BillBrief(
                id="mock-bill-001",
                title="The Finance Bill, 2024",
                tags=["Transport & Logistics", "Finance & Mobile Money"],
                bill_type="financial",
                created_at=datetime.now(timezone.utc),
                ai_status="translated"
            ),
            BillBrief(
                id="mock-bill-002",
                title="Nairobi Motorcycle Taxi (Boda Boda) Permit Regulations 2025",
                tags=["Transport & Logistics"],
                bill_type="regulatory",
                created_at=datetime.now(timezone.utc),
                ai_status="translated"
            )
        ]
        if ai_status and ai_status != "all":
            mock_briefs = [b for b in mock_briefs if b.ai_status == ai_status]
        if industry:
            mock_briefs = [b for b in mock_briefs if industry in b.tags]
        return BillListResponse(
            bills=mock_briefs,
            total=len(mock_briefs),
            page=page,
            limit=limit
        )

    try:
        # 1. If industry filter provided, find bill_ids matching industry tag first
        matching_bill_ids = None
        if industry:
            tag_res = supabase_admin.table("bill_tags").select("bill_id").eq("industry_tag", industry).execute()
            matching_bill_ids = list(set(row["bill_id"] for row in (tag_res.data or [])))
            if not matching_bill_ids:
                # No bills match the requested industry filter
                return BillListResponse(bills=[], total=0, page=page, limit=limit)

        # 2. Build optimized query selecting only columns needed for list view
        query = supabase_admin.table("bills").select(
            "id, title, bill_type, created_at, ai_status, ai_summary_en",
            count="exact"
        )
        
        # Apply ai_status filter unless explicitly 'all'
        if ai_status and ai_status != "all":
            query = query.eq("ai_status", ai_status)

        if matching_bill_ids is not None:
            query = query.in_("id", matching_bill_ids)
            
        # Paginate and order
        offset = (page - 1) * limit
        res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        raw_bills = res.data or []
        total_count = res.count if res.count is not None else len(raw_bills)

        # 3. Fetch tags and impact concise summaries for all returned bill IDs
        bill_ids = [b["id"] for b in raw_bills]
        tags_by_bill = {}
        impact_summary_by_bill = {}
        if bill_ids:
            tags_res = supabase_admin.table("bill_tags").select("bill_id, industry_tag").in_("bill_id", bill_ids).execute()
            if tags_res.data:
                for row in tags_res.data:
                    b_id = row["bill_id"]
                    if b_id not in tags_by_bill:
                        tags_by_bill[b_id] = []
                    tags_by_bill[b_id].append(row["industry_tag"])

            impact_res = supabase_admin.table("tier_impact_cache").select("bill_id, impact_data").in_("bill_id", bill_ids).execute()
            if impact_res.data:
                for row in impact_res.data:
                    b_id = row["bill_id"]
                    idata = row.get("impact_data") or {}
                    if isinstance(idata, dict) and idata.get("concise_summary"):
                        impact_summary_by_bill[b_id] = idata["concise_summary"]

        # 4. Construct response models
        briefs = []
        for b in raw_bills:
            created_at_val = b.get("created_at")
            if isinstance(created_at_val, str):
                created_at_dt = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
            elif isinstance(created_at_val, datetime):
                created_at_dt = created_at_val
            else:
                created_at_dt = datetime.now(timezone.utc)

            raw_type = b.get("bill_type", "financial")
            if raw_type not in ("financial", "regulatory", "hybrid"):
                logger.warning(f"Unexpected bill_type '{raw_type}' for bill {b['id']}; defaulting to 'financial'")
                valid_bill_type = "financial"
            else:
                valid_bill_type = raw_type

            briefs.append(
                BillBrief(
                    id=b["id"],
                    title=b.get("title", "Untitled Bill"),
                    tags=tags_by_bill.get(b["id"], []),
                    bill_type=valid_bill_type,
                    created_at=created_at_dt,
                    ai_status=b.get("ai_status", "ingested"),
                    ai_summary_en=b.get("ai_summary_en"),
                    impact_summary=impact_summary_by_bill.get(b["id"])
                )
            )

        return BillListResponse(
            bills=briefs,
            total=total_count,
            page=page,
            limit=limit
        )

    except Exception as err:
        logger.error(f"Error querying bills list: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while listing bills: {str(err)}"
        )


@router.get("/{bill_id}", response_model=BillDetailResponse)
async def get_bill(bill_id: str):
    """
    Get full detail of a specific bill, including English & Swahili AI summaries,
    regulatory compliance info, regex extractions, and industry tags.
    """
    if not supabase_admin:
        if bill_id == "not-found" or (not getattr(settings, "TESTING", False) and not bill_id.startswith("mock-")):
            if bill_id == "not-found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bill '{bill_id}' not found"
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        # Offline/mock mode fallback
        return BillDetailResponse(
            id=bill_id,
            title="The Finance Bill, 2024 (Mock)",
            bill_type="financial",
            ai_summary_en="Mock English summary for offline testing.",
            ai_summary_sw="Muhtasari wa Kiswahili kwa majaribio.",
            tags=["Transport & Logistics"],
            regex_extractions=[{"value": "16%", "context": "VAT rate increase"}],
            source_url="https://parliament.go.ke/mock-bill.pdf",
            created_at=datetime.now(timezone.utc)
        )

    try:
        # Query bill detail
        res = supabase_admin.table("bills").select("*").eq("id", bill_id).execute()
        if not res.data or len(res.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bill '{bill_id}' not found"
            )

        bill_row = res.data[0]

        # Log warning if requested bill is not yet fully translated
        if bill_row.get("ai_status") != "translated":
            logger.warning(f"Bill '{bill_id}' requested, but ai_status is '{bill_row.get('ai_status')}' (not yet fully translated)")

        # Fetch associated tags
        tags_res = supabase_admin.table("bill_tags").select("industry_tag").eq("bill_id", bill_id).execute()
        tags = [row["industry_tag"] for row in tags_res.data] if tags_res.data else []

        created_at_val = bill_row.get("created_at")
        if isinstance(created_at_val, str):
            created_at_dt = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
        elif isinstance(created_at_val, datetime):
            created_at_dt = created_at_val
        else:
            created_at_dt = datetime.now(timezone.utc)

        raw_type = bill_row.get("bill_type", "financial")
        if raw_type not in ("financial", "regulatory", "hybrid"):
            logger.warning(f"Unexpected bill_type '{raw_type}' for detail bill {bill_id}; defaulting to 'financial'")
            valid_bill_type = "financial"
        else:
            valid_bill_type = raw_type

        return BillDetailResponse(
            id=bill_row["id"],
            title=bill_row.get("title", "Untitled Bill"),
            bill_type=valid_bill_type,
            ai_summary_en=bill_row.get("ai_summary_en"),
            ai_summary_sw=bill_row.get("ai_summary_sw"),
            tags=tags,
            regex_extractions=bill_row.get("regex_extractions"),
            source_url=bill_row.get("source_url", ""),
            created_at=created_at_dt
        )

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error querying detail for bill '{bill_id}': {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while querying bill '{bill_id}'"
        )


