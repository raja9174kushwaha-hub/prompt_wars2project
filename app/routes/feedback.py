"""
Feedback and analytics API routes.

Provides endpoints for collecting user feedback and
retrieving analytics summaries from Google Cloud Firestore.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.analytics_service import (
    log_feedback,
    log_quiz_result,
    get_analytics_summary,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response Models ─────────────────────────────────────────────


class FeedbackRequest(BaseModel):
    """Schema for user feedback submission."""

    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5.")
    comment: str = Field(default="", max_length=500, description="Optional comment.")
    page: str = Field(default="general", max_length=50, description="Page context.")

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v: str) -> str:
        """Strip whitespace and basic HTML from comment."""
        return v.strip().replace("<", "&lt;").replace(">", "&gt;")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    success: bool
    message: str
    doc_id: Optional[str] = None


class QuizResultRequest(BaseModel):
    """Schema for quiz result submission."""

    score: int = Field(..., ge=0, description="Number of correct answers.")
    total: int = Field(..., ge=1, description="Total number of questions.")
    time_taken_seconds: float = Field(
        default=0.0, ge=0, description="Time taken in seconds."
    )


class QuizResultResponse(BaseModel):
    """Response after submitting quiz results."""

    success: bool
    percentage: float
    doc_id: Optional[str] = None


class AnalyticsSummaryResponse(BaseModel):
    """Aggregated analytics data."""

    available: bool
    total_chats: int = 0
    total_quizzes: int = 0
    avg_quiz_score: float = 0.0
    total_feedback: int = 0
    message: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit user feedback",
    description="Stores user feedback (rating + optional comment) in Firestore.",
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Accept and store user feedback.

    Args:
        request: FeedbackRequest with rating (1-5) and optional comment.

    Returns:
        FeedbackResponse confirming storage.
    """
    logger.info("Feedback received: rating=%d page=%s", request.rating, request.page)

    doc_id = await log_feedback(
        rating=request.rating,
        comment=request.comment,
        page=request.page,
    )

    return FeedbackResponse(
        success=True,
        message="Thank you for your feedback!",
        doc_id=doc_id,
    )


@router.post(
    "/quiz-result",
    response_model=QuizResultResponse,
    summary="Submit quiz results",
    description="Stores quiz completion data in Firestore for analytics.",
)
async def submit_quiz_result(request: QuizResultRequest) -> QuizResultResponse:
    """
    Accept and store quiz completion results.

    Args:
        request: QuizResultRequest with score, total, and time taken.

    Returns:
        QuizResultResponse with percentage and document ID.
    """
    percentage = round((request.score / max(request.total, 1)) * 100, 1)
    logger.info("Quiz result: %d/%d (%.1f%%)", request.score, request.total, percentage)

    doc_id = await log_quiz_result(
        score=request.score,
        total=request.total,
        time_taken_seconds=request.time_taken_seconds,
    )

    return QuizResultResponse(
        success=True,
        percentage=percentage,
        doc_id=doc_id,
    )


@router.get(
    "/analytics",
    response_model=AnalyticsSummaryResponse,
    summary="Get analytics summary",
    description="Returns aggregated usage statistics from Firestore.",
)
async def analytics_summary() -> AnalyticsSummaryResponse:
    """
    Fetch aggregated analytics from Firestore.

    Returns:
        AnalyticsSummaryResponse with chat, quiz, and feedback counts.
    """
    data = await get_analytics_summary()
    return AnalyticsSummaryResponse(**data)
