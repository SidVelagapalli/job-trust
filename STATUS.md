# Status — where we left off

_Last updated: 2026-10-29_

## Session 2026-10-29: merge security fixes, README Security section (Rungs 4 + 5 ready to push)
- `security-fixes` fast-forwarded into `main` (no conflict); pytest = **40 passed**.
- README (`0899b15`): removed the "network error looks like not found" limitation; new "Security" section
  (SSRF guard, fenced posting, explanations told to use `rules_fired`). Reviewer: nothing serious; its 4 wording
  overclaims fixed (DNS rebinding named, "if no request gets through at all", www./https/443/5 hops, "told to").
- Security-reviewer on `origin/main..main` + README: **SAFE TO PUSH**. No secrets/data in the push.
  Findings, all low or already open: DNS rebinding; compressed reply can exceed 1 MB in memory before the cut;
  slow-drip has no total timeout; transitive deps unpinned; look-alike tags; no call/spend limit on `check_posting`
  over MCP; README:144 shows `/Users/Siddarth/...` (harmless, `<repo>/` is cleaner).
- Worktree `~/job-trust-fixes` removed, branch `security-fixes` deleted. CLAUDE.md and notes.md left uncommitted (Siddarth editing).
- **Open for Siddarth:**
  - Local branches `rung4-agent` and `rung5-mcp` are merged into main: delete them if you like (`git branch -d`).
  - Push `main` (4 commits ahead of origin, incl. this STATUS commit). Commit your notes.md / CLAUDE.md edits separately.
  - Before the public deploy (Task Set 5): call limit on `check_posting`, total timeout, refuse non-identity
    `content-encoding`, DNS rebinding (pin the checked IP).
  - Still open: "Why (Siddarth):" lines in notes.md, README "Why this threshold", `mcp dev` / `claude mcp add`,
    one paid re-run to check the EXPLAIN fix.
- **Resume:** `cd ~/job-trust && .venv/bin/pytest -q`, then `git push`.

## Session 2026-10-27 (later): security fixes, branch `security-fixes` (worktree `~/job-trust-fixes`)
- **Done** (one commit, not pushed, not merged): the 4 security-reviewer findings.
  - `check_careers_page` (src/tools.py): resolves the host first and refuses private/loopback/link-local IPs;
    redirects followed by hand, same site + https:443 only, IP re-checked each hop, max 5; body capped at 1 MB
    (`Accept-Encoding: identity`); every request failing on the network -> `{"error": "network failure"}`.
  - `strip_posting_tags` (src/agent.py), used in `gather_evidence` and the MCP `vet_posting` prompt (now fenced + labelled).
  - EXPLAIN prompt cites only `rules_fired`. requirements.txt: direct deps pinned with `==` (mcp stays `>=2.3,<3`).
  - `tests/test_security_fixes.py`: 23 offline tests. pytest = **40 passed**. decide.py untouched.
  - Reviewer: nothing serious (minor issues fixed). Security-reviewer: SAFE TO PUSH.
- **Open for Siddarth:**
  - Push `security-fixes` and merge it (your call). README Limitations still says "network error looks like not found"; update it after merge.
  - Follow-ups (low, not done): no overall time limit on a slow-drip careers page; a server can ignore
    `identity` and send gzip anyway (stop if `content-encoding` isn't identity); NAT64 `64:ff9b::/96` counts as public;
    DNS rebinding; transitive deps unpinned; look-alike `＜/posting＞` not stripped.
  - Quiz Q13 added to `~/Desktop/claude-reviews/QUIZ.md`.
- **Resume:** `cd ~/job-trust-fixes && ~/job-trust/.venv/bin/pytest -q`, then push / open a PR.

## Session 2026-10-27: clean-up and ship Rungs 4 + 5
- **Rung 4 (agent) and Rung 5 (MCP server) are done.** Both are on `main` (fast-forwarded to `b0e3b55`); this clean-up is committed on `main`.
- README: new "Agent" section (pipeline diagram, rules table 0.79 / 0.12 and 180 / 730 days, injection and
  no-network results) and "MCP server" section (tools, resource, prompt, `claude mcp add` line). Limitations now
  include:
  - the explanation can overstate the evidence;
  - a careers-page network error looks like "not found";
  - the agent has been tested on only 2 postings.
- `requirements.txt`: `mcp[cli]>=2.3,<3` pinned. `CLAUDE.backup-2026-10-06.md` moved to `~/Desktop`.
- notes.md: quiz lines removed. Quizzes now live in `~/Desktop/claude-reviews/QUIZ.md` (the new CLAUDE.md rule).
- **Cut from this application round:** PatchPilot and PhishLens.
- **Open for Siddarth:**
  - The "Why (Siddarth):" lines in notes.md: experiments 4 and 5 are blank, and 1 and 3 say "not sure".
  - The README "Why this threshold" section is still a TODO.
  - Not run yet: the Inspector test (`mcp dev`) and `claude mcp add`.
  - Push this clean-up commit. Rungs 4 + 5 (`b0e3b55`) are already on GitHub. Security-reviewer (2026-10-27): PASS, findings below.
  - Before the public deploy (Task Set 5): fix the SSRF in `check_careers_page` (redirects + internal hosts, tools.py:107-118), wrap the posting in `vet_posting`, and add a call limit on `check_posting`.

## Session 2026-10-23 (later): Rung 5, Task set C
- Branch `rung5-mcp` was created from `rung4-agent` (Siddarth's OK, even though SPEC says "after Rung 4 is merged").
  It carries the 7 unmerged Rung 4 commits: merge Rung 4 first.
- Installed `mcp[cli]` (mcp 2.3.0, pre-approved) and added it to requirements.txt (not pinned).
- `src/mcp_server.py` copied word for word from SPEC (byte-checked). A stdio client lists `check_posting` + `score_only`,
  resource `jobtrust://red-flags` and prompt `vet_posting`. `score_only(scam.txt)` = 0.9966. pytest = 17 passed. Reviewer: nothing serious.
- Reviewer notes (Siddarth's call):
  - Pin `mcp[cli]>=2.3,<3`; the import only exists in 2.x.
  - The result comes back as JSON text (`structured_content` is None).
  - `score_only` adds "no company logo" and "no company profile" to every pasted posting (defaults in predict.py).
  - The `vet_posting` prompt calls the paid tool.
- **Not done (Siddarth):** `mcp dev src/mcp_server.py` Inspector test; `claude mcp add ...` (see KICKOFF step 6); `check_posting` over MCP (paid).
- **Still open from Rung 4:** the 5 "Why (Siddarth):" lines, then KICKOFF step 5 (README, security-reviewer, merge, push).

## Session 2026-10-23: Rung 4 break-it experiments
- **Experiments 1-5 done**, written up in `notes.md` under "Experiments (Siddarth)" (3 paid runs, about 3 cents total):
  1. real.txt -> LIKELY_REAL. 2. Injection (`examples/scam_injected.txt`) -> stayed SCAM, explanation not fooled.
  3. MAX_STEPS = 1 -> SCAM, cap logged (src/agent.py restored, diff clean). 4. Dead proxy -> no crash, tools return errors.
  5. Workflow vs agent -> same verdicts and same checks on both examples.
- **Findings:**
  - The explanation overstates the evidence: it cites careers page / domain issues that decide.py ignores,
    and in run 1 it called a `found: False` careers page "confirming legitimacy".
  - A network error in `check_careers_page` looks like "not found" (it reports no error).
- **Paused at:** Siddarth fills the 5 "Why (Siddarth):" lines in notes.md, then KICKOFF step 5
  (README "Agent" section draft, security-reviewer, Siddarth edits README and pushes).

## Session 2026-10-21/22: Rung 4, Task set B
- `src/decide.py` done (commit `ba0a90b`). Claude wrote it at Siddarth's request; Siddarth accepted this
  exception to SPEC's "Siddarth writes this" (noted in notes.md).
- **Task set B done**, commit `8e99fd9`: `src/agent.py`, `src/workflow.py`, `tests/test_agent_loop.py`
  (verbatim from SPEC, byte-checked by reviewer). `pytest -q` = 17 passed.
  Free workflow run: `scam.txt` -> scam, `real.txt` -> likely_real.
- Reviewer minor notes (all from SPEC, not changed, Siddarth's call): `workflow.py` SITE_RE misses bare
  domains ("Visit acme.com"); `explain()` assumes first reply block is text; no MAX_STEPS test; a repeated
  tool call overwrites the earlier result. Also: an unregistered domain (scam.txt's) adds no red flag.
- **Real agent run on scam.txt: SCAM** (acceptance met for that file; `claude-haiku-4-5` works; ~1 cent).
  Claude ran all 3 checks in step 0. Note: the explanation cites "no careers page" / "domain not found",
  which decide.py deliberately ignores; worth a break-it experiment.
- **API key:** stays in `~/.zshrc` (Siddarth's choice, shared across projects); no `.env`. The `claude` alias
  strips it, so paid runs load it per command:
  `export $(grep '^export ANTHROPIC_API_KEY=' ~/.zshrc | sed 's/^export //; s/"//g') && .venv/bin/python -m src.agent examples/real.txt`
- **Paused at:** real run on `real.txt` (expect LIKELY_REAL), not run yet.
- **Next (Siddarth):** real runs, break-it experiments in notes.md, README "Agent" section edit,
  security-reviewer, push. Then Task set C (Rung 5, branch `rung5-mcp`).
- Project agents in `.claude/agents/` only load when Claude Code is started inside `~/job-trust`.

## Session 2026-10-17: Rung 4 (agent), fast-track
- Claude Code now runs on the Pro plan (`/login`). `ANTHROPIC_API_KEY` was set in `~/.zshrc`; it
  overrides the Pro login if still exported. Paid `src.agent` runs need that key (put it in `.env` or export it in that terminal only).
- Whole-rung plan for Rung 4 approved (one approval). Branch `rung4-agent` created.
- **Task set A done**, commit `99133d4`: `src/tools.py`, `tests/test_tools_and_rules.py` (both copied word for word from SPEC),
  `examples/scam.txt` + `real.txt`, `anthropic` + `httpx` in requirements.txt, `logs/` in .gitignore, `notes.md`.
  Reviewer: nothing serious. Old 5 tests pass; new test file errors at import until decide.py exists.
- **Paused at:** Siddarth writes `src/decide.py` (it was NOT found on disk this session).
  Done when `.venv/bin/pytest -q` shows 15 passed.
- **Next (pre-approved, no new OK needed):** Task set B: `src/agent.py`, `src/workflow.py`,
  `tests/test_agent_loop.py` copied word for word, pytest = 17 passed, then `python -m src.workflow examples/scam.txt`
  (free network calls, no LLM; Siddarth OK'd it), reviewer, commit, 3 lines in notes.md.
- Reviewer's minor notes for Siddarth: SPEC line 27 wording ("tool tests pass") is wrong while decide.py is missing;
  `age_from_rdap` can raise on a date with no timezone (caught by `check_domain_age`); requirements are unpinned.

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
Or start fresh with: _"Read CLAUDE.md, SPEC.md and STATUS.md. decide.py is done (15 passed): run Task set B."_
Note: SPEC says Rung 4's decide.py covers Task Set 4.5 Part B.

Run the API: `.venv/bin/uvicorn src.api:app --reload` → http://127.0.0.1:8000/docs
Run tests: `.venv/bin/pytest`
