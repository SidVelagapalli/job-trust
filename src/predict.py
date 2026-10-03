"""Score a job posting for scam risk using the trained model (job_trust_v1).

The model is a TF-IDF + logistic regression pipeline trained in notebooks/03_improve.ipynb.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "job_trust_v1.joblib"

# Probability at or above which a posting is flagged as a likely scam.
# Chosen in notebook 03 (step 6) from cross-validated predictions on the TRAINING set only:
# at 0.4 the model caught ~86% of scams while ~2 of every 3 flags were genuine scams.
# We lean toward catching scams because a missed scam costs a job seeker more than a false alarm.
SCAM_THRESHOLD = 0.4

TEXT_FIELDS = ["title", "company_profile", "description", "requirements", "benefits"]
TOP_N_REASONS = 5

# Smallest contribution (in the model's log-odds units) worth showing as a reason.
# 0.2 multiplies the odds of "scam" by about 1.22, i.e. each listed reason raises them by ~22%+.
# Checked on TRAINING postings: 98% of individual word pushes fall below 0.2, yet a typical fake
# posting still has ~7 reasons above it (enough to fill 5 slots) while a typical real one has ~2.
# Lower cutoffs let filler words like "and" through; higher ones leave fakes with too few reasons.
MIN_REASON_CONTRIBUTION = 0.2

# Readable labels for each yes/no feature: (label when 0, label when 1).
METADATA_LABELS = {
    "has_company_logo": ("no company logo", "has company logo"),
    "has_questions": ("no screening questions", "has screening questions"),
    "telecommuting": ("not remote", "remote job"),
    "salary_listed": ("no salary listed", "salary listed"),
    "has_company_profile": ("no company profile", "has company profile"),
}


def load_model(path: Path = MODEL_PATH) -> dict:
    """Load the saved model bundle and check it agrees with this file's threshold."""
    bundle = joblib.load(path)
    # The notebook saved the threshold inside the file too; if someone retrains with a
    # different threshold, fail loudly rather than silently using the wrong one.
    if bundle["threshold"] != SCAM_THRESHOLD:
        raise ValueError(
            f"Model file threshold ({bundle['threshold']}) does not match "
            f"SCAM_THRESHOLD ({SCAM_THRESHOLD}) in predict.py"
        )
    return bundle


@lru_cache(maxsize=1)
def _default_model() -> dict:
    # Cached so calling score_posting() repeatedly only reads the file once.
    return load_model()


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _build_row(fields: dict) -> pd.DataFrame:
    """Turn raw posting fields into the one-row table the pipeline was trained on."""
    # Same as training: blanks become "" and the five fields are joined with spaces.
    text = " ".join((fields.get(name) or "") for name in TEXT_FIELDS)

    row = {
        "text": text,
        "has_company_logo": int(fields["has_company_logo"]),
        "has_questions": int(fields["has_questions"]),
        "telecommuting": int(fields["telecommuting"]),
        # In training a blank CSV cell meant "missing", so whitespace-only counts as missing here.
        "salary_listed": int(not _is_blank(fields.get("salary_range"))),
        "has_company_profile": int(not _is_blank(fields.get("company_profile"))),
    }
    return pd.DataFrame([row])


def _top_reasons(pipeline, row: pd.DataFrame, n: int, min_contribution: float) -> list[dict]:
    """The (up to) n words or metadata facts that pushed this posting most toward "fake".

    The model's score (log-odds of "fake") is:
        bias + sum(word TF-IDF x word weight) + sum(metadata value x metadata weight)
    The reasons are NOT an exact breakdown of that score: they leave out the bias, everything
    pushing toward "real", and anything below min_contribution. They rank what pushed toward fake.

    - Words: TF-IDF x weight, i.e. compared with the word being absent.
    - Yes/no metadata: compared with the OPPOSITE answer, i.e. (value - (1 - value)) x weight.
      Plain value x weight would make "no logo" (value 0) always contribute 0, even though
      lacking a logo is one of the strongest scam signals.
    """
    features = pipeline.named_steps["features"]
    weights = pipeline.named_steps["model"].coef_[0]
    vectorizer = features.named_transformers_["text"]

    candidates = []

    # Words. The ColumnTransformer puts the text columns first, so the first n_terms weights are words.
    tfidf = vectorizer.transform(row["text"])            # 1 x vocabulary, mostly zeros
    n_terms = tfidf.shape[1]
    terms = vectorizer.get_feature_names_out()
    for index, value in zip(tfidf.indices, tfidf.data):  # only terms that appear in the posting
        candidates.append(("word", terms[index], value * weights[index]))

    # Metadata, in the same order the ColumnTransformer passed them to the model.
    metadata_columns = dict((name, cols) for name, _, cols in features.transformers_)["meta"]
    for offset, column in enumerate(metadata_columns):
        value = int(row[column].iloc[0])
        weight = weights[n_terms + offset]
        contribution = (value - (1 - value)) * weight
        candidates.append(("metadata", METADATA_LABELS[column][value], contribution))

    candidates.sort(key=lambda c: c[2], reverse=True)
    return [
        {"label": label, "type": kind, "contribution": round(float(contribution), 3)}
        for kind, label, contribution in candidates[:n]
        if contribution >= min_contribution
    ]


def score_posting(
    *,
    description: str,
    title: str = "",
    company_profile: str = "",
    requirements: str = "",
    benefits: str = "",
    salary_range: str | None = None,
    has_company_logo: bool = False,
    has_questions: bool = False,
    telecommuting: bool = False,
    model: dict | None = None,
) -> dict:
    """Score one posting for scam risk.

    Returns {"probability": 0-1, "flagged": bool, "reasons": [...]}, where each reason is
    {"label", "type": "word" | "metadata", "contribution"}: the strongest pushes toward "fake",
    ranked together (see _top_reasons for how they're measured and what they leave out).
    Raises ValueError if the description is empty: without it there is too little text to judge.
    """
    if _is_blank(description):
        raise ValueError("description is required: paste the job description text to score a posting")

    bundle = model or _default_model()
    pipeline = bundle["pipeline"]

    row = _build_row({
        "title": title,
        "company_profile": company_profile,
        "description": description,
        "requirements": requirements,
        "benefits": benefits,
        "salary_range": salary_range,
        "has_company_logo": has_company_logo,
        "has_questions": has_questions,
        "telecommuting": telecommuting,
    })

    probability = float(pipeline.predict_proba(row)[0, 1])
    return {
        "probability": round(probability, 4),
        "flagged": probability >= SCAM_THRESHOLD,
        "reasons": _top_reasons(pipeline, row, TOP_N_REASONS, MIN_REASON_CONTRIBUTION),
    }
