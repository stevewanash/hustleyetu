"""
LLM Usage Logger & Cost Tracking Service for KeLegislate.
Logs token consumption, latency, and estimated USD cost for all Gemini and DeepSeek API calls.
"""

import logging
from typing import Optional, Dict, Any
from app.database import supabase_admin

logger = logging.getLogger(__name__)

# Pricing per token in USD (Standard tier rates)
# Formula: Cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Gemini 2.5/3.5/3.7/1.5 Flash: $0.15/1M input, $0.60/1M output
    "gemini-2.5-flash": {"input": 0.00000015, "output": 0.00000060},
    "gemini-3.5-flash": {"input": 0.00000015, "output": 0.00000060},
    "gemini-3.7-flash": {"input": 0.00000015, "output": 0.00000060},
    "gemini-1.5-flash": {"input": 0.00000015, "output": 0.00000060},
    "gemini-2.0-flash": {"input": 0.00000015, "output": 0.00000060},
    # Gemini Embeddings: $0.025/1M input
    "text-embedding-004": {"input": 0.000000025, "output": 0.0},
    # DeepSeek V3/Chat: $0.14/1M input, $0.28/1M output
    "deepseek-chat": {"input": 0.00000014, "output": 0.00000028},
    "deepseek-reasoner": {"input": 0.00000055, "output": 0.00000219},
}

# Default fallback pricing (conservative estimate based on Flash models)
DEFAULT_PRICING = {"input": 0.00000015, "output": 0.00000060}


def calculate_estimated_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int = 0
) -> float:
    """
    Computes estimated USD cost based on token counts and target model pricing.
    """
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    input_cost = prompt_tokens * pricing.get("input", 0.0)
    output_cost = completion_tokens * pricing.get("output", 0.0)
    total_cost = input_cost + output_cost
    return round(total_cost, 6)


def log_llm_usage(
    agent_name: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: float,
    bill_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Inserts a record into the Supabase llm_usage_log table.
    Catches errors gracefully to prevent breaking caller workflows.
    """
    cost_usd = calculate_estimated_cost(model, prompt_tokens, completion_tokens)
    
    log_entry = {
        "bill_id": bill_id,
        "agent_name": agent_name,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens or (prompt_tokens + completion_tokens),
        "latency_ms": round(latency_ms, 2),
        "estimated_cost_usd": cost_usd,
    }

    logger.debug(f"LLM Usage [{agent_name} - {model}]: {prompt_tokens} in / {completion_tokens} out, {latency_ms:.1f}ms, ${cost_usd:.6f}")

    if not supabase_admin:
        return log_entry

    try:
        res = supabase_admin.table("llm_usage_log").insert(log_entry).execute()
        return res.data[0] if res.data else log_entry
    except Exception as e:
        logger.warning(f"Failed to persist LLM usage log to Supabase: {e}")
        return log_entry
