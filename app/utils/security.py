"""Security utilities for input validation and sanitization."""

import re
from typing import Any


# Patterns for common injection attempts
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
    r"(--|#|/\*|\*/)",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    r"(\bAND\b\s+\d+\s*=\s*\d+)",
]

XSS_PATTERNS = [
    r"<script[^>]*>[\s\S]*?</script>",
    r"javascript:",
    r"on\w+\s*=",
]


def sanitize_input(text: str) -> str:
    """Remove potentially dangerous characters from user input."""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Strip control characters except newlines and tabs
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return text.strip()


def check_sql_injection(text: str) -> bool:
    """Return True if the text contains potential SQL injection patterns."""
    upper = text.upper()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, upper, re.IGNORECASE):
            return True
    return False


def check_xss(text: str) -> bool:
    """Return True if the text contains potential XSS patterns."""
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def validate_chat_input(message: str) -> dict[str, Any]:
    """Validate a chat message for security issues.

    Returns a dict with:
        - safe: bool — whether the message passed validation
        - sanitized: str — the sanitized message
        - issues: list[str] — list of detected issue names
    """
    issues: list[str] = []
    sanitized = sanitize_input(message)

    if check_sql_injection(sanitized):
        issues.append("sql_injection")
    if check_xss(sanitized):
        issues.append("xss")

    return {
        "safe": len(issues) == 0,
        "sanitized": sanitized,
        "issues": issues,
    }
