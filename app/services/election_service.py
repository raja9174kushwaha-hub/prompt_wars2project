"""
Election Data Service – structured, static election knowledge base.
All data is loaded from content.json to keep the repo clean and allow
easy content expansion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any
from pathlib import Path


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class ElectionStep:
    id: int
    title: str
    description: str
    details: list[str]
    icon: str
    color: str


@dataclass
class ElectionPhase:
    id: int
    name: str
    duration: str
    description: str


@dataclass
class KnowledgeArticle:
    id: str
    title: str
    summary: str
    content: list[str]
    category: str


@dataclass
class QuizQuestion:
    id: int
    question: str
    options: list[str]
    correct_index: int
    explanation: str

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "content.json"

ELECTION_STEPS: list[ElectionStep] = []
ELECTION_PHASES: list[ElectionPhase] = []
KNOWLEDGE_ARTICLES: list[KnowledgeArticle] = []
QUIZ_QUESTIONS: list[QuizQuestion] = []

def _load_data() -> None:
    global ELECTION_STEPS, ELECTION_PHASES, KNOWLEDGE_ARTICLES, QUIZ_QUESTIONS
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        ELECTION_STEPS = [ElectionStep(**step) for step in data.get("steps", [])]
        ELECTION_PHASES = [ElectionPhase(**phase) for phase in data.get("phases", [])]
        KNOWLEDGE_ARTICLES = [KnowledgeArticle(**article) for article in data.get("articles", [])]
        QUIZ_QUESTIONS = [QuizQuestion(**quiz) for quiz in data.get("quizzes", [])]
    except Exception as e:
        import logging
        logging.getLogger("electionguide").error(f"Failed to load content.json: {e}")

_load_data()

# ---------------------------------------------------------------------------
# Public accessors – return plain dicts for JSON serialisation
# ---------------------------------------------------------------------------

def get_election_steps() -> list[dict[str, Any]]:
    return [asdict(s) for s in ELECTION_STEPS]


def get_election_phases() -> list[dict[str, Any]]:
    return [asdict(p) for p in ELECTION_PHASES]


def get_knowledge_articles(category: str | None = None) -> list[dict[str, Any]]:
    articles = KNOWLEDGE_ARTICLES
    if category:
        articles = [a for a in articles if a.category == category]
    return [asdict(a) for a in articles]


def get_knowledge_article(article_id: str) -> dict[str, Any] | None:
    for article in KNOWLEDGE_ARTICLES:
        if article.id == article_id:
            return asdict(article)
    return None


def get_quiz_questions() -> list[dict[str, Any]]:
    return [asdict(q) for q in QUIZ_QUESTIONS]
