import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import africastalking
from app.config import settings

logger = logging.getLogger(__name__)

_at_initialized = False

def _init_at():
    global _at_initialized
    if not _at_initialized:
        username = getattr(settings, "AFRICAS_TALKING_USERNAME", "sandbox")
        api_key = getattr(settings, "AFRICAS_TALKING_API_KEY", "")
        if username and api_key and api_key != "mock-at-key":
            try:
                africastalking.initialize(username, api_key)
                _at_initialized = True
            except Exception as e:
                logger.warning(f"Africa's Talking SDK initialization failed: {e}")

def send_sms(phone: str, message: str) -> dict:
    """
    Send an SMS message to a phone number using Africa's Talking API.
    Normalizes phone numbers to E.164 format via normalize_phone.
    Returns response dict from Africa's Talking or mock dict in test mode.
    """
    from app.utils.phone import normalize_phone
    normalized = normalize_phone(phone) or phone
    _init_at()
    username = getattr(settings, "AFRICAS_TALKING_USERNAME", "sandbox")
    api_key = getattr(settings, "AFRICAS_TALKING_API_KEY", "")
    testing = getattr(settings, "TESTING", False)

    if testing or not api_key or api_key == "mock-at-key":
        logger.info(f"[SMS MOCK/TEST] Sent to {normalized}: '{message}'")
        return {
            "status": "success",
            "recipients": [{"number": normalized, "status": "Success", "cost": "KES 0.8000", "messageId": f"AT-MOCK-{datetime.now().timestamp()}"}]
        }

    try:
        sms = africastalking.SMS
        sender_id = getattr(settings, "AFRICAS_TALKING_SENDER_ID", None)
        kwargs = {}
        if sender_id and sender_id.strip():
            kwargs["sender_id"] = sender_id.strip()

        response = sms.send(message, [normalized], **kwargs)
        logger.info(f"SMS successfully sent to {normalized} via Africa's Talking: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending SMS to {normalized} via Africa's Talking: {e}")
        raise e


async def send_bill_alerts(bill_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Sends SMS notifications to active subscribers for a specific bill.
    Formatted as a concise, non-panic alert directing subscribers to view full details online.
    Enforces MAX_SMS_FAN_OUT limit, checks bill readiness (ai_status), deduplicates re-sends, and logs notification records.
    """
    from app.database import supabase_admin

    max_fan_out = getattr(settings, "MAX_SMS_FAN_OUT", 500)
    bill_title = "Legislative Update"
    bill_tags_list = []

    if supabase_admin:
        try:
            bill_res = supabase_admin.table("bills").select("id, title, ai_status").eq("id", bill_id).execute()
            if not bill_res.data:
                raise ValueError(f"Bill '{bill_id}' not found.")
            
            bill_data = bill_res.data[0]
            bill_title = bill_data.get("title", bill_title)
            ai_status = bill_data.get("ai_status", "ingested")
            
            # Issue 2: Bill readiness check — must be processed (translated or verified)
            if ai_status not in ("translated", "verified"):
                raise ValueError(f"Bill '{bill_id}' has not been fully processed yet (status: '{ai_status}'). Alerts can only be dispatched for processed bills.")
            
            tag_res = supabase_admin.table("bill_tags").select("industry_tag").eq("bill_id", bill_id).execute()
            if tag_res.data:
                bill_tags_list = [row["industry_tag"] for row in tag_res.data if row.get("industry_tag")]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching bill {bill_id} or tags for notifications: {e}")
            if not getattr(settings, "TESTING", False):
                raise e

    # Query active subscribers matching bill's industry tags via strict set overlap (Issue 3)
    subscribers = []
    if supabase_admin:
        try:
            sub_res = supabase_admin.table("subscribers").select("*").eq("is_active", True).limit(max_fan_out).execute()
            all_active = sub_res.data or []
            from app.models.hustle_profiles import ACTIVE_INDUSTRY
            bill_tag_set = set(bill_tags_list) if bill_tags_list else {ACTIVE_INDUSTRY}
            for sub in all_active:
                sub_tags = set(sub.get("industry_tags") or [])
                if bill_tag_set & sub_tags:
                    subscribers.append(sub)
        except Exception as e:
            logger.error(f"Error querying active subscribers: {e}")

    # Fallback mock subscriber for offline test mode
    if not subscribers and getattr(settings, "TESTING", False):
        subscribers = [
            {
                "id": "mock-sub-uuid-1",
                "phone_encrypted": "+254700000000",
                "preferred_language": "en",
                "channels": ["sms"],
                "industry_tags": ["Transport & Logistics"]
            }
        ]

    # Issue 4: Query existing notifications for deduplication if not forced
    existing_notifications = {}
    if supabase_admin and not force:
        try:
            notif_res = supabase_admin.table("notifications").select("subscriber_id, status").eq("bill_id", bill_id).execute()
            for row in (notif_res.data or []):
                existing_notifications[row["subscriber_id"]] = row["status"]
        except Exception as e:
            logger.error(f"Error fetching existing notifications for deduplication: {e}")

    sent_count = 0
    failed_count = 0
    skipped_count = 0

    for sub in subscribers:
        sub_id = sub.get("id")
        phone = sub.get("phone_encrypted") or sub.get("phone")
        lang = sub.get("preferred_language", "en")

        if not phone or not sub_id:
            continue

        # Issue 4: Skip duplicate send if alert was already sent or delivered
        if not force and existing_notifications.get(sub_id) in ("sent", "delivered"):
            logger.info(f"Skipping duplicate alert for subscriber {sub_id}; alert already sent for bill {bill_id}")
            skipped_count += 1
            continue

        if lang.lower() in ("sw", "swahili"):
            msg = f"Taarifa ya Hustleyetu: Mswada mpya '{bill_title}' unaweza kuathiri biashara yako. Pata maelezo na ushiriki wa umma kwa https://hustleyetu.aibuildathon.dev/impact/{bill_id}"
        else:
            msg = f"Hustleyetu Alert: New bill '{bill_title}' may impact your business. View details and public participation info at https://hustleyetu.aibuildathon.dev/impact/{bill_id}"

        now_iso = datetime.now(timezone.utc).isoformat()
        at_msg_id = None
        status_str = "sent"
        failure_reason = None
        sent_at_val = None

        try:
            res = send_sms(phone, msg)
            if isinstance(res, dict) and "recipients" in res and res["recipients"]:
                rec = res["recipients"][0]
                at_msg_id = rec.get("messageId")
                if rec.get("status") not in ("Success", "sent", "success"):
                    status_str = "failed"
                    failure_reason = str(rec.get("status"))
                    failed_count += 1
                else:
                    status_str = "sent"
                    sent_at_val = now_iso  # Issue 6: set sent_at only on successful send
                    sent_count += 1
            else:
                status_str = "sent"
                sent_at_val = now_iso
                sent_count += 1
        except Exception as e:
            logger.error(f"Failed sending alert SMS to subscriber {sub_id} ({phone}): {e}")
            status_str = "failed"
            failure_reason = str(e)
            failed_count += 1

        # Record in notifications table
        if supabase_admin:
            try:
                notif_record = {
                    "bill_id": bill_id,
                    "subscriber_id": sub_id,
                    "channel": "sms",
                    "message_body": msg,
                    "at_message_id": at_msg_id,
                    "status": status_str,
                    "failure_reason": failure_reason,
                    "sent_at": sent_at_val,  # Issue 6: None if failed
                    "created_at": now_iso
                }
                supabase_admin.table("notifications").upsert(
                    notif_record,
                    on_conflict="bill_id, subscriber_id, channel"
                ).execute()
            except Exception as e:
                logger.error(f"Error logging notification record for subscriber {sub_id}: {e}")

    return {
        "bill_id": bill_id,
        "subscribers_found": len(subscribers),
        "alerts_sent": sent_count,
        "alerts_failed": failed_count,
        "alerts_skipped": skipped_count
    }


async def send_sms_alert(subscriber_id: str, message: str) -> dict:
    """
    Dispatch SMS alert for a single subscriber ID.
    """
    from app.database import supabase_admin
    if supabase_admin:
        try:
            res = supabase_admin.table("subscribers").select("phone_encrypted").eq("id", subscriber_id).execute()
            if res.data and res.data[0].get("phone_encrypted"):
                phone = res.data[0]["phone_encrypted"]
                return send_sms(phone, message)
        except Exception as e:
            logger.error(f"Error dispatching single subscriber alert: {e}")

    logger.info(f"Subscriber alert stub called for {subscriber_id}: '{message}'")
    return {"status": "queued"}
