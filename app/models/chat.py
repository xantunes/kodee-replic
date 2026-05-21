"""Pydantic models for chat API."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="Message content from the user")
    session_id: Optional[str] = Field(
        default=None, description="Optional session identifier for conversation continuity"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    message: str = Field(..., description="Response message from the assistant")
    actions: List[Dict] = Field(
        default_factory=list, description="List of actions to be performed"
    )
    session_id: str = Field(..., description="Session identifier for the conversation")
