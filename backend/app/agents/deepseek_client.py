import json
import logging
import time
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

import openai
from openai import (
    OpenAI,
    APIError,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

from app.config import settings
from app.agents.gemini_client import GeminiResponse, TRANSIENT_NETWORK_KEYWORDS

logger = logging.getLogger(__name__)


def get_deepseek_client(timeout: float = 60.0) -> OpenAI:
    """
    Initialize and return an OpenAI client instance configured for DeepSeek API.
    """
    api_key = getattr(settings, "DEEPSEEK_API_KEY", "") or ""
    base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com") or "https://api.deepseek.com"
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set in settings.")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


def _convert_tools_for_openai(tools: Optional[list[Any]]) -> Optional[list[Dict[str, Any]]]:
    """Convert Gemini tool declarations or raw dict specs to OpenAI function tool format."""
    if not tools:
        return None

    converted_tools = []
    for tool in tools:
        if isinstance(tool, dict) and "type" in tool:
            converted_tools.append(tool)
        elif hasattr(tool, "name") and hasattr(tool, "description"):
            # Convert google.genai FunctionDeclaration
            func_name = getattr(tool, "name", "calculate")
            func_desc = getattr(tool, "description", "")
            
            converted_tools.append({
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": func_desc,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to evaluate, e.g. '150000 * 0.025'."
                            }
                        },
                        "required": ["expression"]
                    }
                }
            })
        else:
            logger.warning(f"Unrecognized tool specification format: {type(tool)}. Skipping conversion.")
            
    return converted_tools if converted_tools else None


def call_deepseek(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = "deepseek-chat",
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
    response_schema: Optional[Any] = None,
    response_mime_type: Optional[str] = None,
    tools: Optional[list[Any]] = None,
    client: Optional[OpenAI] = None,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    agent_name: Optional[str] = None,
    bill_id: Optional[str] = None,
) -> GeminiResponse:
    """
    Call DeepSeek API using OpenAI SDK with timing, token usage tracking, structured output, and retry logic.

    Args:
        prompt: The text prompt or user message.
        system_instruction: Optional system instruction text.
        model: Target DeepSeek model name (default: deepseek-chat).
        temperature: Sampling temperature.
        max_output_tokens: Maximum completion tokens limit.
        response_schema: Target Pydantic model for structured JSON output.
        response_mime_type: Expected output MIME type hint.
        tools: Optional list of tools/functions.
        client: Optional explicit OpenAI client instance.
        max_retries: Maximum retry attempts for transient errors.
        backoff_factor: Exponential backoff sleeping factor.

    Returns:
        GeminiResponse object containing text, parsed output, token counts, and latency.
    """
    if client is None:
        client = get_deepseek_client()

    messages: list[Dict[str, Any]] = []

    # 1. System Prompt & Structured Output Injection
    sys_content = system_instruction or ""
    if response_schema is not None:
        try:
            if hasattr(response_schema, "model_json_schema"):
                schema_dict = response_schema.model_json_schema()
            elif hasattr(response_schema, "schema"):
                schema_dict = response_schema.schema()
            else:
                schema_dict = str(response_schema)
            
            schema_str = json.dumps(schema_dict, indent=2)
            json_instruction = (
                f"\n\nYou MUST respond with valid JSON conforming strictly to this JSON Schema:\n{schema_str}"
            )
            sys_content = f"{sys_content}{json_instruction}".strip()
        except Exception as err:
            logger.warning(f"Could not extract JSON schema from response_schema: {err}")

    if sys_content:
        messages.append({"role": "system", "content": sys_content})

    messages.append({"role": "user", "content": prompt})

    # 2. Build API Parameters
    api_kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_output_tokens is not None:
        api_kwargs["max_tokens"] = max_output_tokens

    if response_schema is not None or (response_mime_type and "json" in response_mime_type.lower()):
        api_kwargs["response_format"] = {"type": "json_object"}

    converted_tools = _convert_tools_for_openai(tools)
    if converted_tools:
        api_kwargs["tools"] = converted_tools

    last_exception = None
    start_time = time.perf_counter()

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(**api_kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if getattr(response, "usage", None):
                prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
                total_tokens = getattr(response.usage, "total_tokens", 0) or 0

            choice = response.choices[0] if response.choices else None
            text_output = choice.message.content if choice and choice.message else ""
            text_output = text_output or ""

            parsed_output = None
            if response_schema is not None and text_output.strip():
                try:
                    cleaned_text = text_output.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
                    elif cleaned_text.startswith("```"):
                        cleaned_text = cleaned_text.split("```", 1)[1].rsplit("```", 1)[0].strip()
                    
                    raw_json = json.loads(cleaned_text)
                    if hasattr(response_schema, "model_validate"):
                        parsed_output = response_schema.model_validate(raw_json)
                    elif isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
                        parsed_output = response_schema(**raw_json)
                    else:
                        parsed_output = raw_json
                except Exception as parse_err:
                    logger.warning(
                        f"Failed to parse DeepSeek JSON response into schema {getattr(response_schema, '__name__', response_schema)}: {parse_err}. "
                        f"Raw text: {text_output[:200]}..."
                    )

            # Log LLM usage and estimated cost
            try:
                from app.services.usage_logger import log_llm_usage
                log_llm_usage(
                    agent_name=agent_name or "deepseek",
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=elapsed_ms,
                    bill_id=bill_id,
                )
            except Exception as log_err:
                logger.debug(f"Usage logging skipped: {log_err}")

            return GeminiResponse(
                text=text_output,
                parsed=parsed_output,
                structured_output_requested=(response_schema is not None),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=elapsed_ms,
                model_name=model,
            )

        except (RateLimitError, APITimeoutError, InternalServerError, APIConnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                sleep_time = backoff_factor * (2 ** attempt)
                logger.warning(
                    f"DeepSeek API transient error ({type(e).__name__}): {e}. "
                    f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"DeepSeek API transient error exhausted retries: {e}")
                raise e
        except APIError as e:
            last_exception = e
            status_code = getattr(e, "status_code", None)
            is_transient = status_code in (429, 500, 502, 503, 504) or "rate" in str(e).lower()
            if is_transient and attempt < max_retries:
                sleep_time = backoff_factor * (2 ** attempt)
                logger.warning(
                    f"DeepSeek API status {status_code} error: {e}. "
                    f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"DeepSeek API error (code={status_code}): {e}")
                raise e
        except Exception as e:
            last_exception = e
            is_network = isinstance(e, (ConnectionError, TimeoutError, OSError)) or any(
                kw in str(e).lower() for kw in TRANSIENT_NETWORK_KEYWORDS
            )
            if attempt < max_retries and is_network:
                sleep_time = backoff_factor * (2 ** attempt)
                logger.warning(
                    f"DeepSeek API network error ({type(e).__name__}): {e}. "
                    f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"DeepSeek API unexpected error: {e}")
                raise e

    if last_exception:
        raise last_exception
    raise RuntimeError("Call to DeepSeek failed without returning a response.")
