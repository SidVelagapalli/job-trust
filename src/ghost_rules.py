"""Ghost-job risk score: hand-written RULES, not machine learning.

A ghost job is a real company advertising a role it isn't actively trying to fill.
Our dataset only labels scams, never ghost jobs, and has no posting dates or repost
history, so there is nothing to train a model on. These rules are common-sense warning
signs; the points are judgement calls, not learned or validated weights.
"""

SHORT_DESCRIPTION_WORDS = 80
STALE_AFTER_DAYS = 30

# Phrases suggesting the company is collecting applicants rather than filling a current opening.
EVERGREEN_PHRASES = [
    "always hiring",
    "talent pool",
    "talent community",
    "future opportunities",
    "future openings",
]

# Points per rule; they add up to 100.
POINTS = {
    "no_salary": 15,          # weak alone: most postings omit salary
    "short_description": 15,
    "evergreen_phrase": 25,   # the posting itself admits there may be no current opening
    "stale_posting": 25,
    "seen_before": 20,
}


def ghost_score(
    *,
    description: str,
    salary_range: str | None = None,
    other_text: str = "",
    days_since_posted: int | None = None,
    seen_before: bool | None = None,
) -> dict:
    """Return {"score": 0-100, "reasons": [...], "method": "rules"}.

    other_text: any other posting text (title, company profile, ...) to search for phrases.
    days_since_posted / seen_before are optional user answers; None means "not provided"
    and those rules simply don't fire.
    """
    reasons = []

    def fire(rule: str, message: str) -> None:
        reasons.append({"rule": rule, "points": POINTS[rule], "detail": message})

    if salary_range is None or salary_range.strip() == "":
        fire("no_salary", "No salary listed")

    word_count = len((description or "").split())
    if word_count < SHORT_DESCRIPTION_WORDS:
        fire("short_description", f"Description is only {word_count} words (under {SHORT_DESCRIPTION_WORDS})")

    searchable = f"{description or ''} {other_text}".lower()
    found = [p for p in EVERGREEN_PHRASES if p in searchable]
    if found:
        fire("evergreen_phrase", "Mentions " + ", ".join(f'"{p}"' for p in found))

    if days_since_posted is not None and days_since_posted > STALE_AFTER_DAYS:
        fire("stale_posting", f"Posted {days_since_posted} days ago (over {STALE_AFTER_DAYS})")

    if seen_before:
        fire("seen_before", "You've seen this posting before")

    return {
        "score": sum(r["points"] for r in reasons),
        "reasons": reasons,
        "method": "rules",
    }
