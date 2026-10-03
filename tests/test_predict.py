import pytest

from src.ghost_rules import ghost_score
from src.predict import SCAM_THRESHOLD, score_posting

OBVIOUS_SCAM = dict(
    title="Data Entry Clerk - Work From Home - Earn $500 Weekly",
    description=(
        "Earn $500 to $1,000 weekly working from home! No experience needed. "
        "We are looking for data entry clerks and administrative assistants to start immediately. "
        "Flexible hours, work from the comfort of your home with your own computer. "
        "Get paid weekly by wire transfer. To apply, click the link below and send your "
        "full name, address, phone number and bank details so we can set up your payment."
    ),
    requirements="Must have a computer and internet access. No experience necessary.",
    benefits="Weekly pay, work from home, flexible schedule.",
    salary_range="500-1000",
    has_company_logo=False,
    has_questions=False,
    telecommuting=True,
)

OBVIOUS_REAL_INTERNSHIP = dict(
    title="Marketing Intern",
    company_profile=(
        "We're a fast-growing software company in New York building tools that help small "
        "businesses manage their customers. Our team of 60 engineers, designers and marketers "
        "values curiosity, ownership and clear communication."
    ),
    description=(
        "Our marketing team is looking for a summer intern to help with content, social media "
        "and campaign analysis. You'll work closely with our content marketing manager to write "
        "blog posts, plan our social calendar, and measure how our campaigns perform. "
        "You'll present a project to the wider team at the end of the summer."
    ),
    requirements=(
        "Currently pursuing a bachelor's degree in marketing, communications or a related field. "
        "Strong writing skills and familiarity with social media platforms. "
        "Experience with Google Analytics is a plus."
    ),
    benefits="Paid internship, mentorship from our marketing team, and lunch every Friday.",
    has_company_logo=True,
    has_questions=True,
    telecommuting=False,
)


def test_obvious_scam_is_flagged():
    result = score_posting(**OBVIOUS_SCAM)
    assert result["probability"] > SCAM_THRESHOLD
    assert result["flagged"] is True


def test_obvious_real_internship_is_not_flagged():
    result = score_posting(**OBVIOUS_REAL_INTERNSHIP)
    assert result["probability"] < SCAM_THRESHOLD
    assert result["flagged"] is False


def test_missing_logo_raises_score_and_is_a_reason():
    with_logo = score_posting(**{**OBVIOUS_REAL_INTERNSHIP, "has_company_logo": True})
    without_logo = score_posting(**{**OBVIOUS_REAL_INTERNSHIP, "has_company_logo": False})

    assert without_logo["probability"] > with_logo["probability"]
    assert "no company logo" in [reason["label"] for reason in without_logo["reasons"]]


def test_empty_description_gives_clear_error():
    with pytest.raises(ValueError, match="description is required"):
        score_posting(title="Marketing Intern", description="   ")


def test_ghost_score_is_zero_when_no_rules_fire():
    long_description = " ".join(["Build and test features for our web application."] * 15)  # 105 words
    result = ghost_score(
        description=long_description,
        salary_range="60000-70000",
        days_since_posted=5,
        seen_before=False,
    )
    assert result["score"] == 0
    assert result["reasons"] == []
