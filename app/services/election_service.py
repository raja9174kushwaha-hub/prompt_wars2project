"""
Election Data Service – structured, static election knowledge base.
All data lives in-process to keep the repo under 10 MB and avoid
unnecessary Firestore reads for read-only reference content.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


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
# Election flow steps
# ---------------------------------------------------------------------------
ELECTION_STEPS: list[ElectionStep] = [
    ElectionStep(
        id=1,
        title="Voter Registration",
        description="Citizens enroll to participate in elections.",
        details=[
            "Check age & citizenship eligibility",
            "Submit registration form (online/offline)",
            "Provide ID & proof of address",
            "Receive voter ID / confirmation",
        ],
        icon="how_to_vote",
        color="#1565C0",
    ),
    ElectionStep(
        id=2,
        title="Candidate Nomination",
        description="Eligible individuals file their candidacy.",
        details=[
            "Meet age & eligibility criteria",
            "File nomination papers with election authority",
            "Pay nomination deposit",
            "Scrutiny & approval of nomination",
        ],
        icon="person_add",
        color="#2E7D32",
    ),
    ElectionStep(
        id=3,
        title="Campaigning",
        description="Candidates promote their platforms to voters.",
        details=[
            "Hold public rallies & meetings",
            "Run media & digital campaigns",
            "Follow the Model Code of Conduct",
            "Campaign period ends 48 hours before polling",
        ],
        icon="campaign",
        color="#E65100",
    ),
    ElectionStep(
        id=4,
        title="Voting",
        description="Registered voters cast their ballots.",
        details=[
            "Bring valid voter ID to polling booth",
            "Voter list verified by polling officer",
            "Cast vote (EVM / paper ballot)",
            "Ink mark applied to finger (anti-duplication)",
        ],
        icon="ballot",
        color="#6A1B9A",
    ),
    ElectionStep(
        id=5,
        title="Vote Counting",
        description="Ballots are tallied under official supervision.",
        details=[
            "Counting begins on declared date",
            "Representatives of all candidates present",
            "Results compiled round-by-round",
            "Disputes handled per election rules",
        ],
        icon="calculate",
        color="#00695C",
    ),
    ElectionStep(
        id=6,
        title="Result Declaration",
        description="Official winner is announced and certified.",
        details=[
            "Returning officer declares result",
            "Winner awarded certificate of election",
            "Defeated candidates may file election petitions",
            "Elected official takes oath of office",
        ],
        icon="emoji_events",
        color="#F57F17",
    ),
]

# ---------------------------------------------------------------------------
# Timeline phases
# ---------------------------------------------------------------------------
ELECTION_PHASES: list[ElectionPhase] = [
    ElectionPhase(1, "Pre-Election", "60–90 days", "Announcement, roll update, and preparation phase."),
    ElectionPhase(2, "Nomination", "14–21 days", "Filing and scrutiny of candidacy papers."),
    ElectionPhase(3, "Campaign", "14–21 days", "Active campaigning by parties and candidates."),
    ElectionPhase(4, "Polling Day", "1 day", "Registered voters cast their votes."),
    ElectionPhase(5, "Counting Day", "1 day", "Votes are counted and results announced."),
    ElectionPhase(6, "Post-Election", "7–30 days", "Certification, oath-taking, and dispute resolution."),
]

# ---------------------------------------------------------------------------
# Knowledge base articles
# ---------------------------------------------------------------------------
KNOWLEDGE_ARTICLES: list[KnowledgeArticle] = [
    KnowledgeArticle(
        id="what-is-election",
        title="What is an Election?",
        summary="A formal process by which citizens choose their representatives.",
        content=[
            "An election is a democratic process where eligible citizens vote to select individuals for public office or decide on referendums.",
            "Elections are the cornerstone of representative democracy, enabling peaceful transfer of power.",
            "They are governed by election laws and overseen by independent electoral commissions.",
            "Free and fair elections require transparency, voter access, and impartial administration.",
        ],
        category="basics",
    ),
    KnowledgeArticle(
        id="types-of-elections",
        title="Types of Elections",
        summary="Different elections serve different governmental levels and purposes.",
        content=[
            "**General Elections** – Held nationwide to elect the national legislature or executive.",
            "**State/Provincial Elections** – Determine representatives for state or provincial assemblies.",
            "**Local Body Elections** – Elect municipal, panchayat, or district-level officials.",
            "**By-Elections** – Held to fill a vacancy caused by death, resignation, or disqualification.",
            "**Referendums/Plebiscites** – Direct votes on a specific policy question or constitutional change.",
        ],
        category="types",
    ),
    KnowledgeArticle(
        id="voter-eligibility",
        title="Voter Eligibility",
        summary="Who can vote and what are the requirements?",
        content=[
            "Most democracies require voters to be citizens who have reached the minimum voting age (18 in most countries).",
            "Voters must not be disqualified by court order, mental incapacity declarations, or serving certain criminal sentences.",
            "Registration is required in most jurisdictions before an election date.",
            "Some countries use automatic registration; others require active enrollment by the citizen.",
            "Overseas citizens may vote via absentee ballot or at embassies in many countries.",
        ],
        category="eligibility",
    ),
    KnowledgeArticle(
        id="electoral-systems",
        title="Electoral Systems",
        summary="How votes are converted into seats or outcomes.",
        content=[
            "**First-Past-The-Post (FPTP)** – The candidate with the most votes wins, even without a majority.",
            "**Proportional Representation (PR)** – Seats are allocated proportional to each party's vote share.",
            "**Two-Round System** – A runoff is held if no candidate wins an outright majority in round one.",
            "**Mixed Systems** – Combine FPTP and PR elements (e.g., Germany's MMP system).",
            "The choice of system affects representation, coalition governments, and voter incentives.",
        ],
        category="systems",
    ),
]

# ---------------------------------------------------------------------------
# Quiz questions
# ---------------------------------------------------------------------------
QUIZ_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id=1,
        question="What is the minimum voting age in most democracies?",
        options=["16", "18", "21", "25"],
        correct_index=1,
        explanation="Most countries set the minimum voting age at 18, though some (like Austria and Scotland for certain elections) allow 16-year-olds to vote.",
    ),
    QuizQuestion(
        id=2,
        question="Which electoral system allocates seats proportional to each party's vote share?",
        options=["First-Past-The-Post", "Proportional Representation", "Two-Round System", "Block Voting"],
        correct_index=1,
        explanation="Proportional Representation (PR) ensures that the percentage of seats a party receives matches its percentage of the total votes.",
    ),
    QuizQuestion(
        id=3,
        question="What does the Model Code of Conduct govern?",
        options=["Voter registration rules", "Candidate and party behaviour during campaigns", "Vote counting procedures", "Result declaration process"],
        correct_index=1,
        explanation="The Model Code of Conduct (MCC) sets guidelines for political parties and candidates during the campaign period to ensure fair play.",
    ),
    QuizQuestion(
        id=4,
        question="What is a by-election?",
        options=["An election held abroad", "An election to fill a mid-term vacancy", "The second round of a general election", "An election for local bodies only"],
        correct_index=1,
        explanation="A by-election (or special election) is called to fill a vacancy in a constituency that arises between scheduled general elections.",
    ),
    QuizQuestion(
        id=5,
        question="Which document is typically required at a polling booth?",
        options=["Passport only", "Valid Voter ID / approved photo ID", "Birth certificate", "Tax returns"],
        correct_index=1,
        explanation="Most election authorities require a valid voter ID or approved photo identification to verify a voter's identity before they can cast their ballot.",
    ),
]


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
