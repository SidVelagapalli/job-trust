# KICKOFF - Job Trust (paste these into Claude Code, one block at a time)

Open a terminal tab: `cd ~/job-trust && claude`. Press Shift+Tab until the status bar says plan mode.

## 0. One-time setup (you, 1 minute, in a normal terminal)
Remote tools can't write into `.claude/`, so the subagents and permission settings are waiting in `claude-setup/`:
```bash
cd ~/job-trust
mkdir -p .claude && cp -R claude-setup/. .claude/ && rm -r claude-setup
ls .claude .claude/agents      # settings.json + 4 agents
```
Then start Claude Code and type `/agents`: you should see test-writer, reviewer, security-reviewer, explorer.

## FAST PATH: one approval per rung (paste this instead of the step-by-step prompts)
```
Read CLAUDE.md and SPEC.md. One approval per rung: in plan mode, plan the WHOLE rung (every task set in
SPEC "Order of work", which subagents run in parallel, what you'll run) and wait for my OK. Then build it
all: parallel subagents per task set, reviewer after each task set, commit on the rung's branch.
Never write the files marked "Siddarth writes this": build everything that doesn't depend on them, then
stop and tell me which tests my files must pass. Pre-approved installs are listed in SPEC.md.
Don't run anything that calls the paid API; those runs are mine.
```
The numbered steps below are still your map: they show where YOUR work (your file, experiments, eval data, pushing) fits.
For job-trust, Rung 4 and Rung 5 are separate rungs: one approval each (Rung 5 starts after Rung 4 is merged).


## 1. Task set A (Claude Code, ~10 min while you read SPEC.md's decide.py section)
```
Read CLAUDE.md and SPEC.md. Fast-track mode applies. Plan task set A, then wait for my OK.
After OK: git switch -c rung4-agent. Install anthropic and httpx into .venv and add both to
requirements.txt (pre-approved). Then IN PARALLEL: test-writer creates tests/test_tools_and_rules.py
verbatim from SPEC; a general-purpose subagent creates src/tools.py verbatim; you create examples/*.txt.
Do NOT create src/decide.py. Add logs/ to .gitignore. Run .venv/bin/pytest and show me the output.
```
Expected: tool tests pass, decide tests fail with ImportError. That failure is your to-do list.

## 2. You: write src/decide.py (~45 min, no Claude Code)
Write it in VS Code from the behaviour spec in SPEC.md. Run `.venv/bin/pytest -q` after every rule.
Done when you see 15 passed. If stuck for 15 minutes on one rule, ask Claude to EXPLAIN that test
(not to write the code).

## 3. Task set B (Claude Code)
```
I've written src/decide.py and the tests pass. Plan task set B, wait for my OK, then IN PARALLEL:
create src/agent.py and src/workflow.py verbatim from SPEC, and test-writer creates
tests/test_agent_loop.py verbatim. Run pytest (expect 17 passed). Then run the reviewer subagent
on the diff and show me its 5 Checks. Commit with a clear message if the reviewer finds no problems.
```

## 4. You: run it and break it (~1.5 hrs, costs about 5 cents total)
- `.venv/bin/python -m src.agent examples/scam.txt` and `examples/real.txt`. Paste both traces in notes.md.
- Injection line at the end of scam.txt (Roadmap Rung 4 Step 6). Verdict must stay SCAM.
- MAX_STEPS = 1, then Wi-Fi off. Write what happened.
- Close SPEC.md and rewrite `gather_evidence` from memory in a scratch file. Compare. Fix what you missed.

## 5. Ship Rung 4 (Claude Code)
```
Draft the README "Agent" section from SPEC.md (pipeline diagram, rules table, limitations), then run
security-reviewer and show me its verdict. Don't push.
```
Edit the README yourself, then `git switch main && git merge rung4-agent && git push`.

## 6. Task set C: Rung 5 MCP server (Claude Code)
```
Plan task set C (Rung 5) and wait for my OK. Then: git switch -c rung5-mcp, install "mcp[cli]"
(pre-approved, add to requirements.txt), create src/mcp_server.py verbatim from SPEC, and prove it
works over stdio WITHOUT calling the paid API: list its tools and call score_only.
```
Then you: `.venv/bin/mcp dev src/mcp_server.py` (Inspector), and register it with
`claude mcp add job-trust -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -- /Users/Siddarth/job-trust/.venv/bin/python /Users/Siddarth/job-trust/src/mcp_server.py`.

## Quiz yourself (end of day)
Ask Claude: "Quiz me on notes.md and the Rung 4 checkpoint. One question at a time; don't give answers until I try."
