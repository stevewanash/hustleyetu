import pytest
from unittest.mock import MagicMock, patch
from app.services.usage_logger import calculate_estimated_cost, log_llm_usage


def test_calculate_estimated_cost_gemini_flash():
    """Verify Gemini Flash pricing math: $0.15/1M in, $0.60/1M out."""
    # 1,000,000 prompt tokens = $0.15, 1,000,000 completion = $0.60 -> $0.75
    cost = calculate_estimated_cost("gemini-2.5-flash", 1_000_000, 1_000_000)
    assert cost == 0.75

    # 10,000 prompt tokens = $0.0015, 1,000 completion = $0.0006 -> $0.0021
    cost2 = calculate_estimated_cost("gemini-2.5-flash", 10_000, 1_000)
    assert cost2 == 0.0021


def test_calculate_estimated_cost_embedding():
    """Verify text-embedding-004 pricing math: $0.025/1M in."""
    cost = calculate_estimated_cost("text-embedding-004", 1_000_000, 0)
    assert cost == 0.025


def test_calculate_estimated_cost_deepseek():
    """Verify DeepSeek Chat pricing math: $0.14/1M in, $0.28/1M out."""
    cost = calculate_estimated_cost("deepseek-chat", 1_000_000, 1_000_000)
    assert cost == 0.42


@patch("app.services.usage_logger.supabase_admin")
def test_log_llm_usage_database_insert(mock_db):
    """Verify log_llm_usage formats payload and calls Supabase insert."""
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value.data = [{"id": "log-1"}]
    mock_db.table.return_value = mock_table

    result = log_llm_usage(
        agent_name="summarizer",
        model="gemini-2.5-flash",
        prompt_tokens=1500,
        completion_tokens=400,
        total_tokens=1900,
        latency_ms=850.5,
        bill_id="test-bill-uuid"
    )

    assert result is not None
    mock_db.table.assert_called_with("llm_usage_log")
    insert_call_args = mock_table.insert.call_args[0][0]
    assert insert_call_args["agent_name"] == "summarizer"
    assert insert_call_args["model"] == "gemini-2.5-flash"
    assert insert_call_args["prompt_tokens"] == 1500
    assert insert_call_args["completion_tokens"] == 400
    assert insert_call_args["estimated_cost_usd"] > 0
