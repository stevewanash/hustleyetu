import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Query, Depends, status

from app.agents.orchestrator import run_pipeline_async, PipelineState
from app.services.notifier import send_bill_alerts
from app.models.schemas import SendAlertsResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])


async def verify_admin_token(
    x_api_token: Optional[str] = Header(None, alias="X-API-Token")
):
    """
    FastAPI dependency enforcing admin authentication via X-API-Token header.
    Issue 9 & Issue 12: In production, strictly checks x_api_token against settings.API_SECRET_TOKEN.
    Bypasses for "mock-api-token" ONLY when settings.TESTING is True. Query param fallback removed.
    """
    expected_token = getattr(settings, "API_SECRET_TOKEN", "mock-api-token")
    testing = getattr(settings, "TESTING", False)

    if testing and x_api_token == "mock-api-token":
        return x_api_token

    if not x_api_token or x_api_token != expected_token:
        logger.warning("Admin endpoint access rejected: invalid or missing X-API-Token header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API token. Please provide X-API-Token header."
        )
    return x_api_token


@router.post("/admin/run-pipeline/{bill_id}", dependencies=[Depends(verify_admin_token)])
async def trigger_pipeline(
    bill_id: str,
    force: bool = Query(False, description="Force re-run all pipeline steps"),
    background: bool = Query(False, description="Run pipeline asynchronously in background"),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Admin endpoint to trigger the DAG orchestrator pipeline for a bill.
    Requires X-API-Token header matching API_SECRET_TOKEN.
    """
    if background and background_tasks:
        background_tasks.add_task(run_pipeline_async, bill_id, force)
        return {
            "status": "queued",
            "bill_id": bill_id,
            "message": f"Pipeline execution queued in background for bill '{bill_id}'"
        }

    state: PipelineState = await run_pipeline_async(bill_id, force=force)
    
    if state.status == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed for bill '{bill_id}': {state.error_message}"
        )

    return {
        "status": state.status,
        "bill_id": state.bill_id,
        "step_results": state.step_results,
        "updated_at": state.updated_at
    }


@router.post("/admin/send-alerts/{bill_id}", response_model=SendAlertsResponse, dependencies=[Depends(verify_admin_token)])
async def trigger_bill_alerts(
    bill_id: str,
    force: bool = Query(False, description="Force re-send alerts even if previously dispatched")
):
    """
    Admin endpoint to trigger alert fan-out for a specific bill to active subscribers.
    Requires X-API-Token header matching API_SECRET_TOKEN.
    Checks bill existence, ai_status readiness, pure tag overlap matching, and deduplicates re-sends unless force=True.
    """
    try:
        result = await send_bill_alerts(bill_id, force=force)
        return SendAlertsResponse(
            bill_id=result["bill_id"],
            subscribers_found=result["subscribers_found"],
            alerts_sent=result["alerts_sent"],
            alerts_failed=result["alerts_failed"],
            alerts_skipped=result.get("alerts_skipped", 0)
        )
    except ValueError as ve:
        logger.warning(f"Alert dispatch rejected for bill '{bill_id}': {ve}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error executing manual alert trigger for bill {bill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch alerts for bill '{bill_id}': {str(e)}"
        )
