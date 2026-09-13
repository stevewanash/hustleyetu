import logging
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.models.schemas import DashboardStatsResponse
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(bill_id: Optional[str] = Query(None)):
    """
    Get aggregated dashboard stats (total feedback, stance distribution, average rating, top concerns)
    for a specific bill or globally across all bills.
    """
    if not supabase_admin:
        # Mock / Offline mode fallback for development and testing
        if bill_id == "mock-bill-002" or bill_id == "nairobi-bodaboda-regulations-2025":
            return DashboardStatsResponse(
                total_feedback=86,
                support_pct={"support": 30.0, "oppose": 55.0, "neutral": 15.0},
                avg_rating=2.5,
                top_concerns=[
                    "Withholding tax percentage",
                    "Registration threshold limits",
                    "Mobile money tracking",
                    "Exemptions clarity"
                ]
            )
        elif bill_id:
            return DashboardStatsResponse(
                total_feedback=124,
                support_pct={"support": 12.0, "oppose": 78.0, "neutral": 10.0},
                avg_rating=1.8,
                top_concerns=[
                    "Annual fee burden",
                    "Direct hit on BodaBoda daily margins",
                    "Strict penalty guidelines",
                    "Verification complexity"
                ]
            )
        else:
            return DashboardStatsResponse(
                total_feedback=210,
                support_pct={"support": 19.4, "oppose": 68.6, "neutral": 12.0},
                avg_rating=2.1,
                top_concerns=[
                    "Annual fee burden",
                    "Direct hit on BodaBoda daily margins",
                    "Strict penalty guidelines",
                    "Withholding tax percentage"
                ]
            )

    try:
        query = supabase_admin.table("feedback").select("support, rating, concerns")
        if bill_id:
            query = query.eq("bill_id", bill_id)

        res = query.execute()
        data = res.data or []

        if not data:
            return DashboardStatsResponse(
                total_feedback=0,
                support_pct={"support": 0.0, "oppose": 0.0, "neutral": 0.0},
                avg_rating=0.0,
                top_concerns=[]
            )

        total_feedback = len(data)
        support_count = sum(1 for r in data if r.get("support") == "support")
        oppose_count = sum(1 for r in data if r.get("support") == "oppose")
        neutral_count = sum(1 for r in data if r.get("support") == "neutral")

        support_pct = {
            "support": round((support_count / total_feedback) * 100, 1),
            "oppose": round((oppose_count / total_feedback) * 100, 1),
            "neutral": round((neutral_count / total_feedback) * 100, 1),
        }

        ratings = [r["rating"] for r in data if isinstance(r.get("rating"), (int, float))]
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0

        from collections import Counter

        concerns_list = [
            r["concerns"].strip()
            for r in data
            if r.get("concerns") and isinstance(r["concerns"], str) and r["concerns"].strip()
        ]

        top_concerns = [concern for concern, _ in Counter(concerns_list).most_common(5)]

        return DashboardStatsResponse(
            total_feedback=total_feedback,
            support_pct=support_pct,
            avg_rating=avg_rating,
            top_concerns=top_concerns
        )

    except Exception as err:
        logger.error(f"Error computing dashboard stats: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )
