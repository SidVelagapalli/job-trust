# Notes - Rung 4 (agent)

## Task set log (Claude adds 3 lines per finished task set)

### Task set A - tools, tests, examples
- Built: `src/tools.py` (3 evidence tools: domain age via RDAP, email-vs-company domain, careers page), its offline tests, and two example postings.
- Concept: a tool "never raises" - it returns `{"error": ...}` instead, so one failed lookup (Wi-Fi off, slow site) doesn't crash the whole agent; the model just explains what it couldn't check.
- Quiz: Why does `check_careers_page` returning `found: False` NOT count as a red flag, and what kind of site causes it?

## Experiments (Siddarth)
<!-- traces, injection test, MAX_STEPS=1 / Wi-Fi off, workflow-vs-agent table -->
