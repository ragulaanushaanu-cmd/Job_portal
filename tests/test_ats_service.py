import pytest
from services import ats_service


# ============================================================
# Generic keyword meaningfulness tests
# ============================================================

@pytest.mark.parametrize(
    "keyword, expected",
    [
        ("service", False),
        ("services", False),
        ("database", False),
        ("databases", False),
        ("application", False),
        ("applications", False),
        ("system", False),
        ("systems", False),
        ("experience", False),
        ("candidate", False),
        ("candidates", False),

        # Meaningful multi-word keywords
        ("backend developer", True),
        ("database integration", True),
        ("cloud deployment", True),
    ],
)
def test_keyword_meaningfulness(keyword, expected):
    result = ats_service._keyword_is_meaningful(keyword)

    assert result == expected, (
        f"_keyword_is_meaningful({keyword!r}) -> "
        f"expected={expected}, got={result}"
    )


# ============================================================
# Skill canonicalization - set level
# ============================================================

@pytest.mark.parametrize(
    "values, expected",
    [
        (
            {
                "AWS",
                "AWS Cloud",
                "Amazon AWS",
                "Amazon Web Services",
            },
            {"aws"},
        ),
        (
            {
                "Postgres",
                "PostgreSQL",
                "Postgres DB",
                "PostgreSQL Database",
            },
            {"postgresql"},
        ),
        (
            {
                "REST API",
                "REST APIs",
                "RESTful API",
                "REST-API",
            },
            {"rest api"},
        ),
    ],
)
def test_skill_canonicalization_set(values, expected):
    result = ats_service._canonicalize_skill_set(values)

    assert result == expected, (
        f"_canonicalize_skill_set({values!r}) -> "
        f"expected={expected}, got={result}"
    )


# ============================================================
# Individual skill canonicalization
# ============================================================

@pytest.mark.parametrize(
    "value, expected",
    [
        # Python
        ("Python", "python"),
        ("python", "python"),
        ("PYTHON", "python"),
        ("Python 3", "python"),
        ("Python 3.9", "python"),
        ("Python 3.10", "python"),
        ("Python 3.11", "python"),
        ("Python 3.12", "python"),
        ("Python 3.13", "python"),
        ("Python v3.13", "python"),

        # FastAPI
        ("FastAPI", "fastapi"),
        ("Fast API", "fastapi"),
        ("fast api", "fastapi"),
        ("FASTAPI", "fastapi"),
        ("Fast-API", "fastapi"),

        # PostgreSQL
        ("Postgres", "postgresql"),
        ("PostgreSQL", "postgresql"),
        ("postgres", "postgresql"),
        ("Postgres DB", "postgresql"),
        ("Postgres Database", "postgresql"),
        ("PostgreSQL DB", "postgresql"),
        ("PostgreSQL Database", "postgresql"),

        # MongoDB
        ("MongoDB", "mongodb"),
        ("Mongo DB", "mongodb"),
        ("mongo db", "mongodb"),
        ("Mongo Database", "mongodb"),

        # REST API
        ("REST API", "rest api"),
        ("REST APIs", "rest api"),
        ("RESTful API", "rest api"),
        ("RESTful APIs", "rest api"),
        ("REST-API", "rest api"),

        # Node.js
        ("Node JS", "node.js"),
        ("Node.js", "node.js"),
        ("nodejs", "node.js"),
        ("NODE JS", "node.js"),

        # AWS
        ("AWS", "aws"),
        ("AWS Cloud", "aws"),
        ("Amazon AWS", "aws"),
        ("Amazon Web Services", "aws"),
        ("Amazon Web Services Cloud", "aws"),
    ],
)
def test_skill_canonicalization_variants(value, expected):
    result = ats_service._canonical_skill(value)

    assert result == expected, (
        f"_canonical_skill({value!r}) -> "
        f"expected={expected!r}, got={result!r}"
    )


# ============================================================
# Experience requirement extraction
# ============================================================

@pytest.mark.parametrize(
    "job_text, expected",
    [
        # Mandatory
        ("2 years of experience required", 2.0),
        ("Minimum 3 years experience", 3.0),
        ("At least 4 years of experience", 4.0),
        ("5 years required", 5.0),
        ("5 years mandatory", 5.0),
        ("5 years essential", 5.0),

        # Decimal
        ("2.5 years of experience required", 2.5),
        ("Minimum 2.5 years experience", 2.5),

        # Plus
        ("3+ years of relevant experience", 3.0),
        ("2+ yrs experience", 2.0),
        ("At least 4+ years", 4.0),

        # Preferred / non-mandatory
        ("5 years preferred", None),
        ("5 years desired", None),
        ("5 years desirable", None),
        ("5 years optional", None),
        ("5 years advantageous", None),
        ("3 years of experience preferred", None),
        ("3 years of relevant experience preferred", None),
        ("5+ years experience desired", None),

        # Important regressions
        ("minimum 5 years preferred", None),
        ("minimum 5 years desired", None),
        ("at least 5 years preferred", None),

        # Numbers that are not job experience
        ("Company was founded 5 years ago", None),
        ("The company has been operating for 10 years", None),
        ("10 years in business", None),
    ],
)
def test_required_experience_years(job_text, expected):
    result = ats_service._required_experience_years(job_text)

    assert result == expected, (
        f"_required_experience_years({job_text!r}) -> "
        f"expected={expected}, got={result}"
    )


# ============================================================
# Education requirement extraction
# ============================================================

@pytest.mark.parametrize(
    "job_text, expected",
    [
        ("Bachelor's degree required", 3),
        ("Bachelor's degree required, Master's preferred", 3),
        ("Master's degree preferred", None),

        ("Bachelor's or Master's degree required", 3),
        ("Bachelor's and Master's degrees required", 4),

        ("Bachelor's required and Master's preferred", 3),
        ("Bachelor's preferred and Master's required", 4),

        ("Master's required and PhD preferred", 4),
        ("Bachelor's preferred or Master's required", 4),

        ("PhD required", 5),

        # B.Tech
        ("B.Tech required", 3),
        ("B Tech required", 3),
        ("BTech required", 3),
        ("B-Tech required", 3),
        ("B/Tech required", 3),

        # M.Tech
        ("M.Tech required", 4),
        ("M Tech required", 4),
        ("MTech required", 4),

        # Preferred only
        ("Bachelor's degree preferred", None),
        ("Bachelor's degree desired", None),
        ("PhD preferred", None),

        # Qualifier regressions
        (
            "Bachelor's degree required, Master's degree preferred",
            3,
        ),
        (
            "Bachelor's degree preferred, Master's degree required",
            4,
        ),
    ],
)
def test_required_education_level(job_text, expected):
    result = ats_service._required_education_level(job_text)

    assert result == expected, (
        f"_required_education_level({job_text!r}) -> "
        f"expected={expected}, got={result}"
    )


# ============================================================
# Mixed education qualifier regressions
# ============================================================

@pytest.mark.parametrize(
    "job_text, expected",
    [
        (
            "Bachelor's degree preferred. Master's degree required",
            4,
        ),
        (
            "Bachelor's degree required. Master's degree preferred",
            3,
        ),
        (
            "Bachelor's degree preferred. PhD required",
            5,
        ),
        (
            "Bachelor's degree required. PhD preferred",
            3,
        ),
        (
            "Bachelor's degree preferred, Master's degree required",
            4,
        ),
        (
            "Bachelor's degree required, Master's degree preferred",
            3,
        ),
        (
            "Bachelor's preferred. Master's preferred. PhD required",
            5,
        ),
        (
            "Bachelor's required. Master's preferred. PhD preferred",
            3,
        ),
    ],
)
def test_required_education_level_mixed_qualifiers(
    job_text,
    expected,
):
    result = ats_service._required_education_level(job_text)

    assert result == expected, (
        f"Mixed education requirement failed for {job_text!r}: "
        f"expected={expected}, got={result}"
    )


# ============================================================
# Education score - hierarchy
# ============================================================

@pytest.mark.parametrize(
    "parsed_data, job_text, expected",
    [
        (
            {"education": "B.Tech Computer Science"},
            "Bachelor's degree required",
            "100.00",
        ),
        (
            {"education": "M.Tech Computer Science"},
            "Bachelor's degree required",
            "100.00",
        ),
        (
            {"education": "B.Tech Computer Science"},
            "Master's degree required",
            "0.00",
        ),
        (
            {"education": "M.Tech Computer Science"},
            "Master's degree required",
            "100.00",
        ),
    ],
)
def test_education_score_hierarchy(
    parsed_data,
    job_text,
    expected,
):
    result = ats_service._calculate_education_score(
        parsed_data=parsed_data,
        resume_text="",
        job_text=job_text,
    )

    assert result == ats_service.Decimal(expected), (
        f"Education score failed: "
        f"resume={parsed_data!r}, "
        f"job={job_text!r}, "
        f"expected={expected}, "
        f"got={result}"
    )


# ============================================================
# Education field matching
# ============================================================

@pytest.mark.parametrize(
    "parsed_data, job_text, expected",
    [
        (
            {"education": "B.Tech Computer Science"},
            "Bachelor's degree in Computer Science required",
            "100.00",
        ),
        (
            {"education": "B.Tech Computer Science"},
            "Bachelor's degree in Mechanical Engineering required",
            "60.00",
        ),
        (
            {"education": "B.Tech Computer Science"},
            "Bachelor's degree required",
            "100.00",
        ),
    ],
)
def test_education_field_matching(
    parsed_data,
    job_text,
    expected,
):
    result = ats_service._calculate_education_score(
        parsed_data=parsed_data,
        resume_text="",
        job_text=job_text,
    )

    assert result == ats_service.Decimal(expected), (
        f"Education field matching failed: "
        f"expected={expected}, got={result}"
    )


# ============================================================
# Keyword quality regression
# ============================================================

def test_keyword_quality_rejects_generic_words():
    job_text = """
    We are looking for a Backend Developer.

    The candidate should have experience building REST services,
    web applications and backend systems.

    Required skills include Python and FastAPI.

    Experience with database management and database integration
    is preferred.
    """

    keywords = ats_service._extract_keyword_candidates(
        job_text,
        job_skills={
            "Python",
            "FastAPI",
        },
    )

    generic_keywords = {
        "service",
        "services",
        "database",
        "databases",
        "application",
        "applications",
        "system",
        "systems",
        "experience",
        "candidate",
        "candidates",
    }

    leaked = generic_keywords.intersection(keywords)

    assert not leaked, (
        "Generic keywords leaked into extraction: "
        f"{sorted(leaked)}"
    )


def test_keyword_quality_extracts_meaningful_phrases():
    job_text = """
    We are looking for a Backend Developer.

    The candidate should have experience building REST services,
    web applications and backend systems.

    Required skills include Python and FastAPI.

    Experience with database management and database integration
    is preferred.
    """

    keywords = ats_service._extract_keyword_candidates(
        job_text,
        job_skills={
            "Python",
            "FastAPI",
        },
    )

    assert "backend developer" in keywords
    assert "database integration" in keywords


# ============================================================
# Job 15 keyword extraction regression
# ============================================================

JOB_15_TEXT = """
We are seeking a Backend Developer with experience building
RESTful API services and REST APIs using Python 3 and Fast API.
The ideal candidate has experience working with relational
databases like Postgres and deploying applications on AWS Cloud.
"""


JOB_15_SKILLS = {
    "restful api",
    "rest apis",
    "rest api",
    "postgresql",
    "postgres",
    "fast api",
    "python 3",
    "aws cloud",
}


def test_job_15_keyword_extraction():
    keywords = ats_service._extract_keyword_candidates(
        JOB_15_TEXT,
        job_skills=JOB_15_SKILLS,
    )

    # These are the meaningful non-skill phrases that the
    # current extractor is expected to identify.
    expected_keywords = {
        "backend developer",
        "relational database",
    }

    for keyword in expected_keywords:
        assert keyword in keywords, (
            f"Job 15 keyword extraction failed: "
            f"expected {keyword!r}, got {sorted(keywords)}"
        )


def test_job_15_does_not_leak_technical_skills():
    keywords = ats_service._extract_keyword_candidates(
        JOB_15_TEXT,
        job_skills=JOB_15_SKILLS,
    )

    technical_skills = {
        "python",
        "fastapi",
        "rest api",
        "postgresql",
        "aws",
    }

    leaked = technical_skills.intersection(keywords)

    assert not leaked, (
        "Technical skill leaked into ordinary keyword extraction: "
        f"{sorted(leaked)}"
    )


def test_job_15_does_not_extract_generic_words():
    keywords = ats_service._extract_keyword_candidates(
        JOB_15_TEXT,
        job_skills=JOB_15_SKILLS,
    )

    generic_keywords = {
        "service",
        "services",
        "database",
        "databases",
        "application",
        "applications",
        "experience",
        "candidate",
        "systems",
        "system",
    }

    leaked = generic_keywords.intersection(keywords)

    assert not leaked, (
        "Generic keyword leaked into Job 15 extraction: "
        f"{sorted(leaked)}"
    )


# ============================================================
# Keyword phrase normalization / alias regression
# ============================================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ("relational database", "relational database"),
        ("relational databases", "relational database"),
        ("cloud deployment", "cloud deployment"),
        ("cloud deployments", "cloud deployment"),
        ("problem-solving", "problem solving"),
        ("problem solving", "problem solving"),
    ],
)
def test_keyword_alias_lookup(text, expected):
    cleaned = ats_service._clean_keyword(text)

    result = ats_service._keyword_alias_lookup(cleaned)

    assert result == expected, (
        f"Keyword alias lookup failed: "
        f"{text!r} -> expected={expected!r}, got={result!r}"
    )


# ============================================================
# ATS recommendation tests
# ============================================================


def test_recommendations_missing_skills():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("60.00"),
        experience_score=ats_service.Decimal("100.00"),
        education_score=ats_service.Decimal("100.00"),
        keyword_score=ats_service.Decimal("90.00"),
        overall_score=ats_service.Decimal("80.00"),
        missing_skills=[
            "Postgres",
            "PostgreSQL",
            "AWS Cloud",
        ],
        missing_keywords=[],
    )

    assert any(
        "postgresql" in recommendation.lower()
        for recommendation in recommendations
    )

    assert any(
        "aws" in recommendation.lower()
        for recommendation in recommendations
    )


def test_recommendations_missing_keywords():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("100.00"),
        experience_score=ats_service.Decimal("100.00"),
        education_score=ats_service.Decimal("100.00"),
        keyword_score=ats_service.Decimal("60.00"),
        overall_score=ats_service.Decimal("80.00"),
        missing_skills=[],
        missing_keywords=[
            "database integrations",
            "cloud deployments",
        ],
    )

    assert any(
        "database integration" in recommendation.lower()
        for recommendation in recommendations
    )

    assert any(
        "cloud deployment" in recommendation.lower()
        for recommendation in recommendations
    )


def test_recommendations_education_gap():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("100.00"),
        experience_score=ats_service.Decimal("100.00"),
        education_score=ats_service.Decimal("0.00"),
        keyword_score=ats_service.Decimal("100.00"),
        overall_score=ats_service.Decimal("80.00"),
        missing_skills=[],
        missing_keywords=[],
    )

    assert any(
        "education" in recommendation.lower()
        and "mandatory" in recommendation.lower()
        for recommendation in recommendations
    )


def test_recommendations_education_field_gap():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("100.00"),
        experience_score=ats_service.Decimal("100.00"),
        education_score=ats_service.Decimal("60.00"),
        keyword_score=ats_service.Decimal("100.00"),
        overall_score=ats_service.Decimal("90.00"),
        missing_skills=[],
        missing_keywords=[],
    )

    assert any(
        "education" in recommendation.lower()
        and (
            "field" in recommendation.lower()
            or "specialization" in recommendation.lower()
        )
        for recommendation in recommendations
    )


def test_recommendations_experience_gap():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("100.00"),
        experience_score=ats_service.Decimal("40.00"),
        education_score=ats_service.Decimal("100.00"),
        keyword_score=ats_service.Decimal("100.00"),
        overall_score=ats_service.Decimal("80.00"),
        missing_skills=[],
        missing_keywords=[],
    )

    assert any(
        "experience" in recommendation.lower()
        for recommendation in recommendations
    )


def test_recommendations_no_false_skill_gap():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("100.00"),
        experience_score=ats_service.Decimal("100.00"),
        education_score=ats_service.Decimal("100.00"),
        keyword_score=ats_service.Decimal("100.00"),
        overall_score=ats_service.Decimal("95.00"),
        missing_skills=[],
        missing_keywords=[],
    )

    assert len(recommendations) == 1

    assert (
        "no major ats improvements"
        in recommendations[0].lower()
    )


def test_recommendations_are_unique():
    recommendations = ats_service._build_recommendations(
        skill_score=ats_service.Decimal("60.00"),
        experience_score=ats_service.Decimal("60.00"),
        education_score=ats_service.Decimal("60.00"),
        keyword_score=ats_service.Decimal("60.00"),
        overall_score=ats_service.Decimal("60.00"),
        missing_skills=[
            "Python",
            "python",
            "PYTHON",
        ],
        missing_keywords=[
            "Database Integrations",
            "database integration",
        ],
    )

    assert len(recommendations) == len(
        set(recommendations)
    )

# # ============================================================
# # Project relevance - ATS keyword matching
# # ============================================================

# def test_project_relevance_uses_ats_keywords():
#     project_text = """
#     Built a backend developer project for database integration
#     and cloud deployment.
#     """

#     job_skills = {
#         "Python",
#     }

#     job_keywords = {
#         "backend developer",
#         "database integration",
#         "cloud deployment",
#     }

#     score = ats_service._calculate_project_relevance(
#         project_text=project_text,
#         job_skills=job_skills,
#         job_keywords=job_keywords,
#     )

#     assert score > ats_service.Decimal("0.00")

# ============================================================
# Project relevance - ATS keyword matching
# ============================================================

def test_project_keyword_relevance_matches_ats_keywords():
    project_text = """
    Built a backend developer project with database integration
    and cloud deployment capabilities.
    """

    ats_keywords = [
        "backend developer",
        "database integration",
        "cloud deployment",
    ]

    score = ats_service._project_keyword_relevance(
        project_text=project_text,
        ats_keywords=ats_keywords,
    )

    assert score == ats_service.Decimal("100.00")

def test_project_keyword_relevance_ignores_unmatched_ats_keywords():
    project_text = """
    Built a backend developer project with database integration.
    """

    ats_keywords = [
        "backend developer",
        "database integration",
        "cloud deployment",
    ]

    score = ats_service._project_keyword_relevance(
        project_text=project_text,
        ats_keywords=ats_keywords,
    )

    assert score == ats_service.Decimal("66.67")


def test_project_keyword_relevance_normalizes_keyword_aliases():
    project_text = """
    Developed a backend application involving relational databases
    and cloud deployments.
    """

    ats_keywords = [
        "relational databases",
        "cloud deployments",
    ]

    score = ats_service._project_keyword_relevance(
        project_text=project_text,
        ats_keywords=ats_keywords,
    )

    assert score == ats_service.Decimal("100.00")

def test_project_keyword_relevance_empty_input():
    assert (
        ats_service._project_keyword_relevance(
            project_text="",
            ats_keywords=["backend developer"],
        )
        == ats_service.Decimal("0.00")
    )

    assert (
        ats_service._project_keyword_relevance(
            project_text="backend developer project",
            ats_keywords=[],
        )
        == ats_service.Decimal("0.00")
    )

# ============================================================
# Normalized keyword matching - singular/plural
# ============================================================

@pytest.mark.parametrize(
    "text, term",
    [
        (
            "Developed a backend application involving relational databases.",
            "relational database",
        ),
        (
            "Worked with cloud deployments.",
            "cloud deployment",
        ),
        (
            "Implemented database integrations.",
            "database integration",
        ),
        (
            "Built several backend applications.",
            "backend application",
        ),
    ],
)
def test_contains_normalized_term_matches_plural_forms(
    text,
    term,
):
    assert ats_service._contains_normalized_term(
        text,
        term,
    ) is True

@pytest.mark.parametrize(
    "text, term",
    [
        (
            "Worked with relational database technology.",
            "relational databases",
        ),
        (
            "Worked on cloud deployment.",
            "cloud deployments",
        ),
    ],
)
def test_contains_normalized_term_matches_singular_forms(
    text,
    term,
):
    assert ats_service._contains_normalized_term(
        text,
        term,
    ) is True


# ============================================================
# Project keyword relevance scoring
# ============================================================

@pytest.mark.parametrize(
    "project_text, ats_keywords, expected",
    [
        # All keywords matched
        (
            """
            Built a backend application using Python
            and FastAPI with database integration.
            """,
            [
                "python",
                "fastapi",
                "database integration",
            ],
            "100.00",
        ),

        # Two of three keywords matched
        (
            """
            Built a backend application using Python
            and FastAPI.
            """,
            [
                "python",
                "fastapi",
                "database integration",
            ],
            "66.67",
        ),

        # One of two keywords matched
        (
            """
            Built a backend application using Python.
            """,
            [
                "python",
                "cloud deployment",
            ],
            "50.00",
        ),

        # No keywords matched
        (
            """
            Built a frontend application using HTML and CSS.
            """,
            [
                "python",
                "cloud deployment",
            ],
            "0.00",
        ),

        # Empty project text
        (
            "",
            [
                "python",
                "fastapi",
            ],
            "0.00",
        ),

        # Empty ATS keywords
        (
            "Built a backend application using Python.",
            [],
            "0.00",
        ),
    ],
)
def test_project_keyword_relevance_scoring(
    project_text,
    ats_keywords,
    expected,
):
    score = ats_service._project_keyword_relevance(
        project_text=project_text,
        ats_keywords=ats_keywords,
    )

    assert score == ats_service.Decimal(expected), (
        "Project keyword relevance score failed: "
        f"project={project_text!r}, "
        f"keywords={ats_keywords!r}, "
        f"expected={expected}, "
        f"got={score}"
    )

# ============================================================
# Project keyword relevance - duplicate canonical keywords
# ============================================================

def test_project_keyword_relevance_deduplicates_aliases():
    project_text = """
    Developed backend systems involving relational databases
    and cloud deployment.
    """

    ats_keywords = [
        "relational database",
        "relational databases",
        "cloud deployment",
        "cloud deployments",
    ]

    score = ats_service._project_keyword_relevance(
        project_text=project_text,
        ats_keywords=ats_keywords,
    )

    assert score == ats_service.Decimal("100.00"), (
        "Duplicate keyword aliases should not inflate "
        f"the denominator. Got {score}"
    )


def test_project_keyword_relevance_deduplicates_aliases_when_partially_matched():
    project_text = """
    Developed backend systems involving relational databases.
    """

    ats_keywords = [
        "relational database",
        "relational databases",
        "cloud deployment",
        "cloud deployments",
    ]

    score = ats_service._project_keyword_relevance(
        project_text=project_text,
        ats_keywords=ats_keywords,
    )

    assert score == ats_service.Decimal("50.00"), (
        "Canonical aliases should count as one keyword. "
        f"Expected 50.00, got {score}"
    )

def test_analyze_resume_against_job_creates_analysis(
    db_session,
    candidate_user,
    resume,
    job,
):
    result = ats_service.analyze_resume_against_job(
        db=db_session,
        resume_id=resume.id,
        job_id=job.id,
        current_user=candidate_user,
    )

    assert result is not None
    assert result.id is not None

    assert result.resume_id == resume.id
    assert result.job_id == job.id

    assert result.overall_score is not None
    assert result.skill_score is not None
    assert result.experience_score is not None
    assert result.education_score is not None
    assert result.keyword_score is not None

    assert isinstance(result.matched_skills, list)
    assert isinstance(result.missing_skills, list)
    assert isinstance(result.matched_keywords, list)
    assert isinstance(result.missing_keywords, list)
    assert isinstance(result.recommendations, list)