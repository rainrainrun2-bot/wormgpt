"""Deterministic intent handlers.

These run before the ELIZA / Markov layers so that questions with a real
answer ("what time is it", "12 * 7") get a real answer instead of a vibe.
"""

from __future__ import annotations

import ast
import datetime as _dt
import operator as op
import re
from typing import Callable, List, Optional, Tuple

# --- Safe arithmetic evaluator ------------------------------------------------

_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
_UNARY_OPS = {ast.UAdd: op.pos, ast.USub: op.neg}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


def try_math(text: str) -> Optional[str]:
    """If ``text`` looks like an arithmetic expression, evaluate it safely."""
    cleaned = text.strip().rstrip("?")
    cleaned = re.sub(r"^(what'?s?|whats|calculate|compute|eval(?:uate)?)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = (
        cleaned.replace("plus", "+")
        .replace("minus", "-")
        .replace("times", "*")
        .replace("divided by", "/")
        .replace("x", "*")
        .replace("^", "**")
    )
    if not re.fullmatch(r"[\d\s+\-*/().%]+(\*\*[\d\s+\-*/().%]+)?", cleaned):
        return None
    if not re.search(r"[+\-*/%]", cleaned):
        return None  # bare numbers aren't a question
    try:
        tree = ast.parse(cleaned, mode="eval")
        result = _safe_eval(tree)
    except (SyntaxError, ValueError, ZeroDivisionError):
        return None
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"{result}"


# --- Time / date --------------------------------------------------------------


def try_time(text: str) -> Optional[str]:
    if re.search(r"\b(time|clock)\b", text, re.IGNORECASE):
        return _dt.datetime.now().strftime("It's %H:%M.")
    return None


def try_date(text: str) -> Optional[str]:
    if re.search(r"\b(date|day|today)\b", text, re.IGNORECASE):
        return _dt.date.today().strftime("Today is %A, %B %d, %Y.")
    return None


# --- Identity / help ----------------------------------------------------------


def try_identity(text: str) -> Optional[str]:
    if re.search(r"\b(who are you|your name|what are you)\b", text, re.IGNORECASE):
        return (
            "I'm HolyGPT, a small offline assistant. No APIs, no large "
            "language models, just classical pattern matching and a Markov "
            "chain."
        )
    if re.search(r"\bhelp\b", text, re.IGNORECASE):
        return (
            "Try asking me the time or date, doing simple math (e.g. "
            "'12 * 7'), or just chatting. Type /train <path> to teach me "
            "from a text file, or /quit to exit."
        )
    return None


# --- Dispatcher ---------------------------------------------------------------

Handler = Callable[[str], Optional[str]]

DEFAULT_HANDLERS: List[Handler] = [
    try_identity,
    try_time,
    try_date,
    try_math,
]


def resolve(text: str, handlers: Optional[List[Handler]] = None) -> Optional[str]:
    """Run handlers in order; return the first non-None response."""
    for handler in handlers or DEFAULT_HANDLERS:
        try:
            result = handler(text)
        except Exception:  # pragma: no cover - handler must never crash bot
            result = None
        if result is not None:
            return result
    return None
