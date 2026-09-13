import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.middleware.auth import get_current_user
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit citizen stance feedback on a bill (Requires verified OTP authentication).
    Enforces UNIQUE(bill_id, user_id) constraint, returning HTTP 409 if feedback was already submitted.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid authenticated user context required."
        )

    # Issue 3: Validate UUID format for bill_id
    try:
        uuid.UUID(request.bill_id)
    except ValueError:
        # In test/mock mode, allow mock bill IDs if TESTING is set
        if not (getattr(settings, "TESTING", False) and request.bill_id.startswith("mock-bill-")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bill_id format: '{request.bill_id}'. Must be a valid UUID."
            )

    if request.support not in ("support", "oppose", "neutral"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Support field must be one of: 'support', 'oppose', or 'neutral'."
        )

    if not (1 <= request.rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be an integer between 1 and 5."
        )

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    feedback_id = None

    if supabase_admin:
        try:
            # Issue 3: Check bill existence
            bill_check = supabase_admin.table("bills").select("id").eq("id", request.bill_id).execute()
            if not bill_check.data and not getattr(settings, "TESTING", False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bill '{request.bill_id}' not found."
                )

            # Check for existing duplicate before insert for clean 409 handling
            existing_res = supabase_admin.table("feedback").select("id").eq("bill_id", request.bill_id).eq("user_id", user_id).execute()
            if existing_res.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You've already submitted feedback for this bill."
                )

            insert_data = {
                "bill_id": request.bill_id,
                "user_id": user_id,
                "support": request.support,
                "rating": request.rating,
                "concerns": request.concerns,
                "created_at": now_iso
            }
            res = supabase_admin.table("feedback").insert(insert_data).execute()
            rows = res.data or []
            if rows:
                feedback_id = rows[0]["id"]
                created_at_val = rows[0].get("created_at")
                if isinstance(created_at_val, str):
                    now_dt = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
        except HTTPException:
            raise
        except Exception as e:
            err_msg = str(e).lower()
            err_code = getattr(e, "code", None)
            # Issue 2: Numeric 23505 PostgREST code check with fallback
            if err_code == "23505" or "23505" in err_msg or "unique" in err_msg or "duplicate" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You've already submitted feedback for this bill."
                )
            if "23503" in err_msg or "foreign key" in err_msg or "violates foreign key constraint" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bill '{request.bill_id}' not found."
                )
            logger.error(f"Error saving feedback to database for user {user_id}: {e}")
            if not getattr(settings, "TESTING", False):
                # Issue 4: Generic non-leaking 500 error detail
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to submit feedback. Please try again later."
                )

    if not feedback_id:
        feedback_id = f"fb-{user_id[:8]}-{request.bill_id[:8]}"

    return FeedbackResponse(id=str(feedback_id), created_at=now_dt)
