# Status — where we left off

_Last updated: 2026-10-06_

## Setup session (2026-10-06): Build & Ship workstream
- `CLAUDE.md` updated and committed: session routine, 5 Checks, evaluation rules, stop-and-ask, roadmap.
- Workstream hub `~/Documents/Claude-Workstreams/03-build/CLAUDE.md` rewritten (BUILD_RULES + project
  table + a copy of this repo's CLAUDE.md). Old version kept there as `CLAUDE.old.md`.
- No project work done this session. Task Set 4.5 is unchanged (see below).

## Done
- **Task Set 1** — `notebooks/01_explore.ipynb`: data exploration (17,880 postings, 4.84% fake).
- **Task Set 2** — `notebooks/02_baseline.ipynb`: TF-IDF + logistic regression baseline
  (1,814 duplicates removed; test PR-AUC 0.819).
- **Task Set 3** — `notebooks/03_improve.ipynb`: text + metadata pipeline, C=10, threshold 0.4;
  test PR-AUC 0.857, recall 83.3%, precision 64.9%. Saved to `models/job_trust_v1.joblib`.
- **Task Set 4** — backend: `src/predict.py` (score + reasons, words and metadata ranked
  together, min contribution 0.2), `src/ghost_rules.py` (rule-based ghost score),
  `src/api.py` (FastAPI `POST /score`), `tests/test_predict.py` (5 tests, all passing),
  `README.md` ("Why this threshold" left empty for the owner).
- **Zone analysis** — `notebooks/04_zones.ipynb`, training data only:
  HIGH = **0.79** (≥90% of postings at/above are fake), LOW = **0.12** (below holds ≤5% of fakes).
  First attempted rule ("≤1% of green zone is fake") was rejected: it let 21% of fakes into green.

## Paused at: Task Set 4.5
The code still uses the single 0.4 threshold (`flagged`). Nothing zone-related is in `src/` yet.

- **Part A — not run yet.** Add section 7 to `notebooks/04_zones.ipynb` comparing three versions
  on cross-validated training predictions (no test set): main (90% / 5%), (a) stricter HIGH
  (95%), (b) stricter LOW (2% of fakes). Per zone: postings, % fake, % of all fakes, and % of
  all real postings that land in "unsure". Explain trade-offs; do not recommend.
- **Part B — waiting on the owner's choice** of LOW / HIGH / version. Then: zones + student
  messages in `src/predict.py`, `zone`/`message` in `src/api.py`, updated tests (boundary test,
  banned-words test), re-score the 4 test postings, README updates (rename to
  "Why these thresholds", Limitations, Roadmap for Task Sets 5–9).

## Open questions for the owner
- Keep the missing-logo test from Task Set 4 in Part B? (Suggested: yes.)
- Write "Why this/these thresholds" in `README.md`.
- `CLAUDE.backup-2026-10-06.md` (untracked): delete it? The old CLAUDE.md is already in git history.
- `03-build/CLAUDE.old.md`: delete once happy with the new workstream CLAUDE.md.
- `~/cs320-coach` has no STATUS.md or CLAUDE.md yet (BUILD_RULES rule 11).
- Set the Anthropic Console monthly spend cap before Task Set 8.

## Known findings to remember
- A hand-written modern scam (Madison Tech, "ML and RAG pipeline…") scored **0.1172** — missed;
  it falls just under LOW = 0.12, so it would show as "likely real".
- Real postings pasted without a separate "About the company" field get "no company profile"
  (+1.36) as a reason.
- The test set has been used twice (Task Set 3, and one check of the rejected first zone rule).
- Running notebooks with parallel cross-validation can overload the CPU; notebook 04 limits
  each worker to one thread.

## How to resume
```bash
cd ~/job-trust
claude --continue            # reopen the last conversation, or: claude --resume
```
Or start fresh with: _"Read CLAUDE.md and STATUS.md, then continue Task Set 4.5 Part A."_

Run the API: `.venv/bin/uvicorn src.api:app --reload` → http://127.0.0.1:8000/docs
Run tests: `.venv/bin/pytest`
