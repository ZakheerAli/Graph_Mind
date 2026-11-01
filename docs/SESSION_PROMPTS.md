# Copy-paste prompts

## 1) NEW CHAT START (use this every time)
Read AGENTS.md and docs/PROGRESS.md. Run git status. Tell me in 3 lines: current phase, next task, blockers. Then start the NEXT task from PROGRESS.md. Make a short plan first, wait for my "go".

## 2) WRAP UP (use before closing the chat)
Wrap up. Run make check. Commit. Update docs/PROGRESS.md (done, in progress, NEXT task exact and small, decisions, issues). Add an ADR if we made a big decision. Show me the PROGRESS.md diff.

## 3) SECURITY REVIEW (before each phase ends)
Act as a security auditor. Review the changes of this phase against OWASP Top 10 and OWASP Top 10 for LLM apps. Check auth, RLS, input validation, CORS, rate limits, secrets, injection (SQL/Cypher/prompt), file upload, logging. Table: Issue | File | Severity | Fix. Do not change code yet.

## 4) STUCK / BUG
Bug: <what happens>. Expected: <what should happen>. Do not guess. First reproduce it with a failing test, then find the root cause, then fix, then confirm the test passes.

## 5) EXPLAIN
Explain the diff you just made like I am a beginner. List risks and what to test manually.
