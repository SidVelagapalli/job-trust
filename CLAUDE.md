# Project: Job Trust Score
A tool that scores job postings for scam risk (trained ML model)
and ghost-job risk (rule-based, clearly labeled as rules).

## How to work with me
- I am a complete ML beginner. Explain every concept in plain English
  the first time it appears.
- Before writing or changing any file, explain what you'll do and why,
  then wait for my OK.
- Ask before installing any package. Tell me what it's for.
- Never make changes silently. After each step, summarize what changed.
- Prefer simple, readable code over clever code. Comment the "why."
- Keep data/ out of git (add it to .gitignore).
- Call me Siddarth. Be direct; if I'm avoiding a decision or a hard step, say so.

## Stack
Python, pandas, scikit-learn, Jupyter notebooks for exploration.
Later: FastAPI or a Vercel Python function, Next.js frontend, Supabase.
RAG phase (Task Set 7+): sentence-transformers embeddings, a vector store
(Supabase pgvector preferred, Qdrant acceptable), Claude API for any LLM step.

## Layout
- `data/` — datasets (contents are gitignored)
- `notebooks/` — exploration and analysis notebooks
- `src/` — source code
- `tests/` — pytest tests
- `evals/` — fixed eval questions/postings + scoring script (Task Set 6+)

## Notes
- The GitHub repo is public: never commit data files or credentials.
- Keep secrets in `.env` (gitignored).

## Session routine (every time)
1. Read this file and `STATUS.md`. Say in 3 lines where we are and what's next.
2. Work in small task sets. Each step: explain → wait for OK → do it → show evidence.
3. Commit after each finished step with a clear message (never force-push, never rewrite history).
4. End the session by updating `STATUS.md`: done, paused at, open questions for me, how to resume.

## Definition of DONE (the 5 Checks)
Never report a task as done from implementation alone. Before saying DONE, provide:
- REQUIREMENT: the exact requirement, quoted or paraphrased.
- TEST: the actual test run and its actual output, pasted.
- REGRESSION: what else could break, and what you checked (always run `.venv/bin/pytest`).
- DIFF: every changed file and why.
- UNPROVEN: anything not verified. If nothing, say so.

## Evaluation rules (protect the numbers)
- The held-out test set has already been used twice. Do not score it again without asking me first;
  tune on cross-validated training predictions only.
- Every change that could move results gets a before/after comparison from a repeatable script,
  saved to a CSV. Resume numbers only come from those runs.
- Never present a number as better without the baseline next to it.

## Stop and ask (always)
- Choosing thresholds, zones or anything shown to students as a verdict (that's my decision).
- Touching the test set, deleting data or models, or changing the API's response shape.
- Anything that costs money (API calls in loops, paid services). Estimate the cost first.
- Installing anything not from a well-known vendor: run the Skill & MCP Safety Check first.

## Roadmap
- **Task Set 4.5**: zones (HIGH/LOW/unsure) + student messages. Paused, waiting on my choice. See STATUS.md.
- **4.6**: I write "Why these thresholds" in README; add Limitations and Roadmap sections.
- **5 — Ship v1**: deploy the API (Vercel Python function or Render), a simple web page to paste a posting,
  a public demo link. Rate-limit it. No data stored.
- **6 — Modern eval set**: 50–100 hand-checked 2025–26 postings (real + scam, incl. the "Madison Tech" miss)
  in `evals/`, plus a scoring script. Measure v1 on them honestly.
- **7 — RAG baseline (Sergiu Step 0)**: embed known postings; for a new posting retrieve the 5 most similar
  labeled ones and show them as evidence. Measure with the eval set.
- **8 — LLM second opinion with caching + routing (Sergiu Project 1)**: send only unsure-zone postings to
  Claude; semantic cache for near-duplicate postings; small vs. large model routing; dashboard of
  cost, cache hit rate, p95 latency, accuracy. Resume line only with measured numbers.
- **9 — Polish & story**: README with architecture diagram, results table, demo GIF, limitations;
  a 60-second demo for CredCore.
