import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from app.models.schemas import (
    SubscribeRequest,
    UnsubscribeRequest,
    SubscribeResponse,
    SubscriptionStatusResponse
)
from app.models.hustle_profiles import ACTIVE_INDUSTRY, INDUSTRIES
from app.utils.phone import normalize_phone
from app.services.notifier import send_sms
from app.database import supabase_admin
from app.middleware.auth import get_optional_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscribe", tags=["Subscription"])


@router.post("", response_model=SubscribeResponse)
async def subscribe_alerts(
    request: SubscribeRequest,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Subscribe phone number for SMS legislation alerts.
    Computes phone_hash (SHA-256), upserts subscriber record atomically, and sends confirmation SMS.
    """
    normalized_phone = normalize_phone(request.phone)
    if not normalized_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number format: '{request.phone}'. Please provide a valid Kenyan phone number."
        )

    # Server-side industry tag coercion & validation (Issue 3)
    if not request.industries:
        target_industries = [ACTIVE_INDUSTRY]
    else:
        valid_inds = [ind for ind in request.industries if ind in INDUSTRIES]
        if not valid_inds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"None of the provided industry tags are valid. Allowed tags: {', '.join(INDUSTRIES)}"
            )
        target_industries = valid_inds

    phone_hash = hashlib.sha256(normalized_phone.encode("utf-8")).hexdigest()
    user_id = user.get("id") if user else None
    now_iso = datetime.now(timezone.utc).isoformat()

    subscriber_id = None

    if supabase_admin:
        try:
            # Atomic upsert on phone_hash to eliminate check-then-insert race condition (Issue #1)
            upsert_data = {
                "phone_hash": phone_hash,
                "phone_encrypted": normalized_phone,  # Baseline plaintext storage; Vault encryption in Phase 6
                "industry_tags": target_industries,
                "preferred_language": request.language,
                "channels": list(request.channels),
                "is_active": True,
                "consent_given_at": now_iso,
                "updated_at": now_iso
            }
            if user_id:
                upsert_data["user_id"] = user_id

            upsert_res = supabase_admin.table("subscribers").upsert(
                upsert_data,
                on_conflict="phone_hash"
            ).execute()
            upserted_rows = upsert_res.data or []

            if upserted_rows:
                subscriber_id = upserted_rows[0]["id"]
                logger.info(f"Upserted subscription {subscriber_id} for phone_hash {phone_hash[:8]}...")
            else:
                # Upsert returned no rows — retrieve by phone_hash as fallback
                fetch_res = supabase_admin.table("subscribers").select("id").eq("phone_hash", phone_hash).execute()
                fetch_rows = fetch_res.data or []
                if fetch_rows:
                    subscriber_id = fetch_rows[0]["id"]
                    logger.info(f"Retrieved existing subscriber {subscriber_id} after upsert")
        except Exception as e:
            logger.error(f"Error persisting subscription to database: {e}")
            if not getattr(settings, "TESTING", False):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process subscription: {str(e)}"
                )

    # Issue #2: Only use mock IDs in TESTING mode; raise 503 otherwise when persistence produces no ID
    if not subscriber_id:
        if getattr(settings, "TESTING", False):
            subscriber_id = f"mock-sub-{phone_hash[:12]}"
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Subscription service temporarily unavailable. Please try again."
            )

    # Send confirmation SMS via Africa's Talking
    if request.language == "sw":
        confirm_msg = "Umesajiliwa kupokea arifa za SMS kutoka Hustleyetu. Utapokea taarifa kuhusu sheria zinazoathiri biashara yako."
    else:
        confirm_msg = "You are subscribed to Hustleyetu SMS alerts. You will receive updates on laws impacting your business."

    try:
        send_sms(normalized_phone, confirm_msg)
    except Exception as e:
        logger.warning(f"Confirmation SMS dispatch encountered an error: {e}")

    return SubscribeResponse(subscriber_id=str(subscriber_id), status="subscribed")


@router.delete("")
async def unsubscribe_alerts(
    phone: Optional[str] = Query(None),
    body: Optional[UnsubscribeRequest] = None
):
    """
    Unsubscribe phone number from all alerts (sets is_active = FALSE).
    Accepts phone as a query parameter or JSON body.

    Note (Issue #4): This endpoint is intentionally unauthenticated for baseline
    to match UC-08 SMS "STOP" keyword flow. Post-baseline, require an unsubscribe
    token delivered via SMS or OTP auth.
    """
    target_phone = (body.phone if body else None) or phone
    if not target_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required to unsubscribe."
        )

    normalized_phone = normalize_phone(target_phone)
    if not normalized_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number format: '{target_phone}'."
        )

    phone_hash = hashlib.sha256(normalized_phone.encode("utf-8")).hexdigest()
    now_iso = datetime.now(timezone.utc).isoformat()

    if supabase_admin:
        try:
            supabase_admin.table("subscribers").update({
                "is_active": False,
                "updated_at": now_iso
            }).eq("phone_hash", phone_hash).execute()
            logger.info(f"Deactivated subscription for phone_hash {phone_hash[:8]}...")
        except Exception as e:
            logger.error(f"Error deactivating subscription: {e}")
            if not getattr(settings, "TESTING", False):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to unsubscribe: {str(e)}"
                )

    return {"status": "unsubscribed", "detail": "Subscription deactivated successfully"}


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(phone: str = Query(...)):
    """
    Check subscription status by phone number.

    Note (Issue #4): This endpoint is intentionally unauthenticated for baseline.
    Post-baseline, require OTP auth to prevent preference data exposure.
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number format: '{phone}'."
        )

    phone_hash = hashlib.sha256(normalized_phone.encode("utf-8")).hexdigest()

    if supabase_admin:
        try:
            res = supabase_admin.table("subscribers").select("*").eq("phone_hash", phone_hash).execute()
            rows = res.data or []
            if rows:
                sub = rows[0]
                return SubscriptionStatusResponse(
                    is_active=sub.get("is_active", False),
                    industries=sub.get("industry_tags", []),
                    preferred_language=sub.get("preferred_language", "en"),
                    channels=sub.get("channels", ["sms"])
                )
            # Successful query, no matching row — genuinely not subscribed
            return SubscriptionStatusResponse(
                is_active=False,
                industries=[],
                preferred_language="en",
                channels=[]
            )
        except Exception as e:
            # Issue #3: Surface DB errors as 503 instead of silently returning "not subscribed"
            logger.error(f"Error fetching subscription status: {e}")
            if not getattr(settings, "TESTING", False):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Subscription status lookup temporarily unavailable. Please try again."
                )

    # No supabase_admin available — TESTING mode fallback only
    return SubscriptionStatusResponse(
        is_active=False,
        industries=[],
        preferred_language="en",
        channels=[]
    )
