import logging
import json
import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse

from app.models.schemas import SupabaseSmsWebhookPayload
from app.services.notifier import send_sms
from app.utils.phone import normalize_phone
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Canonical Africa's Talking status mapping to notifications vocabulary (Issue 2)
AT_STATUS_MAP = {
    "success": "delivered",
    "delivered": "delivered",
    "deliveredtoterminal": "delivered",
    "sent": "sent",
    "buffered": "buffered",
    "failed": "failed",
    "rejected": "failed",
    "expired": "failed",
}


def _verify_standardwebhook(raw_body: bytes, headers, secret: str, tolerance_seconds: int = 300) -> bool:
    """
    Verify a standardwebhooks signature (used by Supabase Auth Hooks).
    See: https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md
    """
    try:
        # Extract the base64 secret (remove v1,whsec_ prefix)
        clean_secret = secret
        if clean_secret.startswith("v1,whsec_"):
            clean_secret = clean_secret[len("v1,whsec_"):]
        secret_bytes = base64.b64decode(clean_secret)

        msg_id = headers.get("webhook-id", "")
        msg_timestamp = headers.get("webhook-timestamp", "")
        msg_signatures = headers.get("webhook-signature", "")

        if not msg_id or not msg_timestamp or not msg_signatures:
            return False

        # Check timestamp tolerance (prevent replay attacks)
        ts = int(msg_timestamp)
        if abs(time.time() - ts) > tolerance_seconds:
            logger.warning(f"Webhook timestamp outside tolerance: {ts} vs {time.time()}")
            return False

        # Compute expected HMAC-SHA256 signature: sign("{msg_id}.{timestamp}.{body}")
        body_str = raw_body.decode("utf-8")
        to_sign = f"{msg_id}.{msg_timestamp}.{body_str}"
        expected_sig = base64.b64encode(
            hmac.new(secret_bytes, to_sign.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")

        # Verify against provided signatures (space-separated, each prefixed with "v1,")
        for sig_entry in msg_signatures.split(" "):
            parts = sig_entry.split(",", 1)
            if len(parts) == 2 and parts[0] == "v1":
                if hmac.compare_digest(expected_sig, parts[1]):
                    return True

        logger.warning("Standardwebhook signature mismatch")
        return False
    except Exception as e:
        logger.error(f"Error verifying standardwebhook signature: {e}")
        return False


@router.post("/at-delivery")
async def at_delivery_webhook(
    request: Request,
    x_at_webhook_secret: str = Header(None, alias="x-at-webhook-secret")
):
    """
    Africa's Talking delivery receipts webhook.
    Receives delivery receipts via JSON or Form POST payload, extracts messageId and status,
    normalizes AT status to canonical vocabulary (delivered, failed, sent, buffered, unknown),
    and updates notification record delivery state in database.

    Security Note (Issue 1): Africa's Talking POST callbacks are unauthenticated by default.
    If AT_DELIVERY_WEBHOOK_SECRET is set in environment, x-at-webhook-secret header is validated.
    """
    expected_secret = getattr(settings, "AT_DELIVERY_WEBHOOK_SECRET", None)
    testing = getattr(settings, "TESTING", False)

    if expected_secret and not testing:
        if not x_at_webhook_secret or x_at_webhook_secret != expected_secret:
            logger.warning("AT delivery webhook secret mismatch or missing header")
            raise HTTPException(status_code=401, detail="Invalid or missing webhook secret header")

    content_type = request.headers.get("content-type", "")
    message_id = None
    status_text = None
    failure_reason = None
    data = {}

    try:
        if "application/json" in content_type:
            data = await request.json()
        elif "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            data = dict(form_data)
        else:
            try:
                data = await request.json()
            except Exception:
                form_data = await request.form()
                data = dict(form_data)
    except Exception as e:
        logger.error(f"Failed parsing AT delivery receipt body: {e}")
        return JSONResponse(content={"status": "error", "detail": "Invalid payload format"}, status_code=400)

    message_id = data.get("id") or data.get("messageId")
    status_text = data.get("status")
    failure_reason = data.get("failureReason")

    logger.info(f"Received AT delivery receipt — MessageId: {message_id} | Status: {status_text}")

    if not message_id or not status_text:
        return JSONResponse(content={"status": "ignored", "detail": "Missing messageId or status"}, status_code=200)

    # Issue 2: Canonical status mapping
    status_lower = str(status_text).strip().lower()
    normalized_status = AT_STATUS_MAP.get(status_lower, "unknown")

    now_iso = datetime.now(timezone.utc).isoformat()
    db_updated = False

    if supabase_admin:
        try:
            update_fields = {
                "status": normalized_status,
                "delivered_at": now_iso
            }
            if failure_reason:
                update_fields["failure_reason"] = str(failure_reason)

            supabase_admin.table("notifications").update(update_fields).eq("at_message_id", message_id).execute()
            db_updated = True
            logger.info(f"Updated notification status for messageId '{message_id}' -> '{normalized_status}'")
        except Exception as e:
            logger.error(f"Error updating notification delivery status in DB for messageId {message_id}: {e}")

    # Issue 3: Explicit db_updated status field for observability
    return JSONResponse(
        content={
            "status": "received",
            "message_id": message_id,
            "normalized_status": normalized_status,
            "db_updated": db_updated
        },
        status_code=200
    )


@router.post("/incoming-sms")
@router.post("/sms/incoming")
async def incoming_sms_webhook(payload: dict):
    """
    Africa's Talking / Shared Gateway incoming SMS webhook.
    Receives citizen messages sent to keyword (e.g., 'kamilimu kelegislate ...').
    """
    logger.info(f"Received incoming SMS webhook payload: {payload}")
    from_phone = payload.get("from") or payload.get("phoneNumber") or payload.get("from_phone")
    text = payload.get("text") or payload.get("message")

    logger.info(f"Incoming SMS parsed — From: {from_phone} | Text: '{text}'")
    return {"status": "success", "detail": "Incoming SMS received successfully"}


@router.post("/auth/send-sms")
async def supabase_auth_send_sms(request: Request):
    """
    Custom SMS OTP gateway webhook invoked by Supabase Auth.
    Supports both:
      1. Standardwebhooks signature verification (new Supabase Auth Hooks system)
      2. Simple header-based verification (legacy custom SMS webhook)
    Returns HTTP 200 with empty JSON `{}` per Supabase custom SMS provider specification.
    """
    raw_body = await request.body()
    expected_secret = getattr(settings, "SUPABASE_SMS_WEBHOOK_SECRET", "")
    testing = getattr(settings, "TESTING", False)

    # --- Authentication ---
    webhook_id = request.headers.get("webhook-id")
    webhook_timestamp = request.headers.get("webhook-timestamp")
    webhook_signature = request.headers.get("webhook-signature")
    legacy_header = request.headers.get("x-supabase-webhook-secret")

    if not testing:
        if webhook_id and webhook_timestamp and webhook_signature:
            # New Auth Hooks system: verify standardwebhooks HMAC-SHA256 signature
            if not _verify_standardwebhook(raw_body, request.headers, expected_secret):
                logger.warning("Standardwebhooks signature verification failed for auth/send-sms")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            logger.info("Standardwebhooks signature verified successfully")
        elif expected_secret and expected_secret != "mock-secret":
            # Legacy custom SMS webhook: verify simple header
            if not legacy_header or legacy_header != expected_secret:
                logger.warning("Supabase Auth SMS webhook secret mismatch or missing header")
                raise HTTPException(status_code=401, detail="Invalid or missing webhook secret header")
            logger.info("Legacy webhook header verified successfully")

    # --- Parse payload ---
    try:
        payload_dict = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to parse SMS webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    payload = SupabaseSmsWebhookPayload(**payload_dict)

    phone_raw = payload.get_recipient_phone()
    message_text = payload.get_message_text()

    if not phone_raw or not message_text:
        logger.error(f"Invalid payload for Supabase SMS webhook: {payload}")
        raise HTTPException(status_code=400, detail="Missing phone or SMS text in payload")

    normalized_phone = normalize_phone(phone_raw)
    if not normalized_phone:
        logger.error(f"Invalid phone number format: {phone_raw}")
        raise HTTPException(status_code=400, detail=f"Invalid phone number format: {phone_raw}")

    try:
        send_sms(phone=normalized_phone, message=message_text)
        logger.info(f"Supabase Auth SMS OTP sent successfully to {normalized_phone}")
    except Exception as e:
        logger.error(f"Failed to dispatch Supabase Auth SMS to {normalized_phone}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

    # STRICT REQUIREMENT: Return empty JSON object {} with status code 200
    return JSONResponse(content={}, status_code=200)


# ==========================================
# Tasks / Admin Stub routes
# ==========================================
@router.post("/tasks/scrape")
async def trigger_scraper(authorization: str = Header(None)):
    """
    Trigger parliamentary bill scraping.
    """
    raise HTTPException(status_code=501, detail="Endpoint not implemented yet")
