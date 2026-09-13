import pytest
from unittest.mock import patch, MagicMock

from app.agents.llm_client import call_llm
from app.agents.gemini_client import GeminiResponse


@patch("app.agents.llm_client.settings")
@patch("app.agents.llm_client.call_gemini")
def test_call_llm_routes_to_gemini(mock_call_gemini, mock_settings):
    mock_settings.AI_PROVIDER = "gemini"
    mock_call_gemini.return_value = GeminiResponse(text="Gemini answer", model_name="gemini-2.5-flash")

    res = call_llm(prompt="Test prompt", model="gemini-2.5-flash")

    mock_call_gemini.assert_called_once()
    assert res.text == "Gemini answer"


@patch("app.agents.llm_client.settings")
@patch("app.agents.llm_client.call_deepseek")
def test_call_llm_routes_to_deepseek(mock_call_deepseek, mock_settings):
    mock_settings.AI_PROVIDER = "deepseek"
    mock_call_deepseek.return_value = GeminiResponse(text="DeepSeek answer", model_name="deepseek-chat")

    res = call_llm(prompt="Test prompt", model="gemini-2.5-flash")

    mock_call_deepseek.assert_called_once()
    # Check that model gemini-2.5-flash was mapped to deepseek-chat
    call_kwargs = mock_call_deepseek.call_args.kwargs
    assert call_kwargs["model"] == "deepseek-chat"
    assert res.text == "DeepSeek answer"
