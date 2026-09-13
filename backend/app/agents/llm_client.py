import logging
from typing import Any, Optional

from app.config import settings
from app.agents.gemini_client import GeminiResponse, call_gemini
from app.agents.deepseek_client import call_deepseek

logger = logging.getLogger(__name__)

# Model mapping from Gemini models to DeepSeek models
MODEL_MAPPING = {
    "gemini-2.5-flash": "deepseek-chat",
    "gemini-3.5-flash": "deepseek-reasoner",
}


def call_llm(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
    response_schema: Optional[Any] = None,
    response_mime_type: Optional[str] = None,
    tools: Optional[list[Any]] = None,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    agent_name: Optional[str] = None,
    bill_id: Optional[str] = None,
    **kwargs: Any,
) -> GeminiResponse:
    """
    Provider abstraction router that dispatches calls to Gemini or DeepSeek based on settings.AI_PROVIDER.

    Args:
        prompt: User message or bill text.
        system_instruction: System instruction or context.
        model: Target model identifier or None for default.
        temperature: Sampling temperature.
        max_output_tokens: Token limit.
        response_schema: Pydantic model class for structured JSON.
        response_mime_type: Expected MIME type.
        tools: Optional function tool definitions.
        max_retries: Maximum transient error retries.
        backoff_factor: Exponential backoff factor.
        agent_name: Logical agent name for usage logging (e.g. 'summarizer', 'verifier').
        bill_id: Optional UUID of the associated bill.

    Returns:
        GeminiResponse container object.
    """
    provider = getattr(settings, "AI_PROVIDER", "gemini").lower()

    if provider == "deepseek":
        if model is None:
            target_model = "deepseek-chat"
        elif model in MODEL_MAPPING:
            target_model = MODEL_MAPPING[model]
        elif model.startswith("gemini"):
            target_model = "deepseek-chat"
        else:
            target_model = model

        logger.debug(f"Routing LLM call to DeepSeek (model='{target_model}')")
        return call_deepseek(
            prompt=prompt,
            system_instruction=system_instruction,
            model=target_model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_schema=response_schema,
            response_mime_type=response_mime_type,
            tools=tools,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            agent_name=agent_name,
            bill_id=bill_id,
        )
    else:
        target_model = model or "gemini-2.5-flash"
        logger.debug(f"Routing LLM call to Gemini (model='{target_model}')")
        try:
            return call_gemini(
                prompt=prompt,
                system_instruction=system_instruction,
                model=target_model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_schema=response_schema,
                response_mime_type=response_mime_type,
                tools=tools,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                agent_name=agent_name,
                bill_id=bill_id,
            )
        except Exception as e:
            deepseek_key = getattr(settings, "DEEPSEEK_API_KEY", "")
            if deepseek_key:
                logger.warning(
                    f"Primary Gemini call failed ({e}); falling back to secondary provider DeepSeek."
                )
                ds_model = MODEL_MAPPING.get(target_model, "deepseek-chat")
                return call_deepseek(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    model=ds_model,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    response_schema=response_schema,
                    response_mime_type=response_mime_type,
                    tools=tools,
                    max_retries=max_retries,
                    backoff_factor=backoff_factor,
                    agent_name=agent_name,
                    bill_id=bill_id,
                )
            raise e
