# itmo-helper skill

This skill validates Practice 4 deliverables and aggregates the lab runner output.

Usage:
1. Ensure you are in `practices/practice_04/lab`.
2. Run: `./skills/itmo-helper/verify.sh`.
3. See results in console and log file under `./proofs/skills/verify_*.log`.

What it checks:
- Presence of `AGENTS.md`, `opencode.json`, `skills/itmo-helper/SKILL.md`, `hooks/run_checks.sh`.
- Presence of `mcp/` directory (content checks added after MCP implementation).
- Optional `reflection.md` in lab or practice root.
- Executes `./hooks/run_checks.sh` and includes its output in the report.

Exit codes:
- 0: OK
- 1: FAIL
