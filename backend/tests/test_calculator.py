"""
Unit tests for the safe AST-based calculator tool.
"""

import pytest
from google.genai import types

from app.agents.calculator import (
    evaluate_expression,
    calculate,
    CALCULATOR_TOOL_SPEC,
    execute_calculator_tool,
)


def test_basic_arithmetic():
    assert evaluate_expression("2 + 3") == 5.0
    assert evaluate_expression("10 - 4") == 6.0
    assert evaluate_expression("6 * 7") == 42.0
    assert evaluate_expression("20 / 4") == 5.0
    assert evaluate_expression("10 % 3") == 1.0
    assert evaluate_expression("2 ** 3") == 8.0


def test_complex_and_nested_expressions():
    assert evaluate_expression("(150000 - 50000) * 0.16 / 12") == pytest.approx(1333.3333333333333)
    assert evaluate_expression("((5 + 3) * (10 - 2)) / 4") == 16.0
    assert evaluate_expression("100 + 200 * 3 - 50") == 650.0


def test_floating_and_negative_numbers():
    assert evaluate_expression("-10.5 + 5") == -5.5
    assert evaluate_expression("+15.0 * -2.5") == -37.5
    assert evaluate_expression("0.025 * 50000") == 1250.0


def test_comma_formatted_numbers():
    assert evaluate_expression("150,000 * 0.025") == 3750.0
    assert evaluate_expression("1,000,000 / 100") == 10000.0
    assert evaluate_expression("1,234,567,890 / 100") == 12345678.9


def test_division_and_modulo_by_zero():
    with pytest.raises(ZeroDivisionError, match="Division or modulo by zero"):
        evaluate_expression("10 / 0")

    with pytest.raises(ZeroDivisionError, match="Division or modulo by zero"):
        evaluate_expression("10 % 0")


def test_non_finite_results():
    with pytest.raises(ValueError, match="Result overflowed|Result is non-finite"):
        evaluate_expression("10 ** 1000")

    res_overflow = calculate("10 ** 1000")
    assert res_overflow["success"] is False
    assert any(msg in res_overflow["error"] for msg in ["Result overflowed", "Result is non-finite"])


def test_invalid_input_types_and_empty_strings():
    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        evaluate_expression("")

    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        evaluate_expression("   ")

    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        evaluate_expression(None)

    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        evaluate_expression(5)

    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        evaluate_expression([1, 2])

    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        evaluate_expression({"a": 1})


def test_invalid_syntax():
    with pytest.raises(ValueError, match="Invalid mathematical syntax"):
        evaluate_expression("5 + * 3")

    with pytest.raises(ValueError, match="Invalid mathematical syntax"):
        evaluate_expression("(10 + 5")


def test_security_rejection_of_forbidden_nodes():
    # Variable names
    with pytest.raises(ValueError, match="Forbidden or unsupported AST node: Name"):
        evaluate_expression("x + 1")

    # Function calls
    with pytest.raises(ValueError, match="Forbidden or unsupported AST node: Call"):
        evaluate_expression("abs(-5)")

    # Attribute access
    with pytest.raises(ValueError, match="Forbidden or unsupported AST node: Attribute"):
        evaluate_expression("''.__class__")

    # Import / Exec attempts
    with pytest.raises(ValueError, match="Invalid mathematical syntax|Forbidden or unsupported AST node"):
        evaluate_expression("__import__('os').system('ls')")

    # String constants
    with pytest.raises(ValueError, match="Unsupported constant type"):
        evaluate_expression("'hello' + 'world'")

    # Boolean constants
    with pytest.raises(ValueError, match="Unsupported constant type"):
        evaluate_expression("True + 1")


def test_calculate_helper():
    res_success = calculate("100 * 0.16")
    assert res_success["success"] is True
    assert res_success["expression"] == "100 * 0.16"
    assert res_success["result"] == 16.0
    assert res_success["error"] is None

    res_fail = calculate("10 / 0")
    assert res_fail["success"] is False
    assert res_fail["result"] is None
    assert "Division or modulo by zero" in res_fail["error"]


def test_tool_spec_and_dispatcher():
    assert isinstance(CALCULATOR_TOOL_SPEC, types.FunctionDeclaration)
    assert CALCULATOR_TOOL_SPEC.name == "calculate"
    assert "expression" in CALCULATOR_TOOL_SPEC.parameters.properties

    # Dispatcher call success
    tool_res = execute_calculator_tool("calculate", {"expression": "250 * 4"})
    assert tool_res["success"] is True
    assert tool_res["result"] == 1000.0

    # Dispatcher unknown function
    tool_err = execute_calculator_tool("unknown_tool", {"expression": "250 * 4"})
    assert tool_err["success"] is False
    assert "Unknown tool function name" in tool_err["error"]
