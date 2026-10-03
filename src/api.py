"""HTTP API: POST a job posting to /score, get scam and ghost-job risk back.

Run locally:  .venv/bin/uvicorn src.api:app --reload   then open http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from src.ghost_rules import ghost_score
from src.predict import load_model, score_posting


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once when the server starts and keep it in memory.
    # Loading per request would re-read the file and rebuild the 20,000-term
    # vocabulary every time, adding delay to each call for no benefit.
    app.state.model = load_model()
    yield


app = FastAPI(title="Job Trust Score", lifespan=lifespan)


class PostingIn(BaseModel):
    """What a client sends. Pydantic rejects wrong types/missing fields with a 422 error."""

    description: str = Field(..., description="Full job description text (required)")
    title: str = ""
    company_profile: str = ""
    requirements: str = ""
    benefits: str = ""
    salary_range: str | None = Field(None, description='e.g. "50000-60000"; leave empty if none')
    has_company_logo: bool = False
    has_questions: bool = Field(False, description="Does the application ask screening questions?")
    telecommuting: bool = Field(False, description="Is the job remote?")
    # Optional user answers used only by the ghost-job rules.
    days_since_posted: int | None = Field(None, ge=0)
    seen_before: bool | None = Field(None, description="Have you seen this posting before?")

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("description is required: paste the job description text")
        return value


class ScoreOut(BaseModel):
    scam_probability: float
    flagged: bool
    reasons: list[dict]
    ghost_score: int
    ghost_reasons: list[dict]
    ghost_method: str


@app.post("/score", response_model=ScoreOut)
def score(posting: PostingIn, request: Request) -> ScoreOut:
    try:
        scam = score_posting(
            description=posting.description,
            title=posting.title,
            company_profile=posting.company_profile,
            requirements=posting.requirements,
            benefits=posting.benefits,
            salary_range=posting.salary_range,
            has_company_logo=posting.has_company_logo,
            has_questions=posting.has_questions,
            telecommuting=posting.telecommuting,
            model=request.app.state.model,
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))

    ghost = ghost_score(
        description=posting.description,
        salary_range=posting.salary_range,
        other_text=" ".join([posting.title, posting.company_profile, posting.requirements, posting.benefits]),
        days_since_posted=posting.days_since_posted,
        seen_before=posting.seen_before,
    )

    return ScoreOut(
        scam_probability=scam["probability"],
        flagged=scam["flagged"],
        reasons=scam["reasons"],
        ghost_score=ghost["score"],
        ghost_reasons=ghost["reasons"],
        ghost_method=ghost["method"],
    )
