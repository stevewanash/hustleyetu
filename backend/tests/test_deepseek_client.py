import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field

from app.agents.deepseek_client import call_deepseek, get_deepseek_client, _convert_tools_for_openai
from app.agents.gemini_client import GeminiResponse


class DummySchema(BaseModel):
    summary: str = Field(description="Dummy summary")
    count: int = Field(default=1)


def test_convert_tools_for_openai():
    # Test dictionary input
    dict_tool = {"type": "function", "function": {"name": "test"}}
    res = _convert_tools_for_openai([dict_tool])
    assert res == [dict_tool]

    # Test object input with name & description
    mock_tool = MagicMock()
    mock_tool.name = "calculate"
    mock_tool.description = "Calc desc"
    res2 = _convert_tools_for_openai([mock_tool])
    assert res2 is not None
    assert res2[0]["function"]["name"] == "calculate"


def test_call_deepseek_success_mock():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Sample DeepSeek response text"
    
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 25
    mock_usage.total_tokens = 75
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    
    mock_client.chat.completions.create.return_value = mock_response

    result = call_deepseek(
        prompt="Hello DeepSeek",
        model="deepseek-chat",
        client=mock_client,
    )

    assert isinstance(result, GeminiResponse)
    assert result.text == "Sample DeepSeek response text"
    assert result.prompt_tokens == 50
    assert result.completion_tokens == 25
    assert result.total_tokens == 75
    assert result.model_name == "deepseek-chat"


def test_call_deepseek_structured_output_mock():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"summary": "Test summary", "count": 5}'
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
    
    mock_client.chat.completions.create.return_value = mock_response

    result = call_deepseek(
        prompt="Generate dummy schema",
        response_schema=DummySchema,
        client=mock_client,
    )

    assert result.parsed is not None
    assert isinstance(result.parsed, DummySchema)
    assert result.parsed.summary == "Test summary"
    assert result.parsed.count == 5
