from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import bills, impact, feedback, subscribe, dashboard, webhooks, admin


app = FastAPI(
    title="Hustleyetu API",
    description="Proactive civic technology platform that alerts Kenyan bodaboda riders and transport micro-enterprises about how proposed legislation impacts their livelihood — delivering financial impact analysis and regulatory compliance advice in shillings and cents.",
    version="1.0.0"
)

# CORS setup
origins = [
    "https://hustleyetu.aibuildathon.dev",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(bills.router, prefix="/api")
app.include_router(impact.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(subscribe.router, prefix="/api")

app.include_router(dashboard.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# Direct route alias for Supabase Auth SMS webhook
app.add_api_route("/api/auth/send-sms", webhooks.supabase_auth_send_sms, methods=["POST"], tags=["Webhooks"])


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify backend service state.
    """
    return {"status": "ok"}
