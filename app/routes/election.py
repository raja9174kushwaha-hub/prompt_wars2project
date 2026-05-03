"""
Election data routes – serve structured election content.
All data is static/in-process; no DB round-trip required.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.services.election_service import (
    get_election_phases,
    get_election_steps,
    get_knowledge_article,
    get_knowledge_articles,
    get_quiz_questions,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/steps",
    summary="Election flow steps",
    description="Returns the ordered list of election process steps with descriptions.",
)
async def election_steps() -> dict:
    return {"steps": get_election_steps()}


@router.get(
    "/phases",
    summary="Election timeline phases",
    description="Returns the election timeline phases with typical durations.",
)
async def election_phases() -> dict:
    return {"phases": get_election_phases()}


@router.get(
    "/knowledge",
    summary="Knowledge base articles",
    description="Returns educational articles about elections. Filter by category.",
)
async def knowledge_articles(category: Optional[str] = None) -> dict:
    return {"articles": get_knowledge_articles(category)}


@router.get(
    "/knowledge/{article_id}",
    summary="Single knowledge article",
    description="Returns a single educational article by its ID.",
)
async def knowledge_article(article_id: str) -> dict:
    article = get_knowledge_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found.",
        )
    return {"article": article}


@router.get(
    "/quiz",
    summary="Quiz questions",
    description="Returns multiple-choice quiz questions to test election knowledge.",
)
async def quiz_questions() -> dict:
    return {"questions": get_quiz_questions()}
