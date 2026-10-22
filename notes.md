# Notes - Rung 4 (agent)

## Task set log (Claude adds 3 lines per finished task set)

### Task set A - tools, tests, examples
- Built: `src/tools.py` (3 evidence tools: domain age via RDAP, email-vs-company domain, careers page), its offline tests, and two example postings.
- Concept: a tool "never raises" - it returns `{"error": ...}` instead, so one failed lookup (Wi-Fi off, slow site) doesn't crash the whole agent; the model just explains what it couldn't check.
- Quiz: Why does `check_careers_page` returning `found: False` NOT count as a red flag, and what kind of site causes it?

### decide.py - verdict rules (written by Claude at Siddarth's request, Oct 21)
- Built: `src/decide.py` turns evidence (ML score + tool results) into scam / unsure / likely_real plus a `rules_fired` list. Code decides; the LLM only explains.
- Concept: the verdict is plain `if` rules so it can't be prompt-injected, gives the same answer every time, and is unit-tested. `.get()` + `is True` mean missing evidence never counts as a red or green flag.
- Design choice: webmail vs. email-mismatch uses `elif`, so one bad email = one red flag, not two.
- Quiz: Why does an ML score of 0.85 with no tool results come out "unsure" and not "scam"?
- Quiz: Trace ML 0.50 + Gmail recruiter + 30-day-old domain. Which rules fire and what's the verdict?
- Quiz: Why `email.get("matches_company") is False` instead of `not email.get("matches_company")`?

## Experiments (Siddarth)
<!-- traces, injection test, MAX_STEPS=1 / Wi-Fi off, workflow-vs-agent table -->
