"""
Analytics Service – Google Cloud Firestore integration.

Stores user interaction analytics (chat sessions, feedback, quiz scores)
in Firestore for data-driven insights and continuous improvement.

This service gracefully degrades if Firestore is unavailable,
ensuring the main application remains functional.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Firestore client singleton
_firestore_client = None
_firestore_available = False


def _get_firestore_client():
    """
    Initialize and cache the Firestore client singleton.

    Uses Application Default Credentials (ADC) on Cloud Run,
    which requires no explicit key management.

    Returns:
        google.cloud.firestore.Client or None if unavailable.
    """
    global _firestore_client, _firestore_available

    if _firestore_client is not None:
        return _firestore_client

    try:
        from google.cloud import firestore
        _firestore_client = firestore.Client()
        _firestore_available = True
        logger.info("Firestore client initialized successfully.")
        return _firestore_client
    except ImportError:
        logger.warning("google-cloud-firestore not installed. Analytics disabled.")
        _firestore_available = False
        return None
    except Exception as exc:
        logger.warning("Firestore unavailable: %s. Analytics disabled.", exc)
        _firestore_available = False
        return None


def is_firestore_available() -> bool:
    """Check whether the Firestore client is available."""
    _get_firestore_client()
    return _firestore_available


async def log_chat_interaction(
    message: str,
    response: str,
    language: str = "en",
    response_time_ms: float = 0.0,
) -> Optional[str]:
    """
    Log a chat interaction to Firestore for analytics.

    Args:
        message: The user's sanitized message (truncated for privacy).
        response: The AI response (truncated).
        language: Language code (en/hi).
        response_time_ms: Response latency in milliseconds.

    Returns:
        Document ID if stored successfully, None otherwise.
    """
    client = _get_firestore_client()
    if not client:
        return None

    try:
        doc_data: dict[str, Any] = {
            "type": "chat",
            "message_preview": message[:100],  # Truncate for privacy
            "response_preview": response[:200],
            "language": language,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now(timezone.utc),
        }
        collection = client.collection("electionguide_analytics")
        _, doc_ref = collection.add(doc_data)
        logger.debug("Chat analytics logged: %s", doc_ref.id)
        return doc_ref.id
    except Exception as exc:
        logger.warning("Failed to log chat analytics: %s", exc)
        return None


async def log_feedback(
    rating: int,
    comment: str = "",
    page: str = "general",
) -> Optional[str]:
    """
    Store user feedback in Firestore.

    Args:
        rating: Feedback rating (1-5 stars).
        comment: Optional user comment.
        page: The page/section the feedback is about.

    Returns:
        Document ID if stored successfully, None otherwise.
    """
    client = _get_firestore_client()
    if not client:
        return None

    try:
        doc_data: dict[str, Any] = {
            "type": "feedback",
            "rating": rating,
            "comment": comment[:500],  # Truncate for safety
            "page": page,
            "timestamp": datetime.now(timezone.utc),
        }
        collection = client.collection("electionguide_feedback")
        _, doc_ref = collection.add(doc_data)
        logger.info("Feedback stored: %s (rating=%d)", doc_ref.id, rating)
        return doc_ref.id
    except Exception as exc:
        logger.warning("Failed to store feedback: %s", exc)
        return None


async def log_quiz_result(
    score: int,
    total: int,
    time_taken_seconds: float = 0.0,
) -> Optional[str]:
    """
    Log quiz completion results to Firestore.

    Args:
        score: Number of correct answers.
        total: Total number of questions.
        time_taken_seconds: Time to complete the quiz.

    Returns:
        Document ID if stored successfully, None otherwise.
    """
    client = _get_firestore_client()
    if not client:
        return None

    try:
        doc_data: dict[str, Any] = {
            "type": "quiz_result",
            "score": score,
            "total": total,
            "percentage": round((score / max(total, 1)) * 100, 1),
            "time_taken_seconds": time_taken_seconds,
            "timestamp": datetime.now(timezone.utc),
        }
        collection = client.collection("electionguide_analytics")
        _, doc_ref = collection.add(doc_data)
        logger.debug("Quiz result logged: %s", doc_ref.id)
        return doc_ref.id
    except Exception as exc:
        logger.warning("Failed to log quiz result: %s", exc)
        return None


async def get_analytics_summary() -> dict[str, Any]:
    """
    Retrieve a summary of analytics data from Firestore.

    Returns:
        Dictionary with total_chats, total_quizzes, avg_quiz_score, etc.
    """
    client = _get_firestore_client()
    if not client:
        return {"available": False, "message": "Analytics not configured."}

    try:
        analytics_col = client.collection("electionguide_analytics")

        # Count chat interactions
        chat_docs = list(analytics_col.where("type", "==", "chat").limit(1000).stream())
        total_chats = len(chat_docs)

        # Count and average quiz results
        quiz_docs = list(analytics_col.where("type", "==", "quiz_result").limit(1000).stream())
        total_quizzes = len(quiz_docs)
        avg_score = 0.0
        if total_quizzes > 0:
            scores = [doc.to_dict().get("percentage", 0) for doc in quiz_docs]
            avg_score = round(sum(scores) / len(scores), 1)

        # Count feedback
        feedback_col = client.collection("electionguide_feedback")
        feedback_docs = list(feedback_col.limit(1000).stream())
        total_feedback = len(feedback_docs)

        return {
            "available": True,
            "total_chats": total_chats,
            "total_quizzes": total_quizzes,
            "avg_quiz_score": avg_score,
            "total_feedback": total_feedback,
        }
    except Exception as exc:
        logger.warning("Failed to fetch analytics summary: %s", exc)
        return {"available": False, "error": str(exc)}
