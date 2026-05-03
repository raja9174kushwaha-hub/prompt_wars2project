"""
Chat routes – AI assistant endpoints.
All inputs are validated and sanitised before reaching the AI service.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.ai_service import get_ai_response
from app.utils.validators import (
    sanitize_message,
    validate_chat_history,
    validate_message,
)

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class HistoryEntry(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=500)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    chat_history: Optional[list[HistoryEntry]] = Field(default=None, max_length=10)
    language: str = Field(default="en", pattern="^(en|hi)$")

    @field_validator("message")
    @classmethod
    def sanitise_message(cls, v: str) -> str:
        return sanitize_message(v)


class ChatResponse(BaseModel):
    response: str
    language: str
    tokens_used: Optional[int] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the AI assistant",
    description="Accepts a user message and optional chat history; returns an AI-generated election-domain answer.",
)
@limiter.limit("20/minute")
async def chat_message(
    request: Request,
    payload: ChatRequest,
) -> ChatResponse:
    # Validate message content
    is_valid, error = validate_message(payload.message)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error)

    # Validate history
    history_dicts = None
    if payload.chat_history:
        raw_history = [h.model_dump() for h in payload.chat_history]
        ok, err = validate_chat_history(raw_history)
        if not ok:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err)
        history_dicts = raw_history

    logger.info(
        "Chat request | lang=%s | msg_len=%d | history_turns=%d",
        payload.language,
        len(payload.message),
        len(history_dicts) if history_dicts else 0,
    )

    ai_response = await get_ai_response(payload.message, history_dicts, payload.language)
    return ChatResponse(response=ai_response, language=payload.language)


@router.get(
    "/suggestions",
    summary="Get example questions",
    description="Returns pre-built example questions to help users get started.",
)
async def get_suggestions() -> dict:
    return {
        "suggestions": [
            "How does voter registration work?",
            "What is the election timeline?",
            "Explain the voting process step by step.",
            "What are the different types of elections?",
            "Who is eligible to vote?",
            "What happens on counting day?",
            "What is proportional representation?",
            "How is a candidate nominated?",
        ]
    }
