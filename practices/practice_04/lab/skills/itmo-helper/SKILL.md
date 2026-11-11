---
name: itmo-helper
description: Use ONLY in practices/practice_04/lab to verify Practice 4 artifacts, run the lab runner after edits, and aggregate results. Trigger when the user says "verify_practice_04" or "verify practice 4".
---

# ITMO Helper Skill

Use this skill to validate Practice 4 deliverables and to run the lab's runner automatically after code edits.

## Scenario: verify_practice_04

Purpose: Validate required artifacts and produce a consolidated report.

Steps the agent should perform:
1. Ensure you operate within `practices/practice_04/lab`.
2. Validate presence of required files/directories:
   - `AGENTS.md`
   - `opencode.json`
   - `skills/itmo-helper/SKILL.md` (this file)
   - `hooks/run_checks.sh` (executable)
   - `mcp` directory is present and will be validated for content when implemented
   - `../reflection.md` or `./reflection.md` exists
3. Run the lab runner: `./hooks/run_checks.sh` and capture its stdout/stderr and exit code.
4. Aggregate results into `./proofs/skills/verify_YYYYMMDD_HHMMSS.log`:
   - Include a header, the validation summary, runner output, and a final OK/FAIL line.
5. Return a brief summary to the user: `Skill verify_practice_04: OK` or `...: FAIL` and the path to the log.

Notes:
- Do not commit secrets. Ensure provider options in `opencode.json` use `{env:...}` placeholders.
- If MCP is not yet implemented, warn and continue; the MCP liveness check will be enforced after MCP is added.
