# Demo Scenario: AGENTS.md → Skill → MCP → Autocheck

Date: 2026-10-07

Steps:
1. Edit: created `agent/demo.md` to trigger autochecks and include token AGENTS.
2. Runner: executed `./hooks/run_checks.sh` automatically after edit.
   - Result: PASS
   - Log file: see `proofs/checks/` directory (latest run_* log)
3. Skill: executed `./skills/itmo-helper/verify.sh`.
   - Result: OK
   - Log file: see `proofs/skills/verify_*.log` (latest)
4. MCP: invoked via test client `python3 ./mcp/test_client.py`.
   - Success log: `proofs/mcp/success_*.log`
   - Error log: `proofs/mcp/error_*.log`

Evidence:
- Runner PASS output present with environment, file, JSON and MCP selftest checks.
- Skill log consolidates runner output and artifacts validation.
- MCP success log shows `tools/list` and `tools/call` with `total_matches > 0`.
- MCP error log shows invalid regex error with code -32602.
