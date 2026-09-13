"""
Safe AST-based calculator tool for deterministic financial calculations.
"""

import ast
import math
import operator
import re
from typing import Any, Dict

from google.genai import types

# Whitelisted binary operators
ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Whitelisted unary operators
ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluates a whitelisted AST node. Raises ValueError on forbidden nodes."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        raise ValueError(f"Unsupported constant type or value: {type(node.value).__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_BIN_OPS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        left_val = _eval_node(node.left)
        right_val = _eval_node(node.right)

        if op_type in (ast.Div, ast.Mod) and right_val == 0:
            raise ZeroDivisionError("Division or modulo by zero")

        return float(ALLOWED_BIN_OPS[op_type](left_val, right_val))

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARY_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

        operand_val = _eval_node(node.operand)
        return float(ALLOWED_UNARY_OPS[op_type](operand_val))

    else:
        raise ValueError(f"Forbidden or unsupported AST node: {type(node).__name__}")


def evaluate_expression(expression: str) -> float:
    """
    Safely evaluates a mathematical expression string using an AST-based whitelist.

    Only numbers, basic arithmetic operators (+, -, *, /, %, **), unary operators (+, -),
    and parenthesized grouping are allowed.

    Raises:
        ValueError: If expression is invalid, contains forbidden AST nodes, or evaluates to non-finite numbers.
        ZeroDivisionError: If division or modulo by zero occurs.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression must be a non-empty string")

    sanitized = expression.strip()

    # Normalize thousands separator commas in numbers (e.g. 1,000,000 -> 1000000)
    sanitized = re.sub(r'(?<=\d),(?=\d)', '', sanitized)

    try:
        parsed_ast = ast.parse(sanitized, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Invalid mathematical syntax: {e}") from e

    try:
        res = _eval_node(parsed_ast)
        if not math.isfinite(res):
            raise ValueError(f"Result is non-finite: {res}")
        return res
    except OverflowError as e:
        raise ValueError(f"Result overflowed: {e}") from e


def calculate(expression: str) -> Dict[str, Any]:
    """
    Top-level helper function that evaluates an expression and returns a structured dictionary result.

    Returns:
        dict: {"success": bool, "expression": str, "result": float | None, "error": str | None}
    """
    try:
        val = evaluate_expression(expression)
        return {
            "success": True,
            "expression": expression,
            "result": val,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "expression": expression if isinstance(expression, str) else str(expression),
            "result": None,
            "error": str(e)
        }


# Gemini Function Declaration schema for function calling using google.genai types
CALCULATOR_TOOL_SPEC = types.FunctionDeclaration(
    name="calculate",
    description=(
        "Evaluates a mathematical expression deterministically. "
        "Use this for ALL arithmetic operations (addition, subtraction, multiplication, division, percentages, power, etc.). "
        "Supports operators +, -, *, /, %, **, and parentheses. Numbers can include decimals."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "expression": types.Schema(
                type=types.Type.STRING,
                description="Mathematical expression to evaluate, e.g. '150000 * 0.025' or '(3500 - 500) * 0.16'."
            )
        },
        required=["expression"]
    )
)

# OpenAI-compatible function tool schema for DeepSeek / OpenAI SDK
CALCULATOR_TOOL_SPEC_OPENAI = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "Evaluates a mathematical expression deterministically. "
            "Use this for ALL arithmetic operations (addition, subtraction, multiplication, division, percentages, power, etc.). "
            "Supports operators +, -, *, /, %, **, and parentheses. Numbers can include decimals."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate, e.g. '150000 * 0.025' or '(3500 - 500) * 0.16'."
                }
            },
            "required": ["expression"]
        }
    }
}



def execute_calculator_tool(function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a tool call requested by Gemini.
    """
    if function_name != "calculate":
        return {
            "success": False,
            "expression": args.get("expression", "") if isinstance(args, dict) else "",
            "result": None,
            "error": f"Unknown tool function name: '{function_name}'"
        }

    expr = args.get("expression", "") if isinstance(args, dict) else ""
    return calculate(expr)
