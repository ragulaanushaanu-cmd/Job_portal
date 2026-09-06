import os
import re
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import models


# ============================================================
# CONFIGURATION
# ============================================================

PARSER_VERSION = "2.8"

MAX_NAME_WORDS = 5
MAX_PROJECT_TITLE_WORDS = 10
MAX_EXPERIENCE_HEADING_WORDS = 12

SUPPORTED_FILE_TYPES = {"pdf", "docx"}
CURRENT_YEAR = 2026

MIN_EXTRACTED_TEXT_LENGTH = 40
MAX_WARNING_LENGTH = 500

MIN_NAME_SCORE = 40

MAX_EDUCATION_ENTRIES = 10
MAX_EXPERIENCE_ENTRIES = 20
MAX_PROJECT_ENTRIES = 30


# ============================================================
# SKILL VOCABULARY
# ============================================================

SKILL_VOCABULARY = {
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "javascript": "JavaScript",
    "typescript": "TypeScript",

    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "oracle": "Oracle",
    "sqlite": "SQLite",

    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "spring boot": "Spring Boot",

    "rest api": "REST API",
    "rest apis": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "api development": "API Development",
    "crud": "CRUD",
    "crud operations": "CRUD",

    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "entity framework": "Entity Framework",
    "hibernate": "Hibernate",

    "jwt": "JWT",
    "jwt authentication": "JWT",
    "oauth": "OAuth",
    "oauth2": "OAuth",
    "rbac": "RBAC",
    "role based access control": "RBAC",
    "role-based access control": "RBAC",

    "oop": "OOP",
    "object oriented programming": "OOP",
    "object-oriented programming": "OOP",

    "data structures": "Data Structures",
    "data structure": "Data Structures",
    "algorithms": "Algorithms",
    "algorithm": "Algorithms",

    "database design": "Database Design",

    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "postman": "Postman",
    "vs code": "VS Code",
    "visual studio code": "VS Code",

    "docker": "Docker",
    "kubernetes": "Kubernetes",

    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",

    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",

    "react": "React",
    "react.js": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",

    "pandas": "Pandas",
    "numpy": "NumPy",

    "machine learning": "Machine Learning",
    "artificial intelligence": "Artificial Intelligence",
    "generative ai": "Generative AI",

    "chatgpt": "ChatGPT",
    "google gemini": "Google Gemini",
    "gemini": "Google Gemini",

    "servicenow": "ServiceNow",
    "service now": "ServiceNow",
}


# ============================================================
# AI TOOL VOCABULARY
# ============================================================

AI_TOOL_VOCABULARY = {
    "chatgpt": "ChatGPT",
    "openai chatgpt": "ChatGPT",
    "google gemini": "Google Gemini",
    "gemini": "Google Gemini",
    "github copilot": "GitHub Copilot",
    "copilot": "GitHub Copilot",
    "claude": "Claude",
    "anthropic claude": "Claude",
}


AI_TOOL_SEARCH_NAMES = {
    key.casefold()
    for key in AI_TOOL_VOCABULARY
}


# ============================================================
# SECTION ALIASES
# ============================================================

SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "objective",
        "career objective",
    },
    "skills": {
        "skills",
        "technical skills",
        "technical skill",
        "key skills",
        "core skills",
        "technical competencies",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internship",
        "internships",
        "work history",
    },
    "projects": {
        "projects",
        "project",
        "personal projects",
        "academic projects",
        "key projects",
        "technical projects",
    },
    "education": {
        "education",
        "academic qualification",
        "academic qualifications",
        "qualifications",
        "educational background",
    },
    "certifications": {
        "certification",
        "certifications",
        "certificates",
        "licenses and certifications",
    },
    "languages": {
        "language",
        "languages",
        "known languages",
    },
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_unicode_punctuation(value: str) -> str:
    if not value:
        return ""

    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2012": "-",
        "\u2011": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u2007": " ",
        "\u202f": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value


def normalize_whitespace(value: str) -> str:
    if not value:
        return ""

    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")
    value = value.replace("\xa0", " ")
    value = value.replace("\u2007", " ")
    value = value.replace("\u202f", " ")

    # Collapse spaces and tabs only.
    value = re.sub(r"[ \t]+", " ", value)

    # Remove spaces before punctuation.
    value = re.sub(
        r"\s+([,.;:!?])",
        r"\1",
        value,
    )

    # Remove spaces inside brackets.
    value = re.sub(
        r"([\(\[\{])\s+",
        r"\1",
        value,
    )

    value = re.sub(
        r"\s+([\)\]\}])",
        r"\1",
        value,
    )

    return value.strip()


def normalize_common_pdf_artifacts(value: str) -> str:
    if not value:
        return ""

    value = normalize_unicode_punctuation(value)

    replacements = {
        "CGP A": "CGPA",
        "CGP A:": "CGPA:",
        "C G P A": "CGPA",
        "G P A": "GPA",

        "Object- Oriented": "Object-Oriented",
        "object- oriented": "object-oriented",

        "problem- solving": "problem-solving",
        "problem- Solving": "problem-Solving",

        "role- based": "role-based",
        "role- Based": "role-Based",

        "real- world": "real-world",
        "Real- World": "Real-World",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return normalize_whitespace(value)


def clean_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    value = normalize_common_pdf_artifacts(value)
    value = normalize_whitespace(value)

    return value if value else None


def clean_list(values: list[str]) -> list[str]:
    result = []
    seen = set()

    for value in values:
        cleaned = clean_value(value)

        if not cleaned:
            continue

        key = cleaned.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return result


# ============================================================
# BULLETS
# ============================================================

def normalize_bullet_characters(text: str) -> str:
    if not text:
        return ""

    replacements = {
        "●": "•",
        "▪": "•",
        "◦": "•",
        "‣": "•",
        "➢": "•",
        "➤": "•",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def is_bullet_line(line: str) -> bool:
    if not line:
        return False

    return line.strip().startswith(
        ("•", "-", "*")
    )


def clean_bullet(line: str) -> str:
    if not line:
        return ""

    line = normalize_bullet_characters(
        line.strip()
    )

    line = re.sub(
        r"^[•*\-]\s*",
        "",
        line,
    )

    return line.strip()


def split_bullets(line: str) -> list[str]:
    if not line:
        return []

    cleaned = clean_bullet(line)

    if not cleaned:
        return []

    parts = re.split(
        r"\s*•\s*",
        cleaned,
    )

    return clean_list(parts)


# ============================================================
# SECTION DETECTION
# ============================================================

def normalize_header(line: str) -> str:
    if not line:
        return ""

    value = line.strip().casefold()

    value = re.sub(
        r"[-_/|:]+",
        " ",
        value,
    )

    value = re.sub(
        r"[^a-z ]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def looks_like_heading_case(line: str) -> bool:
    """
    Genuine section headings in resumes are visually distinct from
    body text — they're written ALL CAPS ("TECHNICAL SKILLS") or
    Title Case ("Professional Summary"), never as a stray lowercase
    word floating on its own line.

    This matters because PDF text extraction frequently wraps body
    prose one or two words per line (e.g. a summary sentence like
    "...with hands-on experience building..." can extract as
    "experience" sitting alone on its own line). Without a casing
    check, that lone lowercase word matches a SECTION_ALIASES entry
    ("experience") and gets misread as the start of the Experience
    section, truncating whatever section came before it.
    """

    stripped = line.strip()

    if not stripped:
        return False

    if not any(char.isalpha() for char in stripped):
        return False

    # ALL CAPS, e.g. "TECHNICAL SKILLS", "PROJECTS".
    if stripped == stripped.upper():
        return True

    words = [
        word
        for word in stripped.split()
        if word
    ]

    if not words:
        return False

    # Title Case, e.g. "Professional Summary", "Skills".
    # Every word that starts with a letter must be capitalized.
    for word in words:
        first_alpha = next(
            (char for char in word if char.isalpha()),
            None,
        )

        if first_alpha and not first_alpha.isupper():
            return False

    return True


def detect_section(line: str) -> Optional[str]:
    if not line:
        return None

    if not looks_like_heading_case(line):
        return None

    normalized = normalize_header(line)

    if not normalized:
        return None

    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section

    return None


# Alias kept for readability at call sites — detects whether a line
# is a recognized section heading (summary/skills/experience/etc).
def is_section_heading(line: str) -> bool:
    return detect_section(line) is not None


def split_sections(text: str) -> dict[str, list[str]]:
    sections = {
        "header": []
    }

    current_section = "header"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        detected = detect_section(line)

        if detected:
            current_section = detected

            sections.setdefault(
                current_section,
                [],
            )

            continue

        sections.setdefault(
            current_section,
            [],
        ).append(line)

    return sections


def sections_text(lines: list[str]) -> str:
    return " ".join(
        line.strip()
        for line in lines
        if line.strip()
    )


# ============================================================
# HEADER / NAME QUALITY
# ============================================================

HEADER_ROLE_MARKERS = (
    "aspiring ",
    "backend ",
    "frontend ",
    "full stack ",
    "software ",
    "developer ",
    "engineer ",
    "analyst ",
    "student ",
    "intern ",
    "professional ",
    "data ",
    "python ",
    "java ",
    "javascript ",
    "sql ",
    "fastapi ",
)

CONTACT_MARKERS = (
    "linkedin",
    "github",
    "portfolio",
    "@",
    "phone",
    "email",
    "tel",
    "+91",
)


def split_header_candidates(line: str) -> list[str]:
    if not line:
        return []

    value = normalize_whitespace(line)

    if not value:
        return []

    parts = re.split(
        r"\s*[|•]\s*",
        value,
    )

    candidates = []

    for part in parts:
        part = clean_value(part)

        if not part:
            continue

        candidates.append(part)

    # Try to separate:
    # ANUSHA RAGULA Aspiring Backend Developer
    # into:
    # ANUSHA RAGULA
    # Aspiring Backend Developer
    if candidates:
        first = candidates[0]
        lower = first.casefold()

        marker_positions = []

        for marker in HEADER_ROLE_MARKERS:
            position = lower.find(marker)

            if position > 0:
                marker_positions.append(position)

        if marker_positions:
            split_at = min(marker_positions)

            possible_name = first[:split_at].strip()
            remainder = first[split_at:].strip()

            candidates = (
                [possible_name, remainder]
                + candidates[1:]
            )

    return clean_list(candidates)


# ============================================================
# NAME DETECTION
# ============================================================

def score_name_candidate(line: str) -> int:
    if not line:
        return -100

    value = normalize_whitespace(
        line.strip()
    )

    if not value:
        return -100

    words = value.split()

    if len(words) > MAX_NAME_WORDS:
        return -100

    if "@" in value:
        return -100

    if re.search(
        r"https?://|www\.|linkedin|github",
        value,
        flags=re.IGNORECASE,
    ):
        return -100

    if any(char.isdigit() for char in value):
        return -100

    if re.search(
        r"\+91|phone|email|portfolio",
        value,
        flags=re.IGNORECASE,
    ):
        return -100

    normalized = normalize_header(value)

    ignored = {
        "resume",
        "curriculum vitae",
        "cv",
        "professional summary",
        "summary",
        "technical skills",
        "skills",
        "projects",
        "experience",
        "internship",
        "internships",
        "education",
        "certifications",
        "certification",
        "languages",
    }

    if normalized in ignored:
        return -100

    if not words:
        return -100

    score = 0

    # Word count.
    if len(words) == 2:
        score += 40
    elif len(words) == 3:
        score += 35
    elif len(words) == 4:
        score += 25
    elif len(words) == 5:
        score += 15

    # Alphabetic name structure.
    if all(
        re.fullmatch(
            r"[A-Za-z.'-]+",
            word,
        )
        for word in words
    ):
        score += 35
    else:
        return -100

    # Uppercase / title case.
    if value == value.upper():
        score += 30
    elif value == value.title():
        score += 15

    role_words = {
        "developer",
        "engineer",
        "analyst",
        "intern",
        "student",
        "software",
        "backend",
        "frontend",
        "full",
        "stack",
        "data",
        "python",
        "java",
        "sql",
        "fastapi",
        "database",
        "professional",
        "aspiring",
    }

    if any(
        word.casefold() in role_words
        for word in words
    ):
        score -= 60

    if re.search(
        r"\b(with|using|building|developed|"
        r"passionate|experience|graduate|"
        r"learning|worked|implemented|"
        r"designed|created)\b",
        value,
        flags=re.IGNORECASE,
    ):
        score -= 50

    return score


def extract_header_name(
    header_lines: list[str],
) -> Optional[str]:
    if not header_lines:
        return None

    candidates = []

    for line_index, line in enumerate(
        header_lines[:6]
    ):
        parts = split_header_candidates(line)

        for part_index, candidate in enumerate(parts):
            score = score_name_candidate(candidate)

            if score < MIN_NAME_SCORE:
                continue

            score += max(
                0,
                15 - (line_index * 3),
            )

            if part_index == 0:
                score += 10

            candidates.append(
                (score, candidate)
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return clean_value(
        candidates[0][1]
    )


# ============================================================
# LINE CLASSIFICATION
# ============================================================

def is_contact_line(line: str) -> bool:
    if not line:
        return False

    return bool(
        re.search(
            r"@|https?://|www\.|linkedin|github|\+91",
            line,
            flags=re.IGNORECASE,
        )
    )


def looks_like_explicit_label(line: str) -> bool:
    if not line:
        return False

    return bool(
        re.match(
            r"^[A-Za-z][A-Za-z /]{0,30}:\s*\S+",
            line.strip(),
        )
    )


def looks_like_technology_line(line: str) -> bool:
    if not line or "•" not in line:
        return False

    parts = [
        clean_value(part)
        for part in line.split("•")
    ]

    parts = [
        part
        for part in parts
        if part
    ]

    if len(parts) < 2:
        return False

    known = 0

    skill_keys = {
        key.casefold()
        for key in SKILL_VOCABULARY
    }

    for part in parts[1:]:
        normalized = normalize_whitespace(
            part
        ).casefold()

        if normalized in skill_keys:
            known += 1

    return known >= 1


# ============================================================
# EXPERIENCE HEADING DETECTION
# ============================================================

def looks_like_experience_heading(
    line: str,
) -> bool:
    if not line:
        return False

    value = normalize_whitespace(
        line.strip()
    )

    if is_bullet_line(value):
        return False

    if value.endswith(
        (".", ",", ";", ":")
    ):
        return False

    if len(value.split()) > MAX_EXPERIENCE_HEADING_WORDS:
        return False

    lower = value.casefold()

    prose_starters = (
        "built ",
        "developed ",
        "implemented ",
        "designed ",
        "created ",
        "used ",
        "worked ",
        "learned ",
        "regularly ",
        "passionate ",
        "self-driven ",
        "with ",
        "experience ",
        "building ",
        "using ",
        "improved ",
        "strengthened ",
        "responsible ",
        "managed ",
        "worked on ",
    )

    if lower.startswith(prose_starters):
        return False

    # Strong structure.
    if "|" in value:
        return True

    # Date evidence.
    if re.search(
        r"\b(?:19|20)\d{2}\b",
        value,
    ):
        return True

    employment_keywords = (
        "intern",
        "internship",
        "developer",
        "engineer",
        "analyst",
        "associate",
        "consultant",
        "trainee",
        "manager",
        "administrator",
        "specialist",
        "assistant",
    )

    if any(
        keyword in lower
        for keyword in employment_keywords
    ):
        return True

    return False


# ============================================================
# WRAPPED LINE REPAIR
# ============================================================

def should_join_wrapped_lines(
    current: str,
    next_line: str,
) -> bool:
    if not current or not next_line:
        return False

    if is_bullet_line(next_line):
        return False

    if detect_section(current):
        return False

    if detect_section(next_line):
        return False

    if is_contact_line(next_line):
        return False

    if looks_like_explicit_label(next_line):
        return False

    if looks_like_technology_line(next_line):
        return False

    current = current.strip()
    next_line = next_line.strip()

    if current.endswith(
        (",", "-", "/", "(")
    ):
        return True

    if current.endswith(
        (".", "!", "?", ":")
    ):
        return False

    current_words = current.split()
    next_words = next_line.split()

    if len(current_words) <= 3:
        return True

    if (
        len(next_words) <= 3
        and not looks_like_experience_heading(next_line)
    ):
        return True

    if re.search(
        r"\b(and|or|but|with|using|for|to|of|in|on|"
        r"the|a|an|as|by|from|that|which|while|"
        r"into|through|during|under)$",
        current,
        flags=re.IGNORECASE,
    ):
        return True

    first_alpha = re.search(
        r"[A-Za-z]",
        next_line,
    )

    if (
        first_alpha
        and first_alpha.group(0).islower()
    ):
        return True

    return False


def repair_wrapped_lines(text: str) -> str:
    if not text:
        return ""

    raw_lines = text.splitlines()

    lines = []

    for raw_line in raw_lines:
        line = normalize_whitespace(
            raw_line.strip()
        )
        lines.append(line)

    result = []
    i = 0

    while i < len(lines):
        current = lines[i]

        if not current:
            i += 1
            continue

        while i + 1 < len(lines):
            next_line = lines[i + 1]

            if not next_line:
                break

            if not should_join_wrapped_lines(
                current,
                next_line,
            ):
                break

            current = normalize_whitespace(
                f"{current} {next_line}"
            )

            i += 1

        result.append(current)
        i += 1

    return "\n".join(result)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = normalize_unicode_punctuation(text)
    text = normalize_bullet_characters(text)
    text = normalize_common_pdf_artifacts(text)
    text = repair_wrapped_lines(text)

    cleaned_lines = []

    for line in text.splitlines():
        line = normalize_whitespace(line)

        if line:
            cleaned_lines.append(line)

    return "\n".join(
        cleaned_lines
    ).strip()


# ============================================================
# PDF / DOCX EXTRACTION
# ============================================================

def extract_pdf_text(file_path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF parsing dependency is not installed",
        )

    try:
        reader = PdfReader(file_path)

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n".join(pages).strip()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to extract text from PDF",
        )


def extract_docx_text(file_path: str) -> str:
    try:
        from docx import Document
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="DOCX parsing dependency is not installed",
        )

    try:
        document = Document(file_path)

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n".join(
            paragraphs
        ).strip()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to extract text from DOCX",
        )


def extract_resume_text(
    resume: models.Resume,
) -> str:
    if not os.path.isfile(
        resume.file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Resume file not found on server",
        )

    file_type = (
        resume.file_type or ""
    ).casefold()

    if file_type == "pdf":
        text = extract_pdf_text(
            resume.file_path
        )

    elif file_type == "docx":
        text = extract_docx_text(
            resume.file_path
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported resume file type",
        )

    if not text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in resume",
        )

    return text


def validate_extracted_text(
    text: str,
) -> str:
    cleaned = clean_text(text)

    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in resume",
        )

    if len(cleaned.strip()) < MIN_EXTRACTED_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                "Resume contains insufficient readable text. "
                "The file may be scanned or image-based."
            ),
        )

    return cleaned


# ============================================================
# PERSONAL INFORMATION
# ============================================================

def extract_email(
    text: str,
) -> Optional[str]:
    if not text:
        return None

    match = re.search(
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )

    if not match:
        return None

    return match.group(0).strip().lower()


def extract_phone(
    text: str,
) -> Optional[str]:
    if not text:
        return None

    patterns = [
        # +91 9949873722
        r"(?<!\d)\+91[\s-]?[6-9]\d{9}(?!\d)",

        # 919949873722
        r"(?<!\d)91[\s-]?[6-9]\d{9}(?!\d)",

        # 9949873722
        r"(?<!\d)[6-9]\d{9}(?!\d)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
        )

        if match:
            return match.group(0)

    return None


def normalize_phone(
    phone: Optional[str],
) -> Optional[str]:
    if not phone:
        return None

    value = phone.strip()

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    if digits.startswith("91"):
        remaining = digits[2:]

        if len(remaining) == 10:
            return f"+91 {remaining}"

    if len(digits) == 10:
        return digits

    return value


def normalize_url(
    value: Optional[str],
) -> Optional[str]:
    if not value:
        return None

    value = value.strip()

    markdown_match = re.fullmatch(
        r"\[.*?\]\((https?://[^)]+)\)",
        value,
        flags=re.IGNORECASE,
    )

    if markdown_match:
        value = markdown_match.group(1)

    value = value.strip(
        " \t\r\n.,;:()[]{}<>"
    )

    if not value:
        return None

    if not re.match(
        r"^https?://",
        value,
        flags=re.IGNORECASE,
    ):
        value = "https://" + value

    return value


def extract_link(
    text: str,
    label: str,
) -> Optional[str]:
    if not text:
        return None

    pattern = rf"""
        {re.escape(label)}
        \s*:?\s*
        (?:
            (https?://[^\s]+)
            |
            (www\.[^\s]+)
            |
            ([A-Za-z0-9.-]+\.[A-Za-z]{{2,}}/[^\s]+)
        )
    """

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    if not match:
        return None

    value = next(
        (
            group
            for group in match.groups()
            if group
        ),
        None,
    )

    return normalize_url(value)


# ============================================================
# SUMMARY
# ============================================================

def repair_section_fragments(
    lines: list[str],
) -> list[str]:
    if not lines:
        return []

    result = []

    for raw_line in lines:
        line = normalize_whitespace(raw_line)

        if not line:
            continue

        if not result:
            result.append(line)
            continue

        previous = result[-1]

        if is_bullet_line(line):
            result.append(line)
            continue

        should_merge = False

        if previous.endswith(
            (",", "-", "/", "(")
        ):
            should_merge = True

        elif len(line.split()) <= 3:
            should_merge = True

        else:
            first_alpha = re.search(
                r"[A-Za-z]",
                line,
            )

            if (
                first_alpha
                and first_alpha.group(0).islower()
            ):
                should_merge = True

        if should_merge:
            result[-1] = normalize_whitespace(
                f"{previous} {line}"
            )
        else:
            result.append(line)

    return result


def extract_summary(
    lines: list[str],
) -> Optional[str]:
    """
    Extract the complete summary section.

    NOTE: `lines` is expected to already be just the summary
    section's lines, as produced by split_sections() — that
    function already stops collecting lines for a section as
    soon as it encounters the next recognized section heading.
    So there is no need (and no reliable way, since we only have
    the pre-sliced lines here) to re-detect section boundaries
    inside this function. Earlier versions tried to re-scan for
    headings here using an undefined helper and a mismatched
    "sections" argument that was never actually passed in from
    build_parsed_data() — that caused a TypeError (500 error) on
    every resume with a summary section, and before that, a
    truncated/garbled summary because the boundary logic never
    worked correctly in the first place.

    Fragmented PDF lines are repaired before joining. No
    artificial line or character limit is applied.
    """

    if not lines:
        return None

    cleaned_lines = [
        normalize_whitespace(line)
        for line in lines
        if normalize_whitespace(line)
    ]

    if not cleaned_lines:
        return None

    # Repair PDF-extraction fragments such as:
    #
    # "with hands-on"
    # "experience"
    # "building"
    # "backend"
    # "applications"
    #
    # into:
    #
    # "with hands-on experience building backend applications"

    cleaned_lines = repair_section_fragments(cleaned_lines)

    summary = normalize_whitespace(
        " ".join(cleaned_lines)
    )

    return summary if summary else None


# ============================================================
# SKILLS
# ============================================================

def normalize_skill(
    skill: str,
) -> str:
    if not skill:
        return ""

    value = normalize_whitespace(skill)

    normalized = value.casefold()

    if normalized in SKILL_VOCABULARY:
        return SKILL_VOCABULARY[
            normalized
        ]

    simplified = re.sub(
        r"[-_]+",
        " ",
        normalized,
    )

    simplified = normalize_whitespace(
        simplified
    )

    if simplified in SKILL_VOCABULARY:
        return SKILL_VOCABULARY[
            simplified
        ]

    return value


def extract_skills(
    text: str,
    skills_section_text: str = "",
    projects_text: str = "",
    experience_text: str = "",
) -> list[str]:

    found: dict[str, int] = {}

    def scan(
        source: str,
        confidence: int,
    ) -> None:
        if not source:
            return

        for (
            search_name,
            display_name,
        ) in SKILL_VOCABULARY.items():

            if (
                search_name.casefold()
                in AI_TOOL_SEARCH_NAMES
            ):
                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(search_name)
                + r"(?!\w)"
            )

            if not re.search(
                pattern,
                source,
                flags=re.IGNORECASE,
            ):
                continue

            canonical = normalize_skill(
                display_name
            )

            if not canonical:
                continue

            found[canonical] = max(
                found.get(
                    canonical,
                    0,
                ),
                confidence,
            )

    scan(
        skills_section_text,
        100,
    )

    scan(
        projects_text,
        80,
    )

    scan(
        experience_text,
        70,
    )

    scan(
        text,
        50,
    )

    return sorted(
        clean_list(found.keys()),
        key=str.casefold,
    )


def extract_ai_tools(
    text: str,
) -> list[str]:
    if not text:
        return []

    found = {}

    for (
        search_name,
        display_name,
    ) in AI_TOOL_VOCABULARY.items():

        pattern = (
            r"(?<!\w)"
            + re.escape(search_name)
            + r"(?!\w)"
        )

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            found[display_name] = True

    return sorted(
        found.keys(),
        key=str.casefold,
    )


# ============================================================
# GENERIC TEXT HELPERS
# ============================================================

def join_fragments(
    lines: list[str],
) -> str:
    parts = [
        part.strip()
        for part in lines
        if part.strip()
    ]

    if not parts:
        return ""

    return normalize_whitespace(
        " ".join(parts)
    )


def append_continuation(
    description: list[str],
    text: str,
) -> None:
    text = clean_value(text)

    if not text:
        return

    if description:
        description[-1] = join_fragments(
            [
                description[-1],
                text,
            ]
        )
    else:
        description.append(text)


# ============================================================
# PROJECT PARSING
# ============================================================

PROJECT_TECH_LABEL_PATTERN = re.compile(
    r"^(?:technologies\s+used|"
    r"technologies|technology|"
    r"tech\s+stack(?:\s+used)?|"
    r"tech)"
    r"\s*[:\-]\s*",
    flags=re.IGNORECASE,
)


def is_project_technology_label(
    line: str,
) -> bool:
    if not line:
        return False

    return bool(
        PROJECT_TECH_LABEL_PATTERN.match(
            line.strip()
        )
    )


def extract_project_technology_values(
    line: str,
) -> list[str]:
    if not line:
        return []

    cleaned = normalize_whitespace(
        line
    )

    cleaned = (
        PROJECT_TECH_LABEL_PATTERN.sub(
            "",
            cleaned,
        ).strip()
    )

    if not cleaned:
        return []

    parts = re.split(
        r"\s*(?:•|\||,|;)\s*",
        cleaned,
    )

    technologies = []

    for part in parts:
        value = clean_value(part)

        if not value:
            continue

        normalized = normalize_skill(
            value
        )

        if normalized:
            technologies.append(
                normalized
            )

    return clean_list(
        technologies
    )


def split_project_inline_line(
    line: str,
) -> list[str]:
    if not line:
        return []

    return clean_list(
        re.split(
            r"\s*•\s*",
            line.strip(),
        )
    )


def is_known_project_technology(
    value: str,
) -> bool:
    if not value:
        return False

    normalized = normalize_whitespace(
        value
    ).casefold()

    return normalized in {
        key.casefold()
        for key in SKILL_VOCABULARY
    }


def extract_inline_project_technologies(
    parts: list[str],
) -> list[str]:
    technologies = []

    for part in parts:
        value = clean_value(part)

        if not value:
            continue

        if not is_known_project_technology(
            value
        ):
            continue

        normalized = normalize_skill(
            value
        )

        if normalized:
            technologies.append(
                normalized
            )

    return clean_list(
        technologies
    )


def project_description_line(
    line: str,
) -> list[str]:
    if not line:
        return []

    cleaned = clean_bullet(line)

    if not cleaned:
        return []

    parts = re.split(
        r"\s*•\s*",
        cleaned,
    )

    return clean_list(parts)


def looks_like_project_title(
    line: str,
) -> bool:
    if not line:
        return False

    value = line.strip()

    if is_bullet_line(value):
        return False

    if is_project_technology_label(value):
        return False

    if len(value.split()) > MAX_PROJECT_TITLE_WORDS:
        return False

    if value.endswith(
        (".", ",", ";", ":")
    ):
        return False

    if "@" in value:
        return False

    if re.search(
        r"https?://|www\.",
        value,
        flags=re.IGNORECASE,
    ):
        return False

    prose_starters = (
        "built ",
        "developed ",
        "implemented ",
        "designed ",
        "created ",
        "used ",
        "worked ",
        "integrated ",
        "configured ",
        "deployed ",
        "maintained ",
        "tested ",
        "optimized ",
        "improved ",
        "strengthened ",
        "learned ",
        "managed ",
        "responsible ",
        "automated ",
        "validated ",
        "secured ",
        "added ",
        "performed ",
        "handled ",
        "supported ",
        "regularly ",
        "passionate ",
        "self-driven ",
        "with ",
        "experience ",
        "using ",
    )

    lower = value.casefold()

    if lower.startswith(
        prose_starters
    ):
        return False

    if re.search(
        r"\b(is|are|was|were|has|have|"
        r"use|uses|using|developed|building|"
        r"learning|improving|passionate)\b",
        lower,
    ):
        return False

    return True


def finalize_project(
    project: Optional[dict],
) -> Optional[dict]:
    if not project:
        return None

    name = clean_value(
        project.get("name")
    )

    description = clean_list(
        project.get(
            "description",
            [],
        )
    )

    technologies = clean_list(
        project.get(
            "technologies",
            [],
        )
    )

    if not name:
        return None

    return {
        "name": name,
        "description": description,
        "technologies": [
            normalize_skill(value)
            for value in technologies
        ],
    }


def extract_projects(
    lines: list[str],
) -> list[dict]:
    if not lines:
        return []

    projects = []
    current = None

    def finish_current():
        nonlocal current

        if current is None:
            return

        finalized = finalize_project(
            current
        )

        if finalized:
            projects.append(
                finalized
            )

        current = None

    i = 0

    while i < len(lines):

        if len(projects) >= MAX_PROJECT_ENTRIES:
            break

        line = normalize_whitespace(
            lines[i]
        )

        if not line:
            i += 1
            continue

        # Explicit technology line.
        if is_project_technology_label(
            line
        ):
            if current is not None:
                current[
                    "technologies"
                ].extend(
                    extract_project_technology_values(
                        line
                    )
                )

            i += 1
            continue

        # Bullet description.
        if is_bullet_line(line):
            if current is not None:
                current[
                    "description"
                ].extend(
                    project_description_line(
                        line
                    )
                )

            i += 1
            continue

        # Inline title + technologies.
        if "•" in line:
            parts = split_project_inline_line(
                line
            )

            if len(parts) >= 2:

                # A project is already open, so this line is a
                # continuation (most commonly a bare tech-stack line
                # like "Python • FastAPI • MySQL • SQLAlchemy") — not
                # a new title. Every part, INCLUDING the first one,
                # should be checked as a technology here. Treating
                # only parts[1:] as candidate technologies (as an
                # earlier version of this function did) silently
                # dropped the first listed technology on every
                # project whenever it doubled as this branch's now
                # unused "title" candidate — e.g. "Python" was lost
                # from every project's technologies list because it
                # was parts[0] of a tech-stack line, not a new title.
                if current is not None:
                    technologies = (
                        extract_inline_project_technologies(
                            parts
                        )
                    )

                    known = {
                        value.casefold()
                        for value in technologies
                    }

                    current[
                        "technologies"
                    ].extend(
                        technologies
                    )

                    for part in parts:
                        if (
                            part.casefold()
                            not in known
                        ):
                            current[
                                "description"
                            ].append(part)

                    i += 1
                    continue

                # No project open yet: parts[0] may be a brand-new
                # project title, with the remaining parts as its
                # technologies.
                title = parts[0]

                technologies = (
                    extract_inline_project_technologies(
                        parts[1:]
                    )
                )

                if (
                    looks_like_project_title(
                        title
                    )
                    and technologies
                ):
                    current = {
                        "name": title,
                        "description": [],
                        "technologies": technologies,
                    }

                    i += 1
                    continue

        # New project title.
        if looks_like_project_title(line):

            next_line = (
                lines[i + 1].strip()
                if i + 1 < len(lines)
                else ""
            )

            next_is_tech = (
                is_project_technology_label(
                    next_line
                )
                or looks_like_technology_line(
                    next_line
                )
            )

            next_is_description = (
                is_bullet_line(
                    next_line
                )
            )

            if (
                next_is_tech
                or next_is_description
            ):
                if current is not None:
                    finish_current()

                current = {
                    "name": clean_value(line),
                    "description": [],
                    "technologies": [],
                }

                i += 1
                continue

        # Continuation.
        if current is not None:
            append_continuation(
                current["description"],
                line,
            )

        i += 1

    finish_current()

    return projects


# ============================================================
# EDUCATION
# ============================================================

DEGREE_PATTERNS = [
    r"\bBachelor of [A-Za-z]+(?:\s+\([^)]+\))?",
    r"\bMaster of [A-Za-z]+(?:\s+\([^)]+\))?",
    r"\bB\.?\s*Tech\.?\b",
    r"\bM\.?\s*Tech\.?\b",
    r"\bB\.?\s*Sc\.?\b",
    r"\bM\.?\s*Sc\.?\b",
    r"\bB\.?\s*Com\.?\b",
    r"\bM\.?\s*Com\.?\b",
    r"\bBCA\b",
    r"\bMCA\b",
    r"\bMBA\b",
    r"\bPh\.?\s*D\.?\b",
]


def parse_education_entry(
    lines: list[str],
) -> Optional[dict]:
    cleaned_lines = clean_list(lines)

    if not cleaned_lines:
        return None

    result = {
        "details": cleaned_lines
    }

    text = join_fragments(
        cleaned_lines
    )

    # Degree.
    for pattern in DEGREE_PATTERNS:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            result["degree"] = clean_value(
                match.group(0)
            )
            break

    # Institution / university.
    institution = None
    university = None

    for line in cleaned_lines:
        candidate = line

        candidate = re.sub(
            r"\b(?:CGPA|GPA)"
            r"\s*[:\-]?\s*"
            r"\d+(?:\.\d+)?"
            r"(?:\s*/\s*\d+(?:\.\d+)?)?",
            "",
            candidate,
            flags=re.IGNORECASE,
        )

        candidate = re.sub(
            r"\b(?:19|20)\d{2}"
            r"\s*[-–—]\s*"
            r"(?:19|20)\d{2}\b",
            "",
            candidate,
        )

        candidate = candidate.strip(
            " ,|-"
        )

        if not candidate:
            continue

        parts = [
            part.strip()
            for part in candidate.split(",")
            if part.strip()
        ]

        for part in parts:
            lower = part.casefold()

            if "university" in lower:
                if university is None:
                    university = part

            elif (
                "college" in lower
                or "institute" in lower
            ):
                if institution is None:
                    institution = part

    if institution:
        result["institution"] = clean_value(
            institution
        )

    if university:
        result["university"] = clean_value(
            university
        )

    # CGPA / GPA.
    cgpa_match = re.search(
        r"\b(?:CGPA|GPA)"
        r"\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if cgpa_match:
        try:
            result["cgpa"] = float(
                cgpa_match.group(1)
            )
        except ValueError:
            pass

    # Year range.
    year_match = re.search(
        r"\b(19\d{2}|20\d{2})"
        r"\s*[-–—]\s*"
        r"(19\d{2}|20\d{2})\b",
        text,
    )

    if year_match:
        result["start_year"] = int(
            year_match.group(1)
        )

        result["end_year"] = int(
            year_match.group(2)
        )

    return result


def extract_education(
    lines: list[str],
) -> list[dict]:
    if not lines:
        return []

    cleaned_lines = clean_list(lines)

    if not cleaned_lines:
        return []

    entries = []
    current = []

    for line in cleaned_lines:

        # A new degree strongly indicates
        # another education entry.
        contains_degree = any(
            re.search(
                pattern,
                line,
                flags=re.IGNORECASE,
            )
            for pattern in DEGREE_PATTERNS
        )

        if (
            contains_degree
            and current
        ):
            entry = parse_education_entry(
                current
            )

            if entry:
                entries.append(entry)

            current = []

        current.append(line)

        if len(entries) >= MAX_EDUCATION_ENTRIES:
            break

    if (
        current
        and len(entries) < MAX_EDUCATION_ENTRIES
    ):
        entry = parse_education_entry(
            current
        )

        if entry:
            entries.append(entry)

    return entries


# ============================================================
# EXPERIENCE
# ============================================================

def parse_experience_heading(
    line: str,
) -> dict:
    result = {
        "title": None,
        "company": None,
        "organization": None,
        "start_year": None,
        "end_year": None,
    }

    value = clean_value(line)

    if not value:
        return result

    # Year range.
    year_range = re.search(
        r"\b(19\d{2}|20\d{2})"
        r"\s*[-–—]\s*"
        r"(19\d{2}|20\d{2}|Present|Current)\b",
        value,
        flags=re.IGNORECASE,
    )

    if year_range:
        result["start_year"] = int(
            year_range.group(1)
        )

        end_value = year_range.group(2)

        if end_value.isdigit():
            result["end_year"] = int(
                end_value
            )

        value = (
            value[:year_range.start()]
            + value[year_range.end():]
        )

    else:
        single_year = re.search(
            r"\b(19\d{2}|20\d{2})\b",
            value,
        )

        if single_year:
            result["end_year"] = int(
                single_year.group(1)
            )

            value = (
                value[:single_year.start()]
                + value[single_year.end():]
            )

    value = re.sub(
        r"\(\s*\)",
        "",
        value,
    )

    value = value.strip(
        " |-(),"
    )

    parts = [
        part.strip()
        for part in re.split(
            r"\s*\|\s*",
            value,
        )
        if part.strip()
    ]

    if parts:
        result["title"] = clean_value(
            parts[0]
        )

    if len(parts) >= 2:
        result["company"] = clean_value(
            parts[1]
        )

    if len(parts) >= 3:
        result["organization"] = clean_value(
            parts[2]
        )

    return {
        key: value
        for key, value in result.items()
        if value not in (None, "")
    }


def extract_experience(
    lines: list[str],
) -> list[dict]:
    if not lines:
        return []

    experience = []
    current = None

    def finalize():
        nonlocal current

        if current is None:
            return

        current["description"] = clean_list(
            current.get(
                "description",
                [],
            )
        )

        if (
            current.get("title")
            or current.get("company")
            or current.get("organization")
        ):
            experience.append(
                current
            )

        current = None

    i = 0

    while i < len(lines):

        if len(experience) >= MAX_EXPERIENCE_ENTRIES:
            break

        line = normalize_whitespace(
            lines[i]
        )

        if not line:
            i += 1
            continue

        # Bullet.
        if is_bullet_line(line):
            if current is not None:
                current[
                    "description"
                ].extend(
                    split_bullets(line)
                )

            i += 1
            continue

        # Experience heading.
        if looks_like_experience_heading(
            line
        ):
            finalize()

            current = parse_experience_heading(
                line
            )

            current["description"] = []

            i += 1
            continue

        # Continuation.
        if current is not None:
            append_continuation(
                current["description"],
                line,
            )

        i += 1

    finalize()

    return experience


# ============================================================
# CERTIFICATIONS
# ============================================================

def extract_certifications(
    lines: list[str],
) -> list[str]:
    values = []

    for line in lines:
        if is_bullet_line(line):
            values.extend(
                split_bullets(line)
            )
        else:
            values.append(line)

    return clean_list(values)


# ============================================================
# LANGUAGES
# ============================================================

def extract_languages(
    lines: list[str],
) -> list[str]:
    if not lines:
        return []

    values = []

    for line in lines:
        parts = re.split(
            r"\s*(?:•|,|\|)\s*",
            line,
        )

        values.extend(parts)

    return clean_list(values)


# ============================================================
# PARSER DIAGNOSTICS
# ============================================================

def build_parser_diagnostics(
    parsed_data: dict,
    cleaned_text: str,
) -> dict:

    personal = parsed_data.get(
        "personal",
        {},
    )

    warnings = []

    if not personal.get("name"):
        warnings.append(
            "Name could not be confidently detected."
        )

    if not personal.get("email"):
        warnings.append(
            "Email address was not detected."
        )

    if not parsed_data.get("skills"):
        warnings.append(
            "No technical skills were detected."
        )

    if not parsed_data.get("education"):
        warnings.append(
            "Education section could not be extracted."
        )

    if not parsed_data.get("experience"):
        warnings.append(
            "No experience entries were detected."
        )

    if not parsed_data.get("projects"):
        warnings.append(
            "No project entries were detected."
        )

    return {
        "parser_version": PARSER_VERSION,
        "text_length": len(cleaned_text),
        "sections_detected": [
            key
            for key in (
                "summary",
                "skills",
                "experience",
                "projects",
                "education",
                "certifications",
                "languages",
            )
            if parsed_data.get(key)
        ],
        "warnings": warnings[:10],
    }


# ============================================================
# PARSED DATA VALIDATION
# ============================================================

def validate_parsed_data(
    data: dict,
) -> dict:

    personal = data.get(
        "personal",
        {},
    )

    # Personal.
    if personal.get("name"):
        personal["name"] = clean_value(
            personal["name"]
        )

    if personal.get("email"):
        personal["email"] = clean_value(
            personal["email"]
        )

    if personal.get("phone"):
        personal["phone"] = normalize_phone(
            personal["phone"]
        )

    invalid_names = {
        "api",
        "skills",
        "summary",
        "projects",
        "experience",
        "education",
        "certifications",
        "languages",
        "technical skills",
    }

    name = personal.get("name")

    if (
        name
        and name.casefold()
        in invalid_names
    ):
        personal["name"] = None

    data["personal"] = personal

    # Lists.
    data["skills"] = clean_list(
        data.get("skills", [])
    )

    data["ai_tools"] = clean_list(
        data.get("ai_tools", [])
    )

    data["languages"] = clean_list(
        data.get("languages", [])
    )

    data["certifications"] = clean_list(
        data.get("certifications", [])
    )

    # Summary.
    if data.get("summary"):
        data["summary"] = clean_value(
            data["summary"]
        )

    # Projects.
    cleaned_projects = []

    for project in data.get(
        "projects",
        [],
    ):
        finalized = finalize_project(
            project
        )

        if finalized:
            cleaned_projects.append(
                finalized
            )

    data["projects"] = cleaned_projects[
        :MAX_PROJECT_ENTRIES
    ]

    # Education.
    data["education"] = (
        data.get("education") or []
    )[:MAX_EDUCATION_ENTRIES]

    # Experience.
    data["experience"] = (
        data.get("experience") or []
    )[:MAX_EXPERIENCE_ENTRIES]

    return data


# ============================================================
# BUILD PARSED DATA
# ============================================================

def build_parsed_data(
    text: str,
) -> dict:

    cleaned_text = clean_text(text)

    sections = split_sections(
        cleaned_text
    )

    header_lines = sections.get(
        "header",
        [],
    )

    summary_lines = sections.get(
        "summary",
        [],
    )

    skills_lines = sections.get(
        "skills",
        [],
    )

    projects_lines = sections.get(
        "projects",
        [],
    )

    experience_lines = sections.get(
        "experience",
        [],
    )

    education_lines = sections.get(
        "education",
        [],
    )

    certifications_lines = sections.get(
        "certifications",
        [],
    )

    languages_lines = sections.get(
        "languages",
        [],
    )

    # NOTE: joined with a space, not "\n". extract_skills()/extract_ai_tools()
    # match multi-word vocabulary entries (e.g. "machine learning",
    # "object oriented programming") as a literal phrase with an internal
    # space. PDF extraction frequently wraps such phrases across two lines,
    # so newline-joining this fallback text would silently prevent those
    # phrases from ever matching here (they'd only be caught if they also
    # happened to appear, unwrapped, inside a dedicated Skills/Projects/
    # Experience section, where sections_text() already joins with spaces).
    full_text = " ".join(
        line
        for section_lines in sections.values()
        for line in section_lines
    )

    parsed_data = {
        "skills": extract_skills(
            text=full_text,
            skills_section_text=sections_text(
                skills_lines
            ),
            projects_text=sections_text(
                projects_lines
            ),
            experience_text=sections_text(
                experience_lines
            ),
        ),

        "summary": extract_summary(
            summary_lines
        ),

        "ai_tools": extract_ai_tools(
            full_text
        ),

        "personal": {
            "name": extract_header_name(
                header_lines
            ),
            "email": extract_email(
                cleaned_text
            ),
            "phone": normalize_phone(
                extract_phone(
                    cleaned_text
                )
            ),
            "linkedin": extract_link(
                cleaned_text,
                "LinkedIn",
            ),
            "github": extract_link(
                cleaned_text,
                "GitHub",
            ),
            "portfolio": extract_link(
                cleaned_text,
                "Portfolio",
            ),
        },

        "projects": extract_projects(
            projects_lines
        ),

        "education": extract_education(
            education_lines
        ),

        "experience": extract_experience(
            experience_lines
        ),

        "certifications": extract_certifications(
            certifications_lines
        ),

        "languages": extract_languages(
            languages_lines
        ),
    }

    parsed_data = validate_parsed_data(
        parsed_data
    )

    parsed_data["diagnostics"] = (
        build_parser_diagnostics(
            parsed_data,
            cleaned_text,
        )
    )

    return parsed_data


# ============================================================
# PARSING FAILURE HANDLING
# ============================================================

def mark_parsing_failed(
    db: Session,
    resume_id: int,
    error_message: str,
) -> None:

    try:
        result = (
            db.query(
                models.ResumeParsingResult
            )
            .filter(
                models.ResumeParsingResult.resume_id
                == resume_id
            )
            .first()
        )

        if result is None:
            return

        result.status = "Failed"

        result.error_message = str(
            error_message
        )[:1000]

        result.parser_version = (
            PARSER_VERSION
        )

        db.commit()

    except Exception:
        db.rollback()


# ============================================================
# MAIN PARSER
# ============================================================

def parse_resume(
    db: Session,
    resume_id: int,
    user_id: int,
):
    resume = (
        db.query(models.Resume)
        .filter(
            models.Resume.id == resume_id,
            models.Resume.user_id == user_id,
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    parsing_result = None

    try:

        # ----------------------------------------------------
        # GET OR CREATE PARSING RESULT
        # ----------------------------------------------------

        parsing_result = (
            db.query(
                models.ResumeParsingResult
            )
            .filter(
                models.ResumeParsingResult.resume_id
                == resume.id
            )
            .first()
        )

        if parsing_result is None:

            parsing_result = (
                models.ResumeParsingResult(
                    resume_id=resume.id,
                    status="Processing",
                    parser_version=PARSER_VERSION,
                )
            )

            db.add(parsing_result)

        else:

            parsing_result.status = "Processing"

            parsing_result.error_message = None

            parsing_result.parser_version = (
                PARSER_VERSION
            )

        db.commit()

        db.refresh(
            parsing_result
        )

        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        raw_text = extract_resume_text(
            resume
        )

        # ----------------------------------------------------
        # CLEAN + VALIDATE TEXT
        # ----------------------------------------------------

        cleaned_text = validate_extracted_text(
            raw_text
        )

        # ----------------------------------------------------
        # PARSE
        # ----------------------------------------------------

        parsed_data = build_parsed_data(
            cleaned_text
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        parsing_result.extracted_text = (
            cleaned_text
        )

        parsing_result.parsed_data = (
            parsed_data
        )

        parsing_result.status = "Completed"

        parsing_result.error_message = None

        parsing_result.parser_version = (
            PARSER_VERSION
        )

        db.commit()

        db.refresh(
            parsing_result
        )

        return parsing_result

    except HTTPException as exc:

        db.rollback()

        mark_parsing_failed(
            db,
            resume_id,
            exc.detail,
        )

        raise

    except SQLAlchemyError:

        db.rollback()

        mark_parsing_failed(
            db,
            resume_id,
            "Failed to save resume parsing result",
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to save resume parsing result",
        )

    except Exception as exc:

        db.rollback()

        mark_parsing_failed(
            db,
            resume_id,
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to parse resume",
        )

