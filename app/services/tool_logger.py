"""Tool execution logging helper.

This module provides a stub logger for tool executions. Once async database
sessions are fully wired, it can be updated to persist ToolExecution records.
"""

import logging
from typing import Any, Dict, Optional

from app.models.database import ToolExecution

logger = logging.getLogger(__name__)


def log_tool_execution(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Any,
    success: bool,
    duration_ms: Optional[int] = None,
    conversation_id: Optional[str] = None,
) -> ToolExecution:
    """Log a tool execution.

    Currently logs to the standard logger. When the async DB layer is ready,
    this should persist a ToolExecution record via an async session.

    Args:
        tool_name: Name of the tool that was executed.
        arguments: Arguments passed to the tool.
        result: Result returned by the tool.
        success: Whether the execution succeeded.
        duration_ms: Execution duration in milliseconds.
        conversation_id: Optional conversation UUID string.

    Returns:
        A ToolExecution instance (in-memory only for now).
    """
    conv_id = conversation_id or "N/A"
    logger.info(
        "Tool executed: %s | conversation=%s | success=%s | duration_ms=%s",
        tool_name,
        conv_id,
        success,
        duration_ms,
    )

    # Build an in-memory record so callers can inspect it in tests.
    record = ToolExecution(
        tool_name=tool_name,
        arguments=arguments,
        result=result if isinstance(result, dict) else {"output": str(result)},
        success=success,
        duration_ms=duration_ms,
        conversation_id=conversation_id,
    )
    return record
