from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import models

logger = logging.getLogger("ats_service")


# ============================================================
# Configuration
# ============================================================

# Configurable via environment variable so bumping the resume
# parser doesn't require a code change + redeploy just to keep
# this endpoint from 409-ing on every resume.
PARSER_VERSION_REQUIRED = os.getenv(
    "ATS_PARSER_VERSION_REQUIRED",
    "2.8",
)

_EDUCATION_CONNECTOR_PATTERN = re.compile(
    r"\s+(?:and|or)\s+",
    flags=re.IGNORECASE,
)

# Column on models.Resume that identifies its owner. Centralized
# here so it's one place to fix if your schema differs.
RESUME_OWNER_FIELD = os.getenv(
    "ATS_RESUME_OWNER_FIELD",
    "user_id",
)

SCORE_MIN = Decimal("0.00")
SCORE_MAX = Decimal("100.00")

# ============================================================
# ATS weighting
# ============================================================

SKILL_WEIGHT = Decimal("40")
EXPERIENCE_WEIGHT = Decimal("20")
EDUCATION_WEIGHT = Decimal("15")
KEYWORD_WEIGHT = Decimal("25")


# ============================================================
# Stop words
# ============================================================

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "we",
    "with",
    "will",
    "you",
    "your",
    "our",
    "looking",
    "look",
    "candidate",
    "candidates",
    "role",
    "roles",
    "job",
    "jobs",
    "position",
    "positions",
    "required",
    "requirements",
    "requirement",
    "strong",
    "knowledge",
    "work",
    "working",
    "responsibilities",
    "responsibility",
    "including",
    "related",
    "field",
    "years",
    "year",
    "must",
    "should",
    "ability",
    "abilities",
    "preferred",
    "prefer",
    "plus",
    "good",
    "excellent",
    "using",
    "use",
    "based",
    "etc",

    # Job-logistics terms. These describe the posting itself
    # (schedule, location arrangement, seniority band) and are
    # not something a candidate would ever literally write on a
    # resume as a qualification - matching against them produces
    # unfixable, nonsensical "missing keyword" advice.
    "full-time",
    "part-time",
    "fulltime",
    "parttime",
    "onsite",
    "on-site",
    "remote",
    "hybrid",
    "entry-level",
    "mid-level",
    "senior-level",
    "entry",
    "level",
    "needed",
    "immediate",
    "immediately",
    "asap",
    "urgent",
    "urgently",
}


# ============================================================
# Skill aliases
# ============================================================

SKILL_ALIASES: dict[str, str] = {

    # Python
    "python": "python",
    "python3": "python",
    "python 3": "python",

    # FastAPI
    "fastapi": "fastapi",
    "fast api": "fastapi",

    # SQL / databases
    "sql": "sql",
    "mysql": "mysql",
    "mysql database": "mysql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgresql database": "postgresql",
    "postgressql": "postgresql",  # <--- Place it right here
    "mongodb": "mongodb",
    "mongo db": "mongodb",
    "mongo": "mongodb",
    "mongodb database": "mongodb",
    "redis": "redis",

    # JavaScript
    "javascript": "javascript",
    "java script": "javascript",
    "js": "javascript",

    "typescript": "typescript",
    "type script": "typescript",
    "ts": "typescript",

    # Frontend
    "react": "react",
    "reactjs": "react",
    "react js": "react",

    "html": "html",
    "html5": "html",

    "css": "css",
    "css3": "css",

    # Node
    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "node.js": "node.js",

    # APIs
    "rest api": "rest api",
    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "restful apis development": "rest api",

    "api": "api",
    "apis": "api",
    "api development": "api development",
    "api integration": "api integration",

    # Version control
    "git": "git",
    "github": "github",
    "source control": "version control",
    "version-control": "version control",
    "version control": "version control",

    # Testing
    "unit test": "unit testing",
    "unit tests": "unit testing",
    "unit testing": "unit testing",
    "automated testing": "automated testing",
    "test automation": "test automation",
    "integration testing": "integration testing",
    "pytest": "pytest",


    # Cloud / DevOps
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",

    "aws": "aws",
    "amazon web services": "aws",
    "aws cloud": "aws",

    "azure": "azure",

    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",

    # AI / ML
    "machine learning": "machine learning",
    "machine-learning": "machine learning",
    "ml": "machine learning",

    "artificial intelligence": "artificial intelligence",
    "artificial-intelligence": "artificial intelligence",
    "ai": "artificial intelligence",

    # Data
    "excel": "excel",
    "microsoft excel": "excel",

    "power bi": "power bi",
    "powerbi": "power bi",

    "tableau": "tableau",

    "pandas": "pandas",
    "numpy": "numpy",

    # Programming languages
    "java": "java",
    "c++": "c++",
    "c plus plus": "c++",
    "c#": "c#",
    "c sharp": "c#",
    "c": "c",
    "php": "php",

    # Backend
    "flask": "flask",
    "django": "django",
    "spring": "spring",
    "spring boot": "spring boot",

    # Python ecosystem
    "sqlalchemy": "sqlalchemy",
    "pydantic": "pydantic",
    "jwt": "jwt",
    "json web token": "jwt",
    "pytest": "pytest",

    # Tools
    "linux": "linux",
    "postman": "postman",
}



# ============================================================
# Keyword aliases
# ============================================================

KEYWORD_ALIASES: dict[str, str] = {
    "bachelor degree": "bachelor's degree",
    "bachelors degree": "bachelor's degree",

    "master degree": "master's degree",
    "masters degree": "master's degree",

    "computer application": "computer applications",

    "computer science engineering": "computer science",
    "computer science and engineering": "computer science",

    "information technology engineering": "information technology",
    "information technology and engineering": "information technology",

    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",

    "problem-solving": "problem solving",

    "object-oriented programming": "object oriented programming",

    "data analytics": "data analytics",
    "data analysis": "data analysis",
}


KEYWORD_PHRASE_VARIANTS = {
    "relational database": "relational database",
    "relational databases": "relational database",

    "deploy application": "application deployment",
    "deploy applications": "application deployment",
    "deploying application": "application deployment",
    "deploying applications": "application deployment",

    "cloud deployment": "cloud deployment",
    "cloud deployments": "cloud deployment",

    "problem-solving": "problem solving",
    "problem solving": "problem solving",
}

# ============================================================
# Education hierarchy
# ============================================================

EDUCATION_LEVELS: dict[str, int] = {
    # Doctoral
    "phd": 5,
    "ph.d": 5,
    "doctorate": 5,
    "doctoral": 5,

    # Master's
    "master": 4,
    "masters": 4,
    "master's": 4,
    "master degree": 4,
    "master's degree": 4,
    "masters degree": 4,
    "mtech": 4,
    "m.tech": 4,
    "mca": 4,
    "msc": 4,
    "m.sc": 4,
    "mba": 4,
    "m.com": 4,
    "mcom": 4,

    # Bachelor's
    "bachelor": 3,
    "bachelors": 3,
    "bachelor's": 3,
    "bachelor degree": 3,
    "bachelor's degree": 3,
    "bachelors degree": 3,
    "btech": 3,
    "b.tech": 3,
    "bsc": 3,
    "b.sc": 3,
    "bca": 3,
    "b.com": 3,
    "bcom": 3,

    # Diploma / Associate
    "diploma": 2,
    "associate": 2,

    # School
    "intermediate": 1,
    "12th": 1,
    "higher secondary": 1,
    "10th": 0,
    "secondary": 0,
}

ATS_STANDALONE_KEYWORDS = {
    # Backend / engineering
    "backend",
    "frontend",
    "fullstack",
    "full-stack",
    "api",
    "apis",
    "development",
    "testing",
    "debugging",
    "integration",
    "deployment",
    "authentication",
    "authorization",
    "security",
    "database",
    "databases",
    "architecture",
    "scalability",
    "performance",
    "optimization",

    # Engineering practices
    "automation",
    "documentation",
    "maintenance",
    "monitoring",
    "troubleshooting",
    "implementation",
    "integration",
    "validation",

    # Development methodologies
    "agile",
    "scrum",
    "sprint",

    # Backend concepts
    "microservices",
    "services",
    "endpoints",
    "apis",
    "integration",
    "deployment",

    # Quality
    "testing",
    "unit",
    "integration",
    "pytest",

    # Collaboration / engineering
    "collaboration",
    "teamwork",
    "code",
    "review",
}

# ============================================================
# Generic / low-information ATS keywords
# ============================================================

GENERIC_ATS_KEYWORDS: frozenset[str] = frozenset({
    "candidate",
    "candidates",
    "applicant",
    "applicants",

    "experience",
    "experiences",

    "skill",
    "skills",

    "service",
    "services",

    "system",
    "systems",

    "application",
    "applications",

    "software",

    "technology",
    "technologies",

    "database",
    "databases",

    "development",
    "developments",

    "developer",
    "developers",

    "team",
    "teams",

    "work",
    "works",

    "role",
    "roles",

    "job",
    "jobs",

    "position",
    "positions",

    "company",
    "companies",

    "environment",
    "environments",

    "solution",
    "solutions",

    "project",
    "projects",

    "responsibility",
    "responsibilities",

    "requirement",
    "requirements",

    "qualification",
    "qualifications",
})


# ============================================================
# Education field groups
# ============================================================

EDUCATION_FIELD_GROUPS: list[set[str]] = [
    {
        "computer applications",
        "computer application",
        "bca",
        "bachelor of computer applications",
        "mca",
        "master of computer applications",
    },
    {
        "computer science",
        "computer science engineering",
        "computer science and engineering",
        "cse",
        "btech computer science",
        "b.tech computer science",
    },
    {
        "information technology",
        "information technology engineering",
        "information technology and engineering",
        "it degree",
    },
    {
        "software engineering",
        "software engineering and development",
    },
    {
        "information systems",
        "information system",
    },
    {
        "electronics",
        "electronics and communication",
        "electonics and communications",
        "electronical and electronics",
        "electronics and communication engineering",
        "ece",
    },
    {
        "commerce",
        "commerce and computer applications",
        "b.com",
        "bcom",
        "m.com",
        "mcom",
    },


    {
        "mechanical engineering",
        "mechanical",
    },

    {
        "civil engineering",
        "civil",
    },

    {
        "business administration",
        "business management",
        "management",
        "mba",
    },
]

ATS_CONTROLLED_PHRASES: tuple[str, ...] = (
    "backend developer",
    "backend development",
    "software development",
    "web development",
    "api development",
    "api integration",
    "rest api",
    "rest api development",
    "unit testing",
    "automated testing",
    "integration testing",
    "version control",
    "database design",
    "database management",
    "object oriented programming",
    "problem solving",
    "debugging",
    "code review",
    "agile development",
    "software engineering",
    "backend engineering",
    "web application development",
    "application development",
    "application programming",
    "database integration",
    "cloud deployment",
    "application deployment",
    "authentication",
    "authorization",
    "secure api",
    "scalable applications",
    "performance optimization",
    "microservices architecture",
)


# ============================================================
# Important ATS phrases
# ============================================================

IMPORTANT_PHRASES = [
    # NOTE: Education-related phrases (bachelor's degree, master's
    # degree, computer science, information technology, computer
    # applications, etc.) are intentionally NOT included here.
    # Education requirements are already scored by
    # _calculate_education_score() using EDUCATION_LEVELS and
    # EDUCATION_FIELD_GROUPS, which understand hierarchy (a
    # master's satisfies a bachelor's requirement) and field
    # equivalence (BCA satisfies "computer applications", etc.).
    # Treating these as plain literal keyword-match phrases here
    # would double-count education and could contradict
    # education_score when a resume satisfies the requirement
    # via an abbreviation or synonym the literal phrase match
    # doesn't recognize (e.g. "B.Tech" not containing the exact
    # substring "bachelor's degree").

    # Development
    "software engineering",
    "software development",
    "web development",
    "backend development",
    "backend developer",
    "frontend development",
    "frontend developer",
    "full stack",
    "full stack development",
    "full stack developer",

    # APIs
    "rest api",
    "rest apis",
    "restful api",
    "restful apis",
    "api development",

    # Data / AI
    "machine learning",
    "artificial intelligence",
    "data analysis",
    "data analytics",

    # Programming concepts
    "problem solving",
    "problem-solving",
    "object oriented programming",
    "object-oriented programming",

    # Databases
    "database management",
    "relational database",

    # Software engineering
    "software development lifecycle",
    "version control",
    "unit testing",
    "test automation",

    # Cloud / DevOps
    "cloud computing",
    "continuous integration",
    "continuous deployment",

    # Methodologies
    "agile methodology",
    "agile development",
]


IMPORTANT_PHRASE_ALIASES: dict[str, str] = {
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "api development": "api development",
    "api integration": "api integration",
    "source control": "version control",
    "automated testing": "unit testing",
    "integration testing": "integration testing",
    "sql queries": "sql queries",
    "web services": "web services",
    "backend services": "backend services",
    "object oriented programming": "object oriented programming",
    "object oriented design": "object oriented design",
}


# ============================================================
# Keyword phrase variants
# ============================================================
#
# These are controlled linguistic variants of known ATS phrases.
#
# We deliberately do NOT generate arbitrary n-grams.
# Each variant maps to one canonical ATS keyword.
#
# Examples:
#
#   relational databases
#       -> relational database
#
#   deploy applications
#   deploying applications
#       -> application deployment
#
# This keeps keyword extraction explainable and prevents generic
# phrase explosion.
# ============================================================

KEYWORD_PHRASE_VARIANTS: dict[str, str] = {

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    "relational database": "relational database",
    "relational databases": "relational database",

    "database management": "database management",
    "database management systems": "database management",

    "database integration": "database integration",

    # --------------------------------------------------------
    # Application deployment
    # --------------------------------------------------------

    "application deployment": "application deployment",

    "deploy application": "application deployment",
    "deploy applications": "application deployment",

    "deploying application": "application deployment",
    "deploying applications": "application deployment",

    "deployed application": "application deployment",
    "deployed applications": "application deployment",

    # --------------------------------------------------------
    # Cloud deployment
    # --------------------------------------------------------

    "cloud deployment": "cloud deployment",

    "deploy to cloud": "cloud deployment",
    "deploying to cloud": "cloud deployment",

    "cloud deployments": "cloud deployment",

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    "api development": "api development",
    "api developments": "api development",

    "api integration": "api integration",

    # --------------------------------------------------------
    # Software development
    # --------------------------------------------------------

    "software development": "software development",
    "software developments": "software development",

    "web development": "web development",
    "web developments": "web development",

    "backend development": "backend development",

    # --------------------------------------------------------
    # Testing
    # --------------------------------------------------------

    "unit testing": "unit testing",
    "automated testing": "automated testing",
    "integration testing": "integration testing",

    # --------------------------------------------------------
    # Engineering concepts
    # --------------------------------------------------------

    "problem solving": "problem solving",
    "problem-solving": "problem solving",

    "object oriented programming": (
        "object oriented programming"
    ),

    "object-oriented programming": (
        "object oriented programming"
    ),

    # --------------------------------------------------------
    # Performance / architecture
    # --------------------------------------------------------

    "performance optimization": (
        "performance optimization"
    ),

    "microservices architecture": (
        "microservices architecture"
    ),

    # --------------------------------------------------------
    # Security
    # --------------------------------------------------------

    "secure api": "secure api",
    "secure apis": "secure api",
}

EDUCATION_KEYWORDS = {
    "phd",
    "doctorate",
    "doctoral",
    "master",
    "masters",
    "master's",
    "master degree",
    "master's degree",
    "masters degree",
    "mtech",
    "m.tech",
    "mca",
    "msc",
    "m.sc",
    "mba",
    "m.com",
    "mcom",
    "bachelor",
    "bachelors",
    "bachelor's",
    "bachelor degree",
    "bachelor's degree",
    "bachelors degree",
    "btech",
    "b.tech",
    "bsc",
    "b.sc",
    "bca",
    "b.com",
    "bcom",
    "diploma",
    "associate",
    "computer applications",
    "computer application",
    "computer science",
    "information technology",
}


# ============================================================
# Generic normalization
# ============================================================

def _normalize(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        value = " ".join(str(item) for item in value)

    return " ".join(
        str(value)
        .lower()
        .strip()
        .split()
    )


def _normalize_for_matching(value: Any) -> str:
    text = _normalize(value)

    if not text:
        return ""

    replacements = {
        "’": "'",
        "–": "-",
        "—": "-",

        # Normalize common skill separators.
        "-": " ",
        "_": " ",
        "/": " ",
        "\\": " ",
        ".": " ",

        "|": " ",
        ",": " ",
        ";": " ",
        ":": " ",
        "!": " ",
        "?": " ",
        "(": " ",
        ")": " ",
        "[": " ",
        "]": " ",
        "{": " ",
        "}": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


def _normalize_list(values: Any) -> list[str]:
    if values is None:
        return []

    if isinstance(values, str):
        values = [values]

    if not isinstance(values, (list, tuple, set)):
        return []

    result: list[str] = []

    for value in values:
        normalized = _normalize(value)

        if normalized:
            result.append(normalized)

    return result


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def _score(value: Decimal | float | int) -> Decimal:
    decimal_value = Decimal(str(value))

    if decimal_value < SCORE_MIN:
        decimal_value = SCORE_MIN

    if decimal_value > SCORE_MAX:
        decimal_value = SCORE_MAX

    return decimal_value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# Boundary-aware matching
# ============================================================

def _contains_term(text: str, term: str) -> bool:
    text = _normalize(text)
    term = _normalize(term)

    if not text or not term:
        return False

    escaped = re.escape(term)

    pattern = (
        rf"(?<![a-z0-9+#])"
        rf"{escaped}"
        rf"(?![a-z0-9+#])"
    )

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None

def _contains_keyword_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Determine whether a controlled ATS phrase or one of its
    explicitly configured variants occurs in text.

    Matching is intentionally controlled:
        - no fuzzy matching
        - no arbitrary n-grams
        - no unrestricted stemming

    The phrase must either be present directly or have an
    explicitly configured variant in KEYWORD_PHRASE_VARIANTS.
    """

    normalized_text = _normalize_for_matching(
        text
    )

    normalized_phrase = _normalize_for_matching(
        phrase
    )

    if not normalized_text or not normalized_phrase:
        return False

    # --------------------------------------------------------
    # Direct match
    # --------------------------------------------------------

    if _contains_normalized_term(
        normalized_text,
        normalized_phrase,
    ):
        return True

    # --------------------------------------------------------
    # Explicit configured variants
    # --------------------------------------------------------

    for variant, canonical in (
        KEYWORD_PHRASE_VARIANTS.items()
    ):

        normalized_canonical = (
            _normalize_for_matching(canonical)
        )

        if normalized_canonical != normalized_phrase:
            continue

        normalized_variant = (
            _normalize_for_matching(variant)
        )

        if _contains_normalized_term(
            normalized_text,
            normalized_variant,
        ):
            return True

    return False


def _contains_normalized_term(
    text: str,
    term: str,
) -> bool:
    normalized_text = _normalize_for_matching(text)
    normalized_term = _normalize_for_matching(term)

    if not normalized_text or not normalized_term:
        return False

    def _matches(candidate: str) -> bool:
        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(candidate)}"
            rf"(?![a-z0-9])"
        )

        return re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE,
        ) is not None

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if _matches(normalized_term):
        return True

    words = normalized_term.split()

    if not words:
        return False

    last_word = words[-1]

    candidates = set()

    # --------------------------------------------------------
    # Plural -> singular
    # --------------------------------------------------------

    if last_word.endswith("ies") and len(last_word) > 3:
        singular = last_word[:-3] + "y"

    elif last_word.endswith("ses") and len(last_word) > 3:
        # databases -> database
        # diagnoses -> diagnosis
        if last_word.endswith("ases"):
            singular = last_word[:-1]
        else:
            singular = last_word[:-2]

    elif (
        last_word.endswith("s")
        and not last_word.endswith("ss")
    ):
        singular = last_word[:-1]

    else:
        singular = None

    if singular:
        candidates.add(
            " ".join(words[:-1] + [singular])
        )

    # --------------------------------------------------------
    # Singular -> plural
    # --------------------------------------------------------

    if last_word.endswith("y") and len(last_word) > 1:
        plural = last_word[:-1] + "ies"

    elif last_word.endswith(
        ("s", "x", "z", "ch", "sh")
    ):
        plural = last_word + "es"

    else:
        plural = last_word + "s"

    candidates.add(
        " ".join(words[:-1] + [plural])
    )

    # --------------------------------------------------------
    # Check normalized variants
    # --------------------------------------------------------

    return any(
        _matches(candidate)
        for candidate in candidates
    )

# ============================================================
# Generic flattening
# ============================================================

def _flatten_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, list):
        return " ".join(
            _flatten_value(item)
            for item in value
        )

    if isinstance(value, tuple):
        return " ".join(
            _flatten_value(item)
            for item in value
        )

    if isinstance(value, set):
        return " ".join(
            _flatten_value(item)
            for item in value
        )

    if isinstance(value, dict):
        return " ".join(
            _flatten_value(item)
            for item in value.values()
        )

    return str(value)


# ============================================================
# Resume parsed data
# ============================================================

def _get_parsed_data(
    resume: models.Resume,
) -> dict[str, Any]:

    parsing_result = getattr(
        resume,
        "parsing_result",
        None,
    )

    if parsing_result is None:
        raise HTTPException(
            status_code=409,
            detail="Resume has not been parsed yet.",
        )

    raw_status = getattr(
        parsing_result,
        "status",
        "",
    )

    # Handle Enum columns safely (SQLAlchemy Enum members
    # may not stringify to their plain value via str()).
    status_value = getattr(raw_status, "value", raw_status)
    status = _normalize(status_value)

    if status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Resume parsing is not completed yet.",
        )

    parser_version = _normalize(
        getattr(
            parsing_result,
            "parser_version",
            "",
        )
    )

    if parser_version != _normalize(
        PARSER_VERSION_REQUIRED
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Resume was parsed with an unsupported "
                "parser version. "
                f"Required parser version: "
                f"{PARSER_VERSION_REQUIRED}."
            ),
        )

    parsed_data = getattr(
        parsing_result,
        "parsed_data",
        None,
    )

    if not parsed_data:
        raise HTTPException(
            status_code=409,
            detail="Parsed resume data is not available.",
        )

    if not isinstance(parsed_data, dict):
        raise HTTPException(
            status_code=500,
            detail="Resume parsed data has an invalid format.",
        )

    return parsed_data


def _resume_text(
    resume: models.Resume,
    parsed_data: dict[str, Any],
) -> str:

    parsing_result = getattr(
        resume,
        "parsing_result",
        None,
    )

    extracted_text = ""

    if parsing_result is not None:
        extracted_text = getattr(
            parsing_result,
            "extracted_text",
            "",
        )

    parsed_text = _flatten_value(
        parsed_data
    )

    return _normalize(
        f"{extracted_text} {parsed_text}"
    )

# ============================================================
# Skill canonicalization
# ============================================================

# Aliases that are too short/common to safely search across
# unrestricted resume/job text.
#
# They are still accepted when they come from explicitly
# structured skill fields.
_UNSAFE_TEXT_SKILL_ALIASES = {
    "c",
    "ai",
    "js",
    "ts",
    "it",
    "api",
    "mongo",
}


# Small set of deliberate common technology misspellings.
#
# Do not turn this into unrestricted fuzzy matching because
# fuzzy matching can create incorrect ATS skill matches.
SKILL_ALIASES.update({
    "postgressql": "postgresql",
})


def _normalize_skill_for_lookup(
    value: Any,
) -> str:
    """
    Normalize a skill specifically for alias lookup.

    Examples:
        " Fast API "       -> "fast api"
        "Node-JS"          -> "node js"
        "Node_JS"          -> "node js"
        "POSTGRES"         -> "postgres"
        "Machine-Learning" -> "machine learning"
    """

    normalized = _normalize(value)

    if not normalized:
        return ""

    # Normalize curly apostrophes.
    normalized = normalized.replace(
        "’",
        "'",
    )

    # Normalize separators.
    #
    # These are formatting differences, not different skills:
    # node-js       -> node js
    # node_js       -> node js
    # machine-learning -> machine learning
    normalized = re.sub(
        r"[-_/]+",
        " ",
        normalized,
    )

    # Collapse repeated whitespace.
    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    return normalized

def _canonical_skill(value: str | None) -> str:
    if not value:
        return ""

    normalized = (
        value.lower()
        .strip()
        .replace("-", " ")
        .replace("_", " ")
    )

    normalized = " ".join(normalized.split())

    # Python
    if re.fullmatch(r"python(?:\s+v?\d+(?:\.\d+)*)?", normalized):
        return "python"

    # FastAPI
    if normalized in {
        "fastapi",
        "fast api",
    }:
        return "fastapi"

    # PostgreSQL
    if normalized in {
        "postgres",
        "postgresql",
        "postgres db",
        "postgres database",
        "postgresql db",
        "postgresql database",
    }:
        return "postgresql"

    # MongoDB
    if normalized in {
        "mongodb",
        "mongo db",
        "mongo database",
    }:
        return "mongodb"

    # REST API
    if normalized in {
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "rest api",
    }:
        return "rest api"

    # Node.js
    if normalized in {
        "node js",
        "nodejs",
        "node.js",
    }:
        return "node.js"

    # AWS
    if normalized in {
        "aws",
        "aws cloud",
        "amazon aws",
        "amazon web services",
        "amazon web services cloud",
    }:
        return "aws"

    return normalized


def _canonicalize_skill_set(
    values: Any,
) -> set[str]:
    """
    Convert arbitrary skill values into a canonical,
    deduplicated skill set.

    This is the single normalization path used by ATS
    skill matching.
    """

    if values is None:
        return set()

    if isinstance(values, str):
        values = [values]

    if not isinstance(
        values,
        (list, tuple, set),
    ):
        return set()

    result: set[str] = set()

    for value in values:
        canonical = _canonical_skill(
            value
        )

        if canonical:
            result.add(
                canonical
            )

    return result


def _skill_alias_matches_text(
    text: str,
    alias: str,
) -> bool:
    """
    Safely determine whether a skill alias occurs in text.

    Short/common aliases are excluded from unrestricted text
    scanning because they generate false positives.

    Structured skill fields are still allowed to contain
    these aliases.
    """

    normalized_alias = _normalize_skill_for_lookup(
        alias
    )

    if not normalized_alias:
        return False

    if normalized_alias in _UNSAFE_TEXT_SKILL_ALIASES:
        return False

    # Normalize formatting variations such as:
    #
    #   fast-api
    #   fast/api
    #   fast api
    #
    # into the same searchable representation.
    normalized_text = _normalize_for_matching(
        text
    )

    normalized_alias = _normalize_for_matching(
        normalized_alias
    )

    if not normalized_text or not normalized_alias:
        return False

    return _contains_normalized_term(
        normalized_text,
        normalized_alias,
    )


def _extract_known_skills_from_text(
    text: str,
) -> set[str]:
    """
    Detect known ATS skills from unrestricted text.

    Only aliases explicitly defined in SKILL_ALIASES are
    considered.

    Short/common aliases are excluded to reduce false
    positives.
    """

    if not text:
        return set()

    canonical: set[str] = set()

    aliases = sorted(
        SKILL_ALIASES.items(),
        key=lambda item: len(
            _normalize_skill_for_lookup(
                item[0]
            )
        ),
        reverse=True,
    )

    for alias, canonical_skill in aliases:

        if not _skill_alias_matches_text(
            text,
            alias,
        ):
            continue

        normalized_canonical = _canonical_skill(
            canonical_skill
        )

        if normalized_canonical:
            canonical.add(
                normalized_canonical
            )

    return canonical


def _extract_resume_skills(
    parsed_data: dict[str, Any],
    resume_text: str,
) -> set[str]:
    """
    Extract resume skills from:

    1. Explicit structured parser skill fields.
    2. Known technology names appearing in resume text.

    Both paths use the same canonical representation.
    """

    skills: list[str] = []

    possible_sections = [
        parsed_data.get("skills"),
        parsed_data.get("technical_skills"),
        parsed_data.get("technicalSkills"),
        parsed_data.get("skill"),
    ]

    for section in possible_sections:
        skills.extend(
            _normalize_list(section)
        )

    # --------------------------------------------------------
    # 1. Explicit parser skills
    # --------------------------------------------------------

    canonical = _canonicalize_skill_set(
        skills
    )

    # --------------------------------------------------------
    # 2. Known skills from resume text
    # --------------------------------------------------------

    canonical.update(
        _extract_known_skills_from_text(
            resume_text
        )
    )

    return canonical


def _extract_job_skills(
    job: models.Job,
    job_text: str,
) -> set[str]:
    """
    Extract job-required skills from:

    1. Structured Job.skills data.
    2. Known technology names found in the complete job text.

    Both paths use the same canonical representation.
    """

    skills: list[str] = []

    job_skills = getattr(
        job,
        "skills",
        None,
    )

    if isinstance(
        job_skills,
        (list, tuple, set),
    ):
        skills.extend(
            str(value)
            for value in job_skills
        )

    elif isinstance(
        job_skills,
        dict,
    ):
        for value in job_skills.values():

            if isinstance(
                value,
                (list, tuple, set),
            ):
                skills.extend(
                    str(item)
                    for item in value
                )

            else:
                skills.append(
                    str(value)
                )

    elif isinstance(
        job_skills,
        str,
    ):
        skills.append(
            job_skills
        )

    # --------------------------------------------------------
    # 1. Explicit structured job skills
    # --------------------------------------------------------

    canonical = _canonicalize_skill_set(
        skills
    )

    # --------------------------------------------------------
    # 2. Known skills from job text
    # --------------------------------------------------------

    canonical.update(
        _canonicalize_skill_set(
            _extract_known_skills_from_text(
                job_text
            )
        )
    )

    return canonical

def _calculate_skill_score(
    resume_skills,
    job_skills,
) -> tuple[
    Decimal,
    list[str],
    list[str],
]:
    """
    Calculate ATS skill compatibility.

    Production rules:

    1. Resume and job skills are canonicalized before comparison.
    2. Skill aliases collapse into one canonical skill.
    3. Duplicate aliases cannot inflate the denominator.
    4. Matching is performed only on canonical skills.
    5. Output lists contain canonical skill names only.
    """

    technical_skills = _technical_canonical_skills()

    # ========================================================
    # 1. Canonicalize resume skills
    # ========================================================

    canonical_resume_skills: set[str] = set()

    for skill in resume_skills or []:

        cleaned = _clean_keyword(skill)

        if not cleaned:
            continue

        canonical = _canonical_skill(cleaned)

        if not canonical:
            continue

        if canonical in technical_skills:
            canonical_resume_skills.add(canonical)
            continue

        # Keep non-technical skills only when they are
        # recognized by the existing skill canonicalization.
        canonical_resume_skills.add(canonical)

    # ========================================================
    # 2. Canonicalize job skills
    # ========================================================

    canonical_job_skills: set[str] = set()

    for skill in job_skills or []:

        cleaned = _clean_keyword(skill)

        if not cleaned:
            continue

        canonical = _canonical_skill(cleaned)

        if not canonical:
            continue

        canonical_job_skills.add(canonical)

    # ========================================================
    # 3. No job skills
    # ========================================================

    if not canonical_job_skills:
        return (
            Decimal("100.00"),
            [],
            [],
        )

    # ========================================================
    # 4. Compare canonical skills
    # ========================================================

    matched_skills = sorted(
        canonical_resume_skills
        & canonical_job_skills
    )

    missing_skills = sorted(
        canonical_job_skills
        - canonical_resume_skills
    )

    # ========================================================
    # 5. Calculate score
    # ========================================================

    total = len(canonical_job_skills)

    score = (
        Decimal(len(matched_skills))
        / Decimal(total)
        * Decimal("100")
    )

    matched_skills = _unique_preserve_order(
        [
            _canonical_skill(skill)
            for skill in matched_skills
            if skill
        ]
    )

    missing_skills = _unique_preserve_order(
        [
            _canonical_skill(skill)
            for skill in missing_skills
            if skill
        ]
    )

    return (
        _score(score),
        matched_skills,
        missing_skills,
    )



# ============================================================
# Keyword cleaning
# ============================================================
def _clean_keyword(value: str) -> str:
    value = _normalize(value)

    if not value:
        return ""

    value = value.replace(
        "’",
        "'",
    )

    # Remove punctuation which separates words.
    value = re.sub(
        r'[,:;!?()\[\]{}"“”]',
        " ",
        value,
    )

    # Preserve:
    # letters
    # numbers
    # #
    # +
    # .
    # -
    # apostrophe
    value = re.sub(
        r"[^a-z0-9+#.\-']+",
        " ",
        value,
    )

    # Remove trailing dots.
    value = re.sub(
        r"(?<=[a-z0-9])\.+$",
        "",
        value,
    )

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def _keyword_is_meaningful(
    keyword: str,
) -> bool:
    """
    Determine whether an ordinary ATS keyword carries enough
    information to be useful for keyword scoring.

    Generic nouns such as:

        services
        databases
        applications
        systems
        experience

    are intentionally excluded.

    Multi-word role/domain phrases remain eligible when they
    contain meaningful information.
    """

    if not keyword:
        return False

    normalized = _normalize_for_matching(
        keyword
    )

    if not normalized:
        return False

    # --------------------------------------------------------
    # Exact generic keyword rejection
    # --------------------------------------------------------

    if normalized in GENERIC_ATS_KEYWORDS:
        return False

    # --------------------------------------------------------
    # Normalize simple plural forms for generic detection
    # --------------------------------------------------------

    words = normalized.split()

    if len(words) == 1:
        word = words[0]

        singular_candidates = {
            word[:-3] if word.endswith("ies") else "",
            word[:-2] if word.endswith("es") else "",
            word[:-1] if word.endswith("s") else "",
        }

        for singular in singular_candidates:

            if (
                singular
                and singular in GENERIC_ATS_KEYWORDS
            ):
                return False

    # --------------------------------------------------------
    # Reject extremely short ordinary words
    # --------------------------------------------------------

    if len(words) == 1 and len(words[0]) < 3:
        return False

    return True

# ============================================================
# ATS keyword extraction
# ============================================================

def _technical_canonical_skills() -> set[str]:
    """
    Return all canonical technical skills configured in
    SKILL_ALIASES.
    """
    return {
        canonical
        for canonical in (
            _canonical_skill(skill)
            for skill in SKILL_ALIASES.values()
        )
        if canonical
    }


def _skill_aliases_for_canonical(
    canonical_skill: str,
) -> list[str]:
    """
    Return all configured aliases belonging to one canonical
    technical skill.
    """
    canonical = _canonical_skill(canonical_skill)

    if not canonical:
        return []

    aliases: list[str] = []

    for alias, configured_canonical in SKILL_ALIASES.items():
        if _canonical_skill(configured_canonical) == canonical:
            aliases.append(alias)

    return aliases


def _keyword_alias_lookup(
    value: str,
) -> str:
    """
    Apply keyword aliases after normalizing formatting variants.

    Examples:
        problem-solving
            -> problem solving

        restful api
            -> rest api

        relational databases
            -> relational database

        cloud deployments
            -> cloud deployment
    """

    cleaned = _clean_keyword(value)

    if not cleaned:
        return ""

    # --------------------------------------------------------
    # 1. Direct ordinary keyword alias
    # --------------------------------------------------------

    direct = KEYWORD_ALIASES.get(cleaned)

    if direct:
        return _clean_keyword(direct)

    # --------------------------------------------------------
    # 2. Normalized ordinary keyword alias
    # --------------------------------------------------------

    normalized = _normalize_for_matching(cleaned)

    for alias, canonical in KEYWORD_ALIASES.items():
        if _normalize_for_matching(alias) == normalized:
            return _clean_keyword(canonical)

    # --------------------------------------------------------
    # 3. Controlled phrase variant
    # --------------------------------------------------------

    for variant, canonical in KEYWORD_PHRASE_VARIANTS.items():
        if _normalize_for_matching(variant) == normalized:
            return _clean_keyword(canonical)

    return cleaned


def _keyword_is_technical_skill(
    keyword: str,
) -> bool:
    """
    Determine whether a keyword represents a configured
    technical skill.
    """
    canonical = _canonical_skill(keyword)

    if not canonical:
        return False

    return canonical in _technical_canonical_skills()

def _extract_configured_phrases(
    text: str,
) -> list[str]:
    """
    Extract explicitly configured multi-word ATS phrases.

    Matching supports explicitly configured linguistic variants
    while keeping the vocabulary controlled.
    """

    if not text:
        return []

    candidates: list[str] = []

    for phrase in IMPORTANT_PHRASES:

        cleaned = _keyword_alias_lookup(
            phrase
        )

        if not cleaned:
            continue

        if not _contains_keyword_phrase(
            text,
            cleaned,
        ):
            continue

        if not _keyword_is_meaningful(
            cleaned
        ):
            continue

        candidates.append(
            cleaned
        )

    return _unique_preserve_order(
        candidates
    )


def _extract_job_skill_keywords(
    text: str,
) -> list[str]:
    """
    Extract configured technical skills from job text.

    Matching is alias-aware and uses the same canonical
    representation as resume skill extraction.
    """
    if not text:
        return []

    candidates: list[str] = []

    aliases = sorted(
        SKILL_ALIASES.items(),
        key=lambda item: len(
            _normalize_skill_for_lookup(item[0])
        ),
        reverse=True,
    )

    for alias, canonical_skill in aliases:
        if not _skill_alias_matches_text(
            text,
            alias,
        ):
            continue

        canonical = _canonical_skill(
            canonical_skill
        )

        if not canonical:
            continue

        candidates.append(canonical)

    return candidates


# NOTE: This module deliberately does not generate arbitrary
# single-word or two-word n-grams from free-form job text (an
# earlier version of this file had _extract_role_specific_terms /
# _extract_role_specific_phrases helpers for that, but they were
# never wired into _extract_keyword_candidates and have been
# removed). Arbitrary n-grams produce noisy, unexplainable
# "missing keyword" advice (e.g. "applications computer",
# "candidate should"). The controlled vocabulary below
# (structured Job.skills + SKILL_ALIASES + IMPORTANT_PHRASES) is
# the intended keyword source. Extend IMPORTANT_PHRASES or
# SKILL_ALIASES instead of re-introducing free n-gram extraction.


def _remove_redundant_keywords(
    keywords: list[str],
) -> list[str]:
    """
    Remove an ordinary keyword when it is fully contained in a
    longer ordinary keyword.

    Example:
        software development
        software development lifecycle

    keeps only:
        software development lifecycle

    Technical skills are never removed this way because:
        api
        rest api
    are distinct ATS skills.
    """
    unique = _unique_preserve_order(keywords)

    technical_skills = _technical_canonical_skills()
    result: list[str] = []

    for keyword in unique:
        if keyword in technical_skills:
            result.append(keyword)
            continue

        keyword_words = keyword.split()
        redundant = False

        for other in unique:
            if keyword == other:
                continue

            if other in technical_skills:
                continue

            other_words = other.split()

            if len(other_words) <= len(keyword_words):
                continue

            if _contains_normalized_term(other, keyword):
                redundant = True
                break

        if not redundant:
            result.append(keyword)

    return result


def _extract_keyword_candidates(
    job_text: str,
    job_skills: set[str] | None = None,
) -> list[str]:
    """
    Extract meaningful ATS keyword candidates from job content.

    Sources:
        1. Structured Job.skills
        2. IMPORTANT_PHRASES
        3. Controlled ATS phrases
        4. High-signal standalone ATS terms

    Technical skills remain part of skill_score and are removed
    from ordinary keyword scoring later.

    Arbitrary n-grams are intentionally not generated.
    """

    if not job_text:
        return []

    text = _normalize(job_text)

    if not text:
        return []

    candidates: list[str] = []

    # ============================================================
    # 1. STRUCTURED JOB.SKILLS
    # ============================================================

    if job_skills:
        for skill in job_skills:
            cleaned = _clean_keyword(skill)

            if not cleaned:
                continue

            # Structured technical skills belong exclusively
            # to skill_score, never ordinary keyword_score.
            if _canonical_skill(cleaned) in _technical_canonical_skills():
                continue

            candidates.append(cleaned)

    # ============================================================
    # 2. IMPORTANT CONFIGURED PHRASES
    # ============================================================

    for phrase in IMPORTANT_PHRASES:

        if not _contains_keyword_phrase(
            text,
            phrase,
        ):
            continue

        canonical = _keyword_alias_lookup(
            phrase
        )

        if not canonical:
            continue

        if not _keyword_is_meaningful(
            canonical
        ):
            continue

        candidates.append(
            canonical
        )

    # ============================================================
    # 3. CONTROLLED ATS PHRASES
    # ============================================================

    ats_phrases = (
        "backend developer",
        "backend development",
        "software development",
        "web development",
        "api development",
        "api integration",
        "rest api",
        "rest api development",
        "unit testing",
        "automated testing",
        "integration testing",
        "version control",
        "database design",
        "database management",
        "object oriented programming",
        "problem solving",
        "debugging",
        "code review",
        "agile development",
        "software engineering",
        "backend engineering",
        "web application development",
        "application development",
        "application programming",
        "database integration",
        "cloud deployment",
        "application deployment",
        "authentication",
        "authorization",
        "secure api",
        "scalable applications",
        "performance optimization",
        "microservices architecture",
    )

    for phrase in ATS_CONTROLLED_PHRASES:

        if not _contains_normalized_term(
            text,
            phrase,
        ):
            continue

        # Controlled ATS phrases are already canonical.
        canonical = _clean_keyword(
            phrase
        )

        if not canonical:
            continue

        if not _keyword_is_meaningful(
            canonical
        ):
            continue

        candidates.append(
            canonical
    )
    # ============================================================
    # 4. HIGH-SIGNAL STANDALONE ATS TERMS
    # ============================================================

    words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9+#./-]*",
        text,
    )

    for word in words:

        cleaned = _clean_keyword(
            word
        )

        if not cleaned:
            continue

        canonical_skill = _canonical_skill(
            cleaned
        )

        # Technical skills are handled by skill_score.
        if (
            canonical_skill
            in _technical_canonical_skills()
        ):
            continue

        canonical_keyword = (
            _keyword_alias_lookup(
                cleaned
            )
        )

        if not canonical_keyword:
            continue

        if (
            canonical_keyword
            not in ATS_STANDALONE_KEYWORDS
        ):
            continue

        if not _keyword_is_meaningful(
            canonical_keyword
        ):
            continue

        candidates.append(
            canonical_keyword
        )

    # ============================================================
    # 5. FINAL CANONICALIZATION
    # ============================================================

    normalized_candidates: list[str] = []

    for keyword in candidates:

        cleaned = _clean_keyword(keyword)

        if not cleaned:
            continue

        # --------------------------------------------------------
        # Technical skill canonicalization
        # --------------------------------------------------------

        canonical_skill = _canonical_skill(
            cleaned
        )

        if canonical_skill in _technical_canonical_skills():
            continue

        # --------------------------------------------------------
        # Ordinary keyword alias canonicalization
        # --------------------------------------------------------

        canonical_keyword = _keyword_alias_lookup(
            cleaned
        )

        if not canonical_keyword:
            continue

        # --------------------------------------------------------
        # A keyword alias may itself resolve to a technical skill.
        # Never allow it into keyword_score.
        # --------------------------------------------------------

        canonical_alias_skill = _canonical_skill(
            canonical_keyword
        )

        if canonical_alias_skill in _technical_canonical_skills():
            continue

        # --------------------------------------------------------
        # Meaningfulness filter
        # --------------------------------------------------------

        if not _keyword_is_meaningful(
            canonical_keyword
        ):
            continue

        normalized_candidates.append(
            canonical_keyword
        )

    # ============================================================
    # 6. REMOVE DUPLICATES
    # ============================================================

    normalized_candidates = (
        _unique_preserve_order(
            normalized_candidates
        )
    )

    # ============================================================
    # 7. REMOVE REDUNDANT ORDINARY PHRASES
    # ============================================================

    normalized_candidates = (
        _remove_redundant_keywords(
            normalized_candidates
        )
    )

    return _unique_preserve_order(
        normalized_candidates
    )
# ============================================================
# Keyword scoring
# ============================================================

def _calculate_keyword_score(
    resume_text: str,
    job_text: str,
    job_skills: set[str],
) -> tuple[
    Decimal,
    list[str],
    list[str],
]:
    """
    Calculate ATS keyword coverage for meaningful non-skill terms.

    Structured Job.skills belong exclusively to skill_score.

    Technical skills detected from free-form job text also belong
    exclusively to skill_score.

    Ordinary ATS phrases are scored here.

    Canonicalization happens before scoring so aliases cannot
    inflate the denominator.
    """

    candidates = _extract_keyword_candidates(
        job_text,
        job_skills=job_skills,
    )

    if not candidates:
        return (
            Decimal("100.00"),
            [],
            [],
        )

    technical_skills = _technical_canonical_skills()

    canonical_job_skills = {
        canonical
        for skill in job_skills
        if (
            canonical := _canonical_skill(skill)
        )
    }

    canonical_keywords: list[str] = []

    for keyword in candidates:

        cleaned = _clean_keyword(keyword)

        if not cleaned:
            continue

        # ----------------------------------------------------
        # Structured skill
        # ----------------------------------------------------

        canonical_skill = _canonical_skill(
            cleaned
        )

        if canonical_skill in canonical_job_skills:
            continue

        # ----------------------------------------------------
        # Technical skill from job text
        # ----------------------------------------------------

        if canonical_skill in technical_skills:
            continue

        # ----------------------------------------------------
        # Ordinary keyword
        # ----------------------------------------------------

        canonical_keyword = _keyword_alias_lookup(
            cleaned
        )

        if not canonical_keyword:
            continue

        canonical_alias_skill = _canonical_skill(
            canonical_keyword
        )

        if canonical_alias_skill in technical_skills:
            continue

        if not _keyword_is_meaningful(
            canonical_keyword
        ):
            continue

        canonical_keywords.append(
            canonical_keyword
        )

    canonical_keywords = _unique_preserve_order(
        canonical_keywords
    )

    if not canonical_keywords:
        return (
            Decimal("100.00"),
            [],
            [],
        )

    matched: list[str] = []
    missing: list[str] = []

    for keyword in canonical_keywords:

        if _contains_normalized_term(
            resume_text,
            keyword,
        ):
            matched.append(keyword)
        else:
            missing.append(keyword)

    total = len(canonical_keywords)

    score = (
        Decimal(len(matched))
        / Decimal(total)
        * Decimal("100")
    )

    return (
        _score(score),
        matched,
        missing,
    )

# ============================================================
# Education
# ============================================================

def _education_level(
    education_text: str,
) -> int | None:
    """
    Detect the highest explicitly stated education level.

    Levels:
        5 = PhD / Doctorate
        4 = Master's / M.Tech / MCA / M.Sc / MBA
        3 = Bachelor's / B.Tech / BCA / B.Sc / B.Com
        2 = Diploma / Associate
        1 = Intermediate / 12th / Higher Secondary
    """

    text = _normalize_for_matching(education_text)

    if not text:
        return None

    detected_levels: list[int] = []

    for degree, level in EDUCATION_LEVELS.items():
        if _contains_normalized_term(text, degree):
            detected_levels.append(level)

    if not detected_levels:
        return None

    return max(detected_levels)


def _extract_resume_education(
    parsed_data: dict[str, Any],
    resume_text: str,
) -> str:
    """
    Extract education from structured parser output.

    Structured education is preferred because it prevents unrelated
    resume content from influencing education scoring.

    If structured education is unavailable, attempt to extract only
    the education section from the raw resume text.

    The complete resume is NEVER used as the education fallback.
    """

    sections = [
        parsed_data.get("education"),
        parsed_data.get("educations"),
        parsed_data.get("academic_background"),
        parsed_data.get("academicBackground"),
        parsed_data.get("qualifications"),
        parsed_data.get("qualification"),
    ]

    values = [
        _flatten_value(section)
        for section in sections
        if section
    ]

    education_text = _normalize(
        " ".join(values)
    )

    if education_text:
        return education_text

    # --------------------------------------------------------
    # Raw-text fallback
    # --------------------------------------------------------

    if not resume_text:
        return ""

    normalized_text = _normalize(resume_text)

    # Only extract a likely education section.
    section_pattern = re.compile(
        r"\b(?:education|academic background|"
        r"educational qualifications|qualifications)\b"
        r"(.*?)(?="
        r"\b(?:experience|work experience|"
        r"professional experience|projects|"
        r"skills|technical skills|certifications|"
        r"languages|achievements|interests)\b"
        r"|$)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    match = section_pattern.search(
        normalized_text
    )

    if not match:
        return ""

    return _normalize(
        match.group(1)
    )


# ============================================================
# Education requirement detection
# ============================================================

_MANDATORY_MARKERS: tuple[str, ...] = (
    "required",
    "requirement",
    "must have",
    "must hold",
    "minimum",
    "mandatory",
    "essential",
)

_PREFERRED_MARKERS: tuple[str, ...] = (
    "preferred",
    "preference",
    "prefer",
    "desired",
    "desirable",
    "nice to have",
    "is a plus",
    "a plus",
    "bonus",
    "optional",
    "advantageous",
)

_DEGREE_TERM_GROUPS: tuple[
    tuple[int, tuple[str, ...]]
] = (
    (
        5,
        (
            "phd",
            "ph d",
            "ph.d",
            "doctorate",
            "doctoral",
        ),
    ),
    (
        4,
        (
            "master's degree",
            "masters degree",
            "master degree",
            "master's",
            "masters",
            "master",
            "mtech",
            "m.tech",
            "m tech",
            "mca",
            "msc",
            "m.sc",
            "m sc",
            "mba",
            "m.com",
            "m com",
            "mcom",
        ),
    ),
    (
        3,
        (
            "bachelor's degree",
            "bachelors degree",
            "bachelor degree",
            "bachelor's",
            "bachelors",
            "bachelor",
            "btech",
            "b.tech",
            "b tech",
            "bca",
            "bsc",
            "b.sc",
            "b sc",
            "b.com",
            "b com",
            "bcom",
        ),
    ),
    (
        2,
        (
            "diploma",
            "associate degree",
            "associate",
        ),
    ),
    (
        1,
        (
            "intermediate",
            "12th",
            "higher secondary",
        ),
    ),
)

_QUALIFIER_WINDOW = 60


def _nearest_marker_distance(
    text: str,
    span_start: int,
    span_end: int,
    markers: tuple[str, ...],
    window: int = _QUALIFIER_WINDOW,
) -> int | None:
    """
    Find the nearest qualifier marker to a degree occurrence.

    Only text inside the configured local window is considered.
    """

    window_start = max(
        0,
        span_start - window,
    )

    window_end = min(
        len(text),
        span_end + window,
    )

    local_text = text[
        window_start:window_end
    ]

    local_span_start = (
        span_start - window_start
    )

    local_span_end = (
        span_end - window_start
    )

    best_distance: int | None = None

    for marker in markers:
        for match in re.finditer(
            re.escape(marker),
            local_text,
            flags=re.IGNORECASE,
        ):
            if match.end() <= local_span_start:
                distance = (
                    local_span_start
                    - match.end()
                )

            elif match.start() >= local_span_end:
                distance = (
                    match.start()
                    - local_span_end
                )

            else:
                distance = 0

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance

    return best_distance


def _degree_matches(
    clause_text: str,
    term: str,
) -> list[re.Match]:
    """
    Match degree aliases despite formatting variations.

    Examples:

        B.Tech
        B Tech
        BTech
        B-Tech
        B/Tech

    are treated as the same degree.
    """

    normalized_term = _normalize_for_matching(
        term
    )

    compact_term = re.sub(
        r"[^a-z0-9]+",
        "",
        normalized_term,
    )

    if not compact_term:
        return []

    flexible_term = "".join(
        rf"{re.escape(char)}[\s./_-]*"
        for char in compact_term
    )

    pattern = (
        rf"(?<![a-z0-9])"
        rf"{flexible_term}"
        rf"(?![a-z0-9])"
    )

    return list(
        re.finditer(
            pattern,
            clause_text,
            flags=re.IGNORECASE,
        )
    )

def _select_degree_requirement(
    levels: list[int],
    clause_text: str,
) -> int:
    """
    Resolve multiple degree levels within one requirement clause.

    The caller should pass only degrees belonging to the same
    requirement classification.

    OR:
        Bachelor's or Master's -> lower level is sufficient.

    AND:
        Bachelor's and Master's -> higher level is required.

    If no connector is present, the highest level is used.
    """

    if not levels:
        raise ValueError(
            "levels must not be empty"
        )

    unique_levels = sorted(
        set(levels)
    )

    if len(unique_levels) == 1:
        return unique_levels[0]

    if re.search(
        r"\bor\b",
        clause_text,
        flags=re.IGNORECASE,
    ):
        return min(unique_levels)

    return max(unique_levels)


def _classify_degree_requirement(
    clause_text: str,
    level: int,
    start: int,
    end: int,
) -> str:
    """
    Classify one degree occurrence.

    Returns:

        "mandatory"
        "preferred"
        "unqualified"

    The nearest qualifier wins.

    A preferred qualifier closer to the degree prevents a more
    distant mandatory marker from incorrectly making the degree
    mandatory.
    """

    mandatory_distance = _nearest_marker_distance(
        clause_text,
        start,
        end,
        _MANDATORY_MARKERS,
    )

    preferred_distance = _nearest_marker_distance(
        clause_text,
        start,
        end,
        _PREFERRED_MARKERS,
    )

    if (
        preferred_distance is not None
        and (
            mandatory_distance is None
            or preferred_distance < mandatory_distance
        )
    ):
        return "preferred"

    if mandatory_distance is not None:
        return "mandatory"

    return "unqualified"


def _required_education_level(
    job_text: str,
) -> int | None:
    """
    Detect the effective mandatory education level.

    Rules:

    1. Explicit mandatory requirements have highest priority.
    2. Preferred/desired requirements are never mandatory.
    3. Unqualified degree mentions are used only when no explicit
       mandatory requirement exists.
    4. OR means the lower qualification is sufficient.
    5. AND means the higher qualification is required.
    """

    raw_text = _normalize(job_text)

    if not raw_text:
        return None

    text = re.sub(
        r"\bb\s*(?:[./-]\s*)?tech\b",
        "btech",
        raw_text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bm\s*(?:[./-]\s*)?tech\b",
        "mtech",
        text,
        flags=re.IGNORECASE,
    )

    clauses = re.split(
        r"[,;\n.!?]+",
        text,
    )

    mandatory_levels: list[int] = []
    unqualified_levels: list[int] = []

    for raw_clause in clauses:

        clause_text = raw_clause.strip()

        if not clause_text:
            continue

        detected: list[
            tuple[int, int, int]
        ] = []

        for level, terms in _DEGREE_TERM_GROUPS:

            for term in terms:

                for match in _degree_matches(
                    clause_text,
                    term,
                ):
                    detected.append(
                        (
                            level,
                            match.start(),
                            match.end(),
                        )
                    )

        if not detected:
            continue

        # ----------------------------------------------------
        # Remove duplicate alias matches.
        # ----------------------------------------------------

        unique_detected: list[
            tuple[int, int, int]
        ] = []

        seen_spans: set[
            tuple[int, int]
        ] = set()

        for level, start, end in sorted(
            detected,
            key=lambda item: (
                item[1],
                item[2],
                -item[0],
            ),
        ):
            span_key = (start, end)

            if span_key in seen_spans:
                continue

            seen_spans.add(span_key)
            unique_detected.append(
                (
                    level,
                    start,
                    end,
                )
            )

        mandatory: list[int] = []
        unqualified: list[int] = []

        for level, start, end in unique_detected:

            classification = (
                _classify_degree_requirement(
                    clause_text,
                    level,
                    start,
                    end,
                )
            )

            if classification == "mandatory":
                mandatory.append(level)

            elif classification == "unqualified":
                unqualified.append(level)

        # ----------------------------------------------------
        # Explicit mandatory requirements win within clause.
        # ----------------------------------------------------

        if mandatory:
            mandatory_levels.append(
                _select_degree_requirement(
                    mandatory,
                    clause_text,
                )
            )

        # ----------------------------------------------------
        # Unqualified requirements are fallback only.
        # ----------------------------------------------------

        elif unqualified:
            unqualified_levels.append(
                _select_degree_requirement(
                    unqualified,
                    clause_text,
                )
            )

    if mandatory_levels:
        return max(mandatory_levels)

    if unqualified_levels:
        return max(unqualified_levels)

    return None


def _education_requirement_text(
    job_text: str,
) -> str:
    """
    Extract local clauses containing recognized education terms.
    """

    text = _normalize_for_matching(job_text)

    if not text:
        return ""

    fragments: list[str] = []

    clauses = re.split(
        r"[,;\n.!?]+",
        text,
    )

    for clause in clauses:

        clause = clause.strip()

        if not clause:
            continue

        contains_degree = False

        for _, terms in _DEGREE_TERM_GROUPS:

            if any(
                _degree_matches(
                    clause,
                    term,
                )
                for term in terms
            ):
                contains_degree = True
                break

        if contains_degree:
            fragments.append(clause)

    return _normalize(
        " ".join(
            _unique_preserve_order(
                fragments
            )
        )
    )

def _education_field_match(
    resume_education: str,
    job_text: str,
) -> bool:
    """
    Determine whether the candidate's education field satisfies
    the field associated with the effective education requirement.

    Field matching is limited to degree-related clauses.

    If no recognized education field is explicitly required,
    the field requirement is considered satisfied.
    """

    job_text = _normalize_for_matching(job_text)
    resume_education = _normalize_for_matching(
        resume_education
    )

    if not job_text or not resume_education:
        return False

    clauses = re.split(
        r"[,;\n.!?]+",
        job_text,
    )

    education_clauses: list[str] = []

    for clause in clauses:

        clause = clause.strip()

        if not clause:
            continue

        has_degree = any(
            _degree_matches(
                clause,
                term,
            )
            for _, terms in _DEGREE_TERM_GROUPS
            for term in terms
        )

        if has_degree:
            education_clauses.append(clause)

    # No degree-related requirement.
    if not education_clauses:
        return True

    recognized_field_required = False

    for clause in education_clauses:

        for group in EDUCATION_FIELD_GROUPS:

            job_has_field = any(
                _contains_normalized_term(
                    clause,
                    term,
                )
                for term in group
            )

            if not job_has_field:
                continue

            recognized_field_required = True

            resume_has_field = any(
                _contains_normalized_term(
                    resume_education,
                    term,
                )
                for term in group
            )

            if resume_has_field:
                return True

    # Degree exists, but no recognized field was specified.
    if not recognized_field_required:
        return True

    return False


def _calculate_education_score(
    parsed_data: dict[str, Any],
    resume_text: str,
    job_text: str,
) -> Decimal:
    """
    Calculate candidate education compatibility.

    Rules:

        Higher education satisfies a lower mandatory level.

        Required level + matching field:
            100

        Required level + different recognized field:
            60

        Required level not satisfied:
            0

        No mandatory education requirement:
            100
    """

    required_level = _required_education_level(
        job_text
    )

    if required_level is None:
        return Decimal("100.00")

    resume_education = _extract_resume_education(
        parsed_data,
        resume_text,
    )

    if not resume_education:
        return Decimal("0.00")

    resume_level = _education_level(
        resume_education
    )

    if resume_level is None:
        return Decimal("0.00")

    # Higher qualification satisfies lower qualification.
    if resume_level < required_level:
        return Decimal("0.00")

    if _education_field_match(
        resume_education,
        job_text,
    ):
        return Decimal("100.00")

    return Decimal("60.00")

# ============================================================
# Experience
# ============================================================

def _extract_experience_text(
    parsed_data: dict[str, Any],
) -> str:
    sections = [
        parsed_data.get("experience"),
        parsed_data.get("work_experience"),
        parsed_data.get("workExperience"),
        parsed_data.get("professional_experience"),
        parsed_data.get("employment"),
        parsed_data.get("employment_history"),
    ]

    values = [
        _flatten_value(section)
        for section in sections
        if section
    ]

    return _normalize(
        " ".join(values)
    )


def _extract_project_text(
    parsed_data: dict[str, Any],
) -> str:
    sections = [
        parsed_data.get("projects"),
        parsed_data.get("project"),
        parsed_data.get("academic_projects"),
        parsed_data.get("personal_projects"),
    ]

    values = [
        _flatten_value(section)
        for section in sections
        if section
    ]

    return _normalize(
        " ".join(values)
    )


def _extract_years_from_text(
    text: str,
) -> float | None:
    """
    Extract explicit professional experience durations.

    Supported:

        2 years
        2+ years
        2.5 years
        2 yrs
        2+ yrs

    Only structured experience text should be supplied.

    Employment dates are intentionally not converted into years
    because doing so reliably requires date-range reasoning and
    overlap handling.
    """

    if not text:
        return None

    text = _normalize(text)

    pattern = (
        r"\b"
        r"(\d+(?:\.\d+)?)"
        r"\s*\+?\s*"
        r"(?:years?|yrs?)"
        r"\b"
        r"(?:"
            r"\s+of\s+"
            r"(?:professional\s+|relevant\s+)?"
            r"experience\b"
            r"|"
            r"\s+experience\b"
        r")?"
    )

    values: list[float] = []

    for match in re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    ):
        try:
            value = float(
                match.group(1)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if value >= 0:
            values.append(value)

    if not values:
        return None

    return max(values)


def _extract_clause_around_match(
    text: str,
    start: int,
    end: int,
) -> str:
    """
    Extract the punctuation-delimited clause surrounding a match.
    """

    left_candidates = [
        text.rfind(",", 0, start),
        text.rfind(";", 0, start),
        text.rfind(".", 0, start),
        text.rfind("\n", 0, start),
    ]

    left_boundary = max(
        left_candidates
    )

    right_candidates = [
        position
        for position in (
            text.find(",", end),
            text.find(";", end),
            text.find(".", end),
            text.find("\n", end),
        )
        if position != -1
    ]

    right_boundary = (
        min(right_candidates)
        if right_candidates
        else len(text)
    )

    return text[
        left_boundary + 1:
        right_boundary
    ].strip()

def _experience_requirement_clause(
    text: str,
    start: int,
    end: int,
) -> str:
    """
    Extract the punctuation-delimited clause containing an
    experience requirement.
    """

    return _extract_clause_around_match(
        text,
        start,
        end,
    )

def _experience_requirement_is_preferred(
    text: str,
    start: int,
    end: int,
) -> bool:
    """
    Determine whether an experience requirement is preferred
    rather than mandatory.

    Qualifiers are evaluated inside the same punctuation-delimited
    clause as the experience requirement.
    """

    clause = _experience_requirement_clause(
        text,
        start,
        end,
    )

    if not clause:
        return False

    local_start = clause.lower().find(
        text[start:end].lower()
    )

    if local_start == -1:
        return False

    local_end = (
        local_start
        + (end - start)
    )

    mandatory_distance = _nearest_marker_distance(
        clause,
        local_start,
        local_end,
        _MANDATORY_MARKERS,
        window=_QUALIFIER_WINDOW,
    )

    preferred_distance = _nearest_marker_distance(
        clause,
        local_start,
        local_end,
        _PREFERRED_MARKERS,
        window=_QUALIFIER_WINDOW,
    )

    if (
        preferred_distance is not None
        and (
            mandatory_distance is None
            or preferred_distance < mandatory_distance
        )
    ):
        return True

    return False


def _required_experience_years(
    job_text: str,
) -> float | None:
    """
    Detect explicit experience requirements.

    Supported:

        2 years of experience required
        2+ years experience
        minimum 3 years
        at least 4 years
        5 years required
        5 years mandatory
        5 years essential

    Preferred-only requirements are ignored.

    Examples ignored:

        5 years preferred
        5 years desired
        minimum 5 years preferred
        3 years of experience desirable
    """

    text = _normalize(job_text)

    if not text:
        return None


    values: list[float] = []

    non_mandatory_pattern = re.compile(
        r"""
        (?:
            minimum\s+
            |
            at\s+least\s+
        )?
        \d+(?:\.\d+)?
        \+?
        \s*
        (?:years?|yrs?)
        \b
        .*?
        \b
        (?:preferred|desired|desirable|optional|advantageous)
        \b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    if non_mandatory_pattern.search(text):
        return None

    # --------------------------------------------------------
    # 1. X years of experience
    # --------------------------------------------------------

    experience_pattern = re.compile(
        r"\b"
        r"(\d+(?:\.\d+)?)"
        r"\s*\+?\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+of)?\s+"
        r"(?:(?:relevant|professional)\s+)?"
        r"experience\b",
        flags=re.IGNORECASE,
    )

    for match in experience_pattern.finditer(
        text
    ):

        if _experience_requirement_is_preferred(
            text,
            match.start(),
            match.end(),
        ):
            continue

        try:
            value = float(
                match.group(1)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if value >= 0:
            values.append(value)

    # --------------------------------------------------------
    # 2. Minimum / at least X years
    # --------------------------------------------------------

    minimum_pattern = re.compile(
        r"\b"
        r"(?:minimum|at\s+least)"
        r"\s+"
        r"(\d+(?:\.\d+)?)"
        r"\s*\+?\s*"
        r"(?:years?|yrs?)"
        r"\b",
        flags=re.IGNORECASE,
    )

    for match in minimum_pattern.finditer(
        text
    ):

        if _experience_requirement_is_preferred(
            text,
            match.start(),
            match.end(),
        ):
            continue

        try:
            value = float(
                match.group(1)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if value >= 0:
            values.append(value)

    # --------------------------------------------------------
    # 3. X years required / mandatory / essential
    # --------------------------------------------------------

    required_pattern = re.compile(
        r"\b"
        r"(\d+(?:\.\d+)?)"
        r"\s*\+?\s*"
        r"(?:years?|yrs?)"
        r"\s+"
        r"(?:required|mandatory|essential)"
        r"\b",
        flags=re.IGNORECASE,
    )

    for match in required_pattern.finditer(
        text
    ):

        try:
            value = float(
                match.group(1)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if value >= 0:
            values.append(value)

    # --------------------------------------------------------
    # 4. Conservative bare-year fallback
    # --------------------------------------------------------

    bare_pattern = re.compile(
        r"\b"
        r"(\d+(?:\.\d+)?)"
        r"\s*\+?\s*"
        r"(?:years?|yrs?)"
        r"\b",
        flags=re.IGNORECASE,
    )

    for match in bare_pattern.finditer(
        text
    ):

        # If this is already represented by another explicit
        # pattern, don't add it again.
        clause = _extract_clause_around_match(
            text,
            match.start(),
            match.end(),
        )

        if not clause:
            continue

        if _experience_requirement_is_preferred(
            text,
            match.start(),
            match.end(),
        ):
            continue

        # Only accept bare years when they occur in an
        # experience-oriented clause.
        if not re.search(
            r"\bexperience\b",
            clause,
            flags=re.IGNORECASE,
        ):
            if not re.search(
                r"\b(?:minimum|at\s+least)\b",
                clause,
                flags=re.IGNORECASE,
            ):
                continue

        try:
            value = float(
                match.group(1)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if value >= 0:
            values.append(value)

    if not values:
        return None

    return max(values)

def _project_keyword_relevance(
    project_text: str,
    ats_keywords: list[str],
) -> Decimal:
    """
    Measure how strongly projects demonstrate ATS keywords.

    Projects are supporting evidence only.

    Projects NEVER contribute professional experience years.

    Both technical skills and ordinary ATS keywords use the same
    canonical representation used elsewhere in ATS scoring.
    """

    if not project_text or not ats_keywords:
        return Decimal("0.00")

    project_text = _normalize(
        project_text
    )

    technical_skills = (
        _technical_canonical_skills()
    )

    canonical_keywords: list[str] = []

    for keyword in ats_keywords:

        cleaned = _clean_keyword(
            keyword
        )

        if not cleaned:
            continue

        canonical_skill = _canonical_skill(
            cleaned
        )

        # ----------------------------------------------------
        # Technical skill
        # ----------------------------------------------------

        if canonical_skill in technical_skills:
            canonical_keywords.append(
                canonical_skill
            )
            continue

        # ----------------------------------------------------
        # Ordinary keyword
        # ----------------------------------------------------

        canonical_keyword = (
            _keyword_alias_lookup(
                cleaned
            )
        )

        if not canonical_keyword:
            continue

        canonical_alias_skill = (
            _canonical_skill(
                canonical_keyword
            )
        )

        if (
            canonical_alias_skill
            in technical_skills
        ):
            canonical_keywords.append(
                canonical_alias_skill
            )
        else:
            canonical_keywords.append(
                canonical_keyword
            )

    canonical_keywords = (
        _unique_preserve_order(
            canonical_keywords
        )
    )

    if not canonical_keywords:
        return Decimal("0.00")

    matched: set[str] = set()

    for keyword in canonical_keywords:

        # ----------------------------------------------------
        # Technical skill matching
        # ----------------------------------------------------

        if keyword in technical_skills:

            aliases = (
                _skill_aliases_for_canonical(
                    keyword
                )
            )

            if any(
                _skill_alias_matches_text(
                    project_text,
                    alias,
                )
                for alias in aliases
            ):
                matched.add(keyword)

            continue

        # ----------------------------------------------------
        # Ordinary ATS keyword matching
        # ----------------------------------------------------

        if _contains_normalized_term(
            project_text,
            keyword,
        ):
            matched.add(keyword)

    ratio = (
        Decimal(len(matched))
        / Decimal(len(canonical_keywords))
    )

    return _score(
        ratio * Decimal("100")
    )

def _calculate_experience_score(
    parsed_data: dict[str, Any],
    resume_text: str,
    job_text: str,
    job_skills: set[str],
) -> Decimal:
    """
    Calculate experience compatibility.

    Professional experience = 70%
    Relevant project evidence = 30%

    Projects never become professional experience years.

    If the candidate already satisfies the required professional
    experience duration, the experience component is 100%.

    If the candidate falls short, project relevance can partially
    compensate for the experience component.
    """

    required_years = (
        _required_experience_years(
            job_text
        )
    )

    if required_years is None:
        return Decimal("100.00")

    experience_text = (
        _extract_experience_text(
            parsed_data
        )
    )

    project_text = (
        _extract_project_text(
            parsed_data
        )
    )

    resume_years = (
        _extract_years_from_text(
            experience_text
        )
    )

    if resume_years is None:
        resume_years = 0.0

    # --------------------------------------------------------
    # Candidate already satisfies requirement.
    # --------------------------------------------------------

    if resume_years >= required_years:
        return Decimal("100.00")

    # --------------------------------------------------------
    # Professional experience score.
    # --------------------------------------------------------

    if required_years <= 0:
        professional_score = (
            Decimal("100.00")
        )

    else:
        professional_ratio = (
            Decimal(str(resume_years))
            / Decimal(str(required_years))
        )

        professional_score = _score(
            professional_ratio
            * Decimal("100")
        )

    # --------------------------------------------------------
    # Project relevance.
    # --------------------------------------------------------

    ats_keywords = (
        _extract_keyword_candidates(
            job_text,
            job_skills=job_skills,
        )
    )

    project_score = (
        _project_keyword_relevance(
            project_text,
            ats_keywords,
        )
    )

    # --------------------------------------------------------
    # Combined experience component.
    # --------------------------------------------------------

    combined = (
        professional_score
        * Decimal("0.70")
        +
        project_score
        * Decimal("0.30")
    )

    return _score(
        combined
    )


# ============================================================
# Job text
# ============================================================

def _job_text(
    job: models.Job,
) -> str:
    """
    Build ATS analysis text from actual job content.

    Job metadata such as employment_type, experience_level and
    work_mode is deliberately excluded because these are posting
    attributes, not candidate competencies.
    """
    fields = [
        getattr(job, "title", ""),
        getattr(job, "description", ""),
        getattr(job, "requirements", ""),
        getattr(job, "responsibilities", ""),
        getattr(job, "skills", ""),
    ]

    return _normalize(
        " ".join(
            _flatten_value(value)
            for value in fields
            if value is not None
        )
    )


# ============================================================
# Overall score
# ============================================================

def _calculate_overall_score(
    skill_score: Decimal,
    experience_score: Decimal,
    education_score: Decimal,
    keyword_score: Decimal,
) -> Decimal:
    """
    Overall ATS score.

    Current production weighting:
        Skills     = 40%
        Keywords   = 25%
        Experience = 20%
        Education  = 15%
    """
    overall = (
        skill_score * SKILL_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + education_score * EDUCATION_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
    ) / Decimal("100")

    return _score(overall)


# ============================================================
# Recommendations
# ============================================================

def _build_recommendations(
    skill_score: Decimal,
    experience_score: Decimal,
    education_score: Decimal,
    keyword_score: Decimal,
    overall_score: Decimal,
    missing_skills: list[str],
    missing_keywords: list[str],
) -> list[str]:
    """
    Build concise, actionable recommendations from actual ATS gaps.

    Recommendations are driven by the component that actually
    needs improvement.

    Rules:
        1. Missing skills -> skill recommendation.
        2. Missing keywords -> keyword recommendation.
        3. Education gap -> education recommendation.
        4. Experience gap -> experience recommendation.
        5. Strong overall match -> positive summary.
        6. Avoid mentioning gaps that do not actually exist.
        7. Avoid duplicate recommendations.
    """

    recommendations: list[str] = []

    # --------------------------------------------------------
    # Normalize recommendation inputs
    # --------------------------------------------------------

    missing_skills = _unique_preserve_order(
        [
            _canonical_skill(skill)
            for skill in missing_skills
            if skill
        ]
    )

    missing_keywords = _unique_preserve_order(
        [
            _clean_keyword(keyword)
            for keyword in missing_keywords
            if keyword
        ]
    )

    # --------------------------------------------------------
    # Overall classification
    # --------------------------------------------------------

    if overall_score >= Decimal("90"):
        recommendations.append(
            "Your resume is an excellent match for this job. "
            "Focus on maintaining clear evidence for the required "
            "skills, experience, education, and job-specific keywords."
        )

    elif overall_score >= Decimal("75"):
        recommendations.append(
            "Your resume is a strong match. Focus on the specific "
            "areas identified below to improve alignment further."
        )

    elif overall_score >= Decimal("50"):
        recommendations.append(
            "Your resume has a moderate match. Address the most "
            "important gaps identified below before applying."
        )

    else:
        recommendations.append(
            "Your resume currently has a low match for this job. "
            "Review the required skills, experience, education, "
            "and job-specific requirements before applying."
        )

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    if missing_skills:

        recommendations.append(
            "Add or strengthen these job-required skills if you "
            "genuinely have them: "
            f"{', '.join(missing_skills[:8])}."
        )

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    if education_score < Decimal("100"):

        if education_score == Decimal("0"):

            recommendations.append(
                "Your education does not currently satisfy the "
                "detected mandatory qualification. Verify the "
                "requirement before applying."
            )

        else:

            recommendations.append(
                "Your education level appears to satisfy the "
                "required level, but the job specifies a different "
                "or more specific field. Make your relevant degree "
                "or specialization clearer if applicable."
            )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    if experience_score < Decimal("50"):

        recommendations.append(
            "Your resume shows limited evidence for the job's "
            "professional experience requirement. If you have "
            "additional relevant experience, make the duration, "
            "responsibilities, technologies, and measurable "
            "outcomes explicit."
        )

    elif experience_score < Decimal("80"):

        recommendations.append(
            "Strengthen the experience section by clearly "
            "connecting your professional experience and relevant "
            "projects to the target role, technologies, and "
            "measurable results."
        )

    # ----------------------------------------------------
    # Keywords
    # --------------------------------------------------------

    if missing_keywords:

        recommendations.append(
            "Improve ATS keyword alignment by naturally including "
            "job-description terms that accurately describe your "
            "experience: "
            f"{', '.join(missing_keywords[:8])}."
        )

    elif keyword_score < Decimal("70"):

        recommendations.append(
            "Your resume has relatively weak keyword alignment. "
            "Use more specific technical and role-related "
            "terminology from the job description where it "
            "truthfully reflects your experience."
        )

    elif keyword_score < Decimal("90"):

        recommendations.append(
            "Improve keyword alignment by making relevant "
            "technical and role-specific terminology more explicit."
        )

    # --------------------------------------------------------
    # If there are no meaningful gaps
    # --------------------------------------------------------

    if (
        not missing_skills
        and not missing_keywords
        and education_score >= Decimal("100")
        and experience_score >= Decimal("90")
        and keyword_score >= Decimal("90")
        and overall_score >= Decimal("90")
    ):
        return [
            "Your resume is an excellent match for this job. "
            "No major ATS improvements are currently needed."
        ]

    # --------------------------------------------------------
    # Remove duplicate recommendations
    # --------------------------------------------------------

    return _unique_preserve_order(
        recommendations
    )[:6]

# ============================================================
# Database helpers
# ============================================================

def _get_resume(
    db: Session,
    resume_id: int,
) -> models.Resume:
    resume = (
        db.query(models.Resume)
        .filter(
            models.Resume.id == resume_id
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found.",
        )

    return resume


def _get_job(
    db: Session,
    job_id: int,
) -> models.Job:
    job = (
        db.query(models.Job)
        .filter(
            models.Job.id == job_id
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    return job


def _assert_resume_ownership(
    resume: models.Resume,
    current_user: "models.User | None",
    *,
    allow_missing_user: bool = False,
) -> None:
    """
    Fail-closed ownership check.

    Missing user context is denied unless the caller explicitly opts
    into a trusted system/background call with allow_missing_user=True.

    If the configured owner column does not exist, fail closed rather
    than silently exposing another user's resume.
    """
    if current_user is None:
        if allow_missing_user:
            logger.info(
                "Ownership check bypassed for resume_id=%s: "
                "no user context, explicitly allowed by caller.",
                getattr(resume, "id", "?"),
            )
            return

        logger.warning(
            "Ownership check failed: no authenticated user context "
            "was provided for resume_id=%s.",
            getattr(resume, "id", "?"),
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission to analyze this resume."
            ),
        )

    if not hasattr(resume, RESUME_OWNER_FIELD):
        logger.error(
            "Resume model has no '%s' attribute. Ownership check "
            "cannot be performed safely for resume_id=%s.",
            RESUME_OWNER_FIELD,
            getattr(resume, "id", "?"),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Resume ownership configuration is invalid."
            ),
        )

    owner_id = getattr(
        resume,
        RESUME_OWNER_FIELD,
        None,
    )

    current_id = getattr(
        current_user,
        "id",
        None,
    )

    # A missing owner_id must also fail closed. Otherwise a malformed
    # row could become accessible to any authenticated candidate.
    if owner_id is None or current_id is None:
        logger.error(
            "Ownership information is incomplete for resume_id=%s.",
            getattr(resume, "id", "?"),
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission to analyze this resume."
            ),
        )

    if owner_id != current_id:
        logger.info(
            "Ownership check failed: resume_id=%s belongs to "
            "user_id=%s, requested by user_id=%s.",
            getattr(resume, "id", "?"),
            owner_id,
            current_id,
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission to analyze this resume."
            ),
        )


# ============================================================
# Create / update ATS analysis
# ============================================================

def _apply_analysis_values(
    analysis: models.ATSAnalysis,
    *,
    overall_score: Decimal,
    skill_score: Decimal,
    experience_score: Decimal,
    education_score: Decimal,
    keyword_score: Decimal,
    matched_skills: list[str],
    missing_skills: list[str],
    matched_keywords: list[str],
    missing_keywords: list[str],
    recommendations: list[str],
) -> None:
    """Apply calculated ATS values to an analysis ORM object."""
    analysis.overall_score = overall_score
    analysis.skill_score = skill_score
    analysis.experience_score = experience_score
    analysis.education_score = education_score
    analysis.keyword_score = keyword_score
    analysis.matched_skills = matched_skills
    analysis.missing_skills = missing_skills
    analysis.matched_keywords = matched_keywords
    analysis.missing_keywords = missing_keywords
    analysis.recommendations = recommendations


def _save_ats_analysis(
    db: Session,
    analysis: models.ATSAnalysis,
    *,
    operation: str,
    resume_id: int,
    job_id: int,
) -> models.ATSAnalysis:
    """
    Commit and refresh an ATSAnalysis record.

    Rolls back the transaction on database failure and converts the
    SQLAlchemy error into a controlled HTTP 500 response.
    """
    try:
        db.commit()
        db.refresh(analysis)
        return analysis

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error %s ATS analysis "
            "(analysis_id=%s, resume_id=%s, job_id=%s).",
            operation,
            getattr(analysis, "id", "?"),
            resume_id,
            job_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to {operation} ATS analysis due to "
                "a database error."
            ),
        )


def analyze_resume_against_job(
    db: Session,
    resume_id: int,
    job_id: int,
    current_user: "models.User | None" = None,
    *,
    allow_missing_user: bool = False,
):
    """
    Analyze one resume against one job.

    The (resume_id, job_id) pair represents one logical ATS analysis.
    Re-running analysis updates the existing record.

    IMPORTANT: a database-level UNIQUE constraint on
    (resume_id, job_id) on models.ATSAnalysis is required for true
    concurrency safety - the IntegrityError handling below is a
    no-op if that constraint doesn't exist in the schema, e.g.:

        class ATSAnalysis(Base):
            __tablename__ = "ats_analyses"
            __table_args__ = (
                UniqueConstraint(
                    "resume_id", "job_id",
                    name="uq_ats_analysis_resume_job",
                ),
            )
    """
    try:
        return _analyze_resume_against_job_impl(
            db=db,
            resume_id=resume_id,
            job_id=job_id,
            current_user=current_user,
            allow_missing_user=allow_missing_user,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error during ATS analysis "
            "(resume_id=%s, job_id=%s).",
            resume_id,
            job_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred while analyzing "
                "this resume. The issue has been logged."
            ),
        )


def _analyze_resume_against_job_impl(
    db: Session,
    resume_id: int,
    job_id: int,
    current_user: "models.User | None" = None,
    allow_missing_user: bool = False,
) -> models.ATSAnalysis:
    """
    Analyze one resume against one job and create or update the
    corresponding ATSAnalysis record.

    The logical identity of an analysis is:

        (resume_id, job_id)

    Resume ownership is validated before analysis.

    A database UNIQUE constraint on (resume_id, job_id) protects
    against duplicate analyses during concurrent creation.

    Existing analysis rows are locked during updates where the
    database supports row-level locking.

    Re-running an analysis updates the existing record.
    """

    # ========================================================
    # 1. Load resume and job
    # ========================================================

    resume = _get_resume(
        db,
        resume_id,
    )

    job = _get_job(
        db,
        job_id,
    )

    # ========================================================
    # 2. Authorization
    # ========================================================

    _assert_resume_ownership(
        resume,
        current_user,
        allow_missing_user=allow_missing_user,
    )

    # ========================================================
    # 3. Load parsed resume data
    # ========================================================

    parsed_data = _get_parsed_data(
        resume
    )

    resume_text = _resume_text(
        resume,
        parsed_data,
    )

    job_text = _job_text(
        job
    )

    if not resume_text:
        raise HTTPException(
            status_code=409,
            detail=(
                "Resume text is not available for ATS analysis."
            ),
        )

    if not job_text:
        raise HTTPException(
            status_code=409,
            detail=(
                "Job content is not available for ATS analysis."
            ),
        )

    # ========================================================
    # 4. Skills
    # ========================================================

    resume_skills = _extract_resume_skills(
        parsed_data,
        resume_text,
    )

    job_skills = _extract_job_skills(
        job,
        job_text,
    )

    (
        skill_score,
        matched_skills,
        missing_skills,
    ) = _calculate_skill_score(
        resume_skills,
        job_skills,
    )

    # ========================================================
    # 5. Keywords
    # ========================================================

    (
        keyword_score,
        matched_keywords,
        missing_keywords,
    ) = _calculate_keyword_score(
        resume_text,
        job_text,
        job_skills,
    )

    # ========================================================
    # 6. Education
    # ========================================================

    education_score = _calculate_education_score(
        parsed_data,
        resume_text,
        job_text,
    )

    # ========================================================
    # 7. Experience
    # ========================================================

    experience_score = _calculate_experience_score(
        parsed_data,
        resume_text,
        job_text,
        job_skills,
    )

    # ========================================================
    # 8. Overall score
    # ========================================================

    overall_score = _calculate_overall_score(
        skill_score,
        experience_score,
        education_score,
        keyword_score,
    )

    # ========================================================
    # 9. Recommendations
    # ========================================================

    recommendations = _build_recommendations(
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        keyword_score=keyword_score,
        overall_score=overall_score,
        missing_skills=missing_skills,
        missing_keywords=missing_keywords,
    )

    # ========================================================
    # 10. Find existing analysis
    # ========================================================

    analysis = (
        db.query(models.ATSAnalysis)
        .filter(
            models.ATSAnalysis.resume_id == resume_id,
            models.ATSAnalysis.job_id == job_id,
        )
        .with_for_update()
        .first()
    )

    # ========================================================
    # 11. Update existing analysis
    # ========================================================

    if analysis is not None:
        _apply_analysis_values(
            analysis,
            overall_score=overall_score,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            keyword_score=keyword_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            recommendations=recommendations,
        )

        if hasattr(analysis, "updated_at"):
            analysis.updated_at = datetime.now(
                timezone.utc
            )

        return _save_ats_analysis(
            db,
            analysis,
            operation="update",
            resume_id=resume_id,
            job_id=job_id,
        )

    # ========================================================
    # 12. Create new analysis
    # ========================================================
    
    analysis = models.ATSAnalysis(
        resume_id=resume_id,
        job_id=job_id,
        overall_score=overall_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        keyword_score=keyword_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        recommendations=recommendations,
    )

    db.add(analysis)

    try:
        db.commit()
        db.refresh(analysis)
        return analysis

    except IntegrityError:

        db.rollback()

        logger.info(
            "IntegrityError while creating ATS analysis "
            "(resume_id=%s, job_id=%s). Checking whether "
            "another analysis was created concurrently.",
            resume_id,
            job_id,
        )

        # ----------------------------------------------------
        # Look for the expected concurrent row.
        # ----------------------------------------------------

        existing_analysis = (
            db.query(models.ATSAnalysis)
            .filter(
                models.ATSAnalysis.resume_id
                == resume_id,
                models.ATSAnalysis.job_id
                == job_id,
            )
            .with_for_update()
            .first()
        )

        # ----------------------------------------------------
        # No existing row means this was NOT the expected
        # duplicate-creation race.
        # ----------------------------------------------------

        if existing_analysis is None:

            logger.exception(
                "IntegrityError creating ATS analysis "
                "(resume_id=%s, job_id=%s) and no concurrent "
                "analysis was found.",
                resume_id,
                job_id,
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to create ATS analysis because "
                    "of a database integrity error."
                ),
            )

        # ----------------------------------------------------
        # Expected concurrent creation.
        # Update the row that won the race.
        # ----------------------------------------------------

        logger.info(
            "Concurrent ATS analysis creation detected. "
            "Updating existing analysis "
            "(analysis_id=%s, resume_id=%s, job_id=%s).",
            getattr(
                existing_analysis,
                "id",
                "?",
            ),
            resume_id,
            job_id,
        )

        _apply_analysis_values(
            existing_analysis,
            overall_score=overall_score,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            keyword_score=keyword_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            recommendations=recommendations,
        )

        if hasattr(
            existing_analysis,
            "updated_at",
        ):
            existing_analysis.updated_at = (
                datetime.now(timezone.utc)
            )

        return _save_ats_analysis(
            db,
            existing_analysis,
            operation="update",
            resume_id=resume_id,
            job_id=job_id,
        )

    except SQLAlchemyError:

        db.rollback()

        logger.exception(
            "Database error creating ATS analysis "
            "(resume_id=%s, job_id=%s).",
            resume_id,
            job_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save ATS analysis due to "
                "a database error."
            ),
        )

# ============================================================
# Get ATS analysis
# ============================================================

def get_ats_analysis(
    db: Session,
    analysis_id: int,
    current_user: models.User,
) -> models.ATSAnalysis:
    analysis = (
        db.query(models.ATSAnalysis)
        .filter(
            models.ATSAnalysis.id == analysis_id
        )
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="ATS analysis not found.",
        )

    resume = _get_resume(
        db,
        analysis.resume_id,
    )

    _assert_resume_ownership(
        resume,
        current_user,
    )

    return analysis

# ============================================================
# Get ATS analysis by resume + job
# ============================================================

def get_ats_analysis_for_resume_job(
    db: Session,
    resume_id: int,
    job_id: int,
    current_user: models.User,
) -> models.ATSAnalysis:
    resume = _get_resume(
        db,
        resume_id,
    )

    _assert_resume_ownership(
        resume,
        current_user,
    )

    analysis = (
        db.query(models.ATSAnalysis)
        .filter(
            models.ATSAnalysis.resume_id == resume_id,
            models.ATSAnalysis.job_id == job_id,
        )
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "ATS analysis not found for this resume and job."
            ),
        )

    return analysis



