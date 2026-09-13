import logging
import os
import time
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

TRANSIENT_NETWORK_KEYWORDS = ("connection", "timeout", "timed out", "reset", "dns", "unreachable")

class GeminiResponse(BaseModel):
    """Container for Gemini API response data and performance metrics."""
    text: str = ""
    parsed: Optional[Any] = None
    structured_output_requested: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    model_name: str = ""

def get_gemini_client(timeout: int = 60000) -> genai.Client:
    """
    Initialize and return a google-genai Client instance using configured API key or Vertex AI ADC,
    platform routing, and explicit request timeout (default: 60000ms / 60s).
    """
    platform = getattr(settings, "GEMINI_PLATFORM", "vertex_ai")
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    google_creds = getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", None)
    vertex_project = getattr(settings, "VERTEX_PROJECT", None)
    vertex_location = getattr(settings, "VERTEX_LOCATION", "us-central1")

    if google_creds:
        if not os.path.isabs(google_creds) and not os.path.exists(google_creds):
            # check in workspace root directory
            parent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), google_creds)
            if os.path.exists(parent_path):
                google_creds = parent_path
        if os.path.exists(google_creds):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(google_creds)

    kwargs: dict[str, Any] = {
        "http_options": {"timeout": timeout},
    }

    if platform == "vertex_ai":
        kwargs["vertexai"] = True
        if vertex_project:
            kwargs["project"] = vertex_project
        if vertex_location:
            kwargs["location"] = vertex_location
        if api_key:
            kwargs["api_key"] = api_key
    else:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in settings for AI Studio platform.")
        kwargs["api_key"] = api_key

    return genai.Client(**kwargs)

def call_gemini(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
    response_schema: Optional[Any] = None,
    response_mime_type: Optional[str] = None,
    tools: Optional[list[Any]] = None,
    client: Optional[genai.Client] = None,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    agent_name: Optional[str] = None,
    bill_id: Optional[str] = None,
) -> GeminiResponse:
    """
    Call Gemini API with timing, token usage tracking, structured output, and retry logic.
    
    Args:
        prompt: The text prompt or user message for Gemini.
        system_instruction: Optional system instructions/context.
        model: Target Gemini model name (default: gemini-2.5-flash).
        temperature: Sampling temperature (0.0 to 2.0).
        max_output_tokens: Maximum tokens in response.
        response_schema: Target Pydantic model or schema for structured JSON output.
        response_mime_type: MIME type of output (e.g. "application/json").
        tools: Optional list of tools (e.g. FunctionDeclaration or tool definitions).
        client: Optional explicit genai.Client instance.
        max_retries: Maximum number of retry attempts after initial call (total calls = 1 initial + max_retries).
        backoff_factor: Multiplier for exponential backoff sleep.
        
    Returns:
        GeminiResponse object with text, parsed output, token counts, and latency.
    """
    if client is None:
        client = get_gemini_client()

    config_kwargs: dict[str, Any] = {
        "temperature": temperature,
    }
    
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if max_output_tokens is not None:
        config_kwargs["max_output_tokens"] = max_output_tokens
    if response_schema is not None:
        config_kwargs["response_schema"] = response_schema
        if not response_mime_type:
            config_kwargs["response_mime_type"] = "application/json"
    if response_mime_type is not None:
        config_kwargs["response_mime_type"] = response_mime_type
    if tools is not None:
        wrapped_tools = []
        for tool in tools:
            if isinstance(tool, types.FunctionDeclaration):
                wrapped_tools.append(types.Tool(function_declarations=[tool]))
            else:
                wrapped_tools.append(tool)
        config_kwargs["tools"] = wrapped_tools

    config = types.GenerateContentConfig(**config_kwargs)

    last_exception = None
    start_time = time.perf_counter()

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count or 0
                completion_tokens = response.usage_metadata.candidates_token_count or 0
                total_tokens = response.usage_metadata.total_token_count or 0

            text_output = response.text or ""
            parsed_output = response.parsed if hasattr(response, "parsed") else None

            # Log LLM usage and estimated cost
            try:
                from app.services.usage_logger import log_llm_usage
                log_llm_usage(
                    agent_name=agent_name or "gemini",
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

        except APIError as e:
            last_exception = e
            status_code = getattr(e, "code", None)
            is_transient = status_code in (429, 500, 502, 503, 504) or "rate" in str(e).lower()
            
            if is_transient and attempt < max_retries:
                sleep_time = backoff_factor * (2 ** attempt)
                logger.warning(
                    f"Gemini API transient error (code={status_code}): {e}. "
                    f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"Gemini API error (code={status_code}): {e}")
                raise e
        except Exception as e:
            last_exception = e
            is_network = isinstance(e, (ConnectionError, TimeoutError, OSError)) or any(
                kw in str(e).lower() for kw in TRANSIENT_NETWORK_KEYWORDS
            )
            if attempt < max_retries and is_network:
                sleep_time = backoff_factor * (2 ** attempt)
                logger.warning(
                    f"Gemini API network error ({type(e).__name__}): {e}. "
                    f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"Gemini API call unexpected error: {e}")
                raise e

    if last_exception:
        raise last_exception
    raise RuntimeError("Call to Gemini failed without returning a response.")

def count_tokens(
    prompt: str,
    model: str = "gemini-2.5-flash",
    client: Optional[genai.Client] = None,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> int:
    """Calculate token count for a given text prompt using the Gemini API with transient error retries."""
    if client is None:
        client = get_gemini_client()

    for attempt in range(max_retries + 1):
        try:
            result = client.models.count_tokens(model=model, contents=prompt)
            return getattr(result, "total_tokens", 0) or 0
        except APIError as e:
            status_code = getattr(e, "code", None)
            is_transient = status_code in (429, 500, 502, 503, 504) or "rate" in str(e).lower()
            if is_transient and attempt < max_retries:
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise e
        except Exception as e:
            is_network = isinstance(e, (ConnectionError, TimeoutError, OSError)) or any(
                kw in str(e).lower() for kw in TRANSIENT_NETWORK_KEYWORDS
            )
            if attempt < max_retries and is_network:
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise e

    return 0
