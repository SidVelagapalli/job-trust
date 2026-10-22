# Notes - Rung 4 (agent)

## Task set log (Claude adds 3 lines per finished task set)

### Task set A - tools, tests, examples
- Built: `src/tools.py` (3 evidence tools: domain age via RDAP, email-vs-company domain, careers page), its offline tests, and two example postings.
- Concept: a tool "never raises" - it returns `{"error": ...}` instead, so one failed lookup (Wi-Fi off, slow site) doesn't crash the whole agent; the model just explains what it couldn't check.
- Quiz: Why does `check_careers_page` returning `found: False` NOT count as a red flag, and what kind of site causes it?

### decide.py - verdict rules (written by Claude at Siddarth's request, Oct 21; Siddarth accepted this exception to SPEC's "Siddarth writes this" on Oct 22)
- Built: `src/decide.py` turns evidence (ML score + tool results) into scam / unsure / likely_real plus a `rules_fired` list. Code decides; the LLM only explains.
- Concept: the verdict is plain `if` rules so it can't be prompt-injected, gives the same answer every time, and is unit-tested. `.get()` + `is True` mean missing evidence never counts as a red or green flag.
- Design choice: webmail vs. email-mismatch uses `elif`, so one bad email = one red flag, not two.
- Quiz: Why does an ML score of 0.85 with no tool results come out "unsure" and not "scam"?
- Quiz: Trace ML 0.50 + Gmail recruiter + 30-day-old domain. Which rules fire and what's the verdict?
- Quiz: Why `email.get("matches_company") is False` instead of `not email.get("matches_company")`?
- Walkthrough (by part, matching the comments in the file):
  - Part 1: thresholds. ML high >= 0.79, low < 0.12 (from `notebooks/04_zones.ipynb`); domain < 180 days = red, >= 730 days = green.
  - Part 2: ML score read with `[]` (always present); tool results with `.get(...) or {}` so a missing tool doesn't crash.
  - Part 3: red flags. Webmail OR email/company mismatch (`elif`, max one email flag); young domain.
  - Part 4: green checks. Separate `if`s: email matches, old domain, careers page found. Careers not found adds nothing.
  - Part 5: ML zone line. Explanation only, doesn't change the verdict.
  - Part 6: verdict. scam = high ML + 1 red, or any 2 reds. likely_real = 0 reds + (low ML + 1 green, or non-high ML + 2 greens). Else unsure.
  - Part 7: returns `verdict` + `rules_fired` (the reasons the LLM explains).
  - Tests: `tests/test_tools_and_rules.py` lines 34-63.

### Task set B - agent loop + fixed workflow
- Built: `src/agent.py` (Claude picks which checks to run, max 6 steps, `decide()` sets the verdict, Claude explains, every run logged to `logs/`), `src/workflow.py` (same checks via regex, no LLM), `tests/test_agent_loop.py` (fake Claude, no API cost).
- Concept: the agent loop (ReAct): the model asks for a tool, our code runs it, the result goes back in, repeat until it says DONE or hits MAX_STEPS.
- Quiz: In `test_agent_loop.py`, why can the test run the full pipeline without an API key, and what does `FakeClient` pretend to do on call 1 vs. call 2?

## Experiments (Siddarth)
<!-- traces, injection test, MAX_STEPS=1 / Wi-Fi off, workflow-vs-agent table -->
