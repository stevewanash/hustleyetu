from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

# ==========================================
# BILL SCHEMAS
# ==========================================
class BillBrief(BaseModel):
    id: str
    title: str
    tags: List[str]
    bill_type: Literal["financial", "regulatory", "hybrid"] = "financial"
    created_at: datetime
    ai_status: str
    ai_summary_en: Optional[str] = None
    impact_summary: Optional[str] = None

class BillListResponse(BaseModel):
    bills: List[BillBrief]
    total: int
    page: int
    limit: int

class BillDetailResponse(BaseModel):
    id: str
    title: str
    bill_type: Literal["financial", "regulatory", "hybrid"] = "financial"
    ai_summary_en: Optional[str] = None
    ai_summary_sw: Optional[str] = None
    tags: List[str]
    regex_extractions: Optional[List[Dict[str, Any]]] = None
    source_url: str
    created_at: datetime

# ==========================================
# COMPLIANCE SCHEMAS
# ==========================================
class ComplianceItem(BaseModel):
    """A single regulatory compliance requirement extracted from a bill."""
    requirement: str
    status: str  # 'required', 'recommended', 'optional'
    deadline: Optional[str] = None
    estimated_cost_kes: Optional[float] = None
    penalty_for_non_compliance: Optional[str] = None

class PenaltyRisk(BaseModel):
    """A penalty risk associated with non-compliance of a regulatory bill."""
    violation: str
    penalty: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

# ==========================================
# PRE-GENERATED REDESIGN IMPACT SCHEMAS (v1.3)
# ==========================================
class ScenarioPersona(BaseModel):
    """Hypothetical persona profile for worked example scenarios."""
    name: str
    description: str
    metrics: Dict[str, Any] = {}

class ComplianceActionItem(BaseModel):
    """Action item for regulatory compliance guides."""
    action: str
    deadline: str
    source: str

class ImpactRequest(BaseModel):
    bill_id: str
    industry: Optional[str] = "ALL"
    tier: Optional[str] = "ALL"

class ImpactItem(BaseModel):
    """Structured model for a single financial impact line item."""
    description: str
    base_kes: float
    change_kes: float
    period: str = "monthly"  # "monthly", "annual", "one-time"
    section_ref: str
    math_breakdown: str

class ImpactResponse(BaseModel):
    """
    Unified response for pre-generated example scenarios and compliance checklists.
    Supports both legacy tier calculations and v1.3 pre-generated payloads.
    """
    bill_id: Optional[str] = None
    bill_title: Optional[str] = None
    bill_type: Literal["financial", "regulatory", "hybrid"] = "financial"
    concise_summary: Optional[str] = None
    
    # Financial Pre-generated Example Scenario
    scenario_persona: Optional[ScenarioPersona] = None
    key_figures: Optional[List[str]] = None
    math_breakdown: Optional[List[str]] = None
    calculator_formula: Optional[str] = None
    
    # Regulatory Compliance Checklist
    regulatory_changes: Optional[List[str]] = None
    compliance_checklist: Optional[List[ComplianceActionItem]] = None
    
    # Common Fields
    sources: Optional[List[str]] = None
    risk_level: str = "MEDIUM"  # 'LOW', 'MEDIUM', 'HIGH'
    pdf_url: Optional[str] = None
    verified: bool = True
    disclaimer: Optional[str] = "This impact analysis is an automated estimate for informational purposes and does not constitute legal or tax advice."

    # Legacy compatibility fields
    impact_table: Optional[List[ImpactItem]] = None
    net_monthly_impact: Optional[float] = None
    compliance_cost_total: Optional[float] = None
    penalty_risks: Optional[List[PenaltyRisk]] = None


# ==========================================
# FEEDBACK SCHEMAS
# ==========================================
class FeedbackRequest(BaseModel):
    bill_id: str
    support: str  # 'support', 'oppose', 'neutral'
    rating: int  # 1 to 5
    concerns: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: str
    created_at: datetime

# ==========================================
# SUBSCRIPTION SCHEMAS
# ==========================================
class SubscribeRequest(BaseModel):
    phone: str  # E.164 format
    industries: Optional[List[str]] = Field(default=None, description="Target industry sectors. Defaults to ACTIVE_INDUSTRY if omitted/empty.")
    language: Literal["en", "sw"] = "en"
    channels: List[Literal["sms", "whatsapp"]] = ["sms"]

class UnsubscribeRequest(BaseModel):
    phone: str

class SubscribeResponse(BaseModel):
    subscriber_id: str
    status: str

class SubscriptionStatusResponse(BaseModel):
    is_active: bool
    industries: List[str]
    preferred_language: str
    channels: List[str]

class SendAlertsResponse(BaseModel):
    bill_id: str
    subscribers_found: int
    alerts_sent: int
    alerts_failed: int
    alerts_skipped: int = 0


# ==========================================
# DASHBOARD SCHEMAS
# ==========================================
class DashboardStatsResponse(BaseModel):
    total_feedback: int
    support_pct: Dict[str, float]  # e.g., {"support": 60.0, "oppose": 30.0, "neutral": 10.0}
    avg_rating: float
    top_concerns: List[str]

# ==========================================
# WEBHOOK SCHEMAS
# ==========================================
class DeliveryReceiptRequest(BaseModel):
    messageId: str
    status: str
    phoneNumber: Optional[str] = None
    retryCount: Optional[int] = None
    networkCode: Optional[str] = None

class SupabaseSmsWebhookPayload(BaseModel):
    type: Optional[str] = "sms"
    phone: Optional[str] = None
    text: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    sms: Optional[Dict[str, Any]] = None

    def get_recipient_phone(self) -> Optional[str]:
        if self.phone:
            return self.phone
        if self.user and isinstance(self.user, dict) and "phone" in self.user:
            return self.user["phone"]
        return None

    def get_message_text(self) -> Optional[str]:
        if self.text:
            return self.text
        if self.sms and isinstance(self.sms, dict):
            if "otp" in self.sms:
                return f"Your Hustle Yetu verification code is: {self.sms['otp']}"
            if "text" in self.sms:
                return self.sms["text"]
        return None

class IncomingSMSPayload(BaseModel):
    from_phone: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    text: str
    date: Optional[str] = None
    id: Optional[str] = None
    linkId: Optional[str] = None


