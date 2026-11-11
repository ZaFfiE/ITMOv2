#!/usr/bin/env bash

# Skill runner: verify_practice_04
# Produces a consolidated report and returns 0/1 based on checks + lab runner.

set -u -o pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# lab root is two levels up from skills/itmo-helper
LAB_DIR="$(cd "$SKILL_DIR/../.." && pwd)"
PROOF_DIR="$LAB_DIR/proofs/skills"
RUNNER="$LAB_DIR/hooks/run_checks.sh"
mkdir -p "$PROOF_DIR"
LOG_FILE="$PROOF_DIR/verify_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

FAIL=0
WARN=0
section() { echo "== $1 =="; }
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); }
warn() { echo "[WARN] $1"; WARN=$((WARN+1)); }

section "Skill: verify_practice_04"
echo "Lab dir: $LAB_DIR"

section "Artifacts"
[[ -f "$LAB_DIR/AGENTS.md" ]] && pass "AGENTS.md present" || fail "AGENTS.md missing"
[[ -f "$LAB_DIR/opencode.json" ]] && pass "opencode.json present" || fail "opencode.json missing"
[[ -f "$SKILL_DIR/SKILL.md" ]] && pass "Skill SKILL.md present" || fail "Skill SKILL.md missing"
[[ -x "$RUNNER" ]] && pass "Runner executable present" || fail "Runner missing or not executable"
[[ -d "$LAB_DIR/mcp" ]] && pass "MCP directory present" || warn "MCP directory missing"
if [[ -f "$LAB_DIR/reflection.md" ]]; then
  pass "reflection.md present in lab"
elif [[ -f "$(cd "$LAB_DIR/.." && pwd)/reflection.md" ]]; then
  pass "reflection.md present in practice root"
else
  warn "reflection.md not found yet"
fi

section "Run lab runner"
RUN_RESULT=0
if [[ -x "$RUNNER" ]]; then
  (cd "$LAB_DIR" && "$RUNNER") || RUN_RESULT=$?
  if [[ $RUN_RESULT -eq 0 ]]; then
    pass "Lab runner completed with PASS"
  else
    fail "Lab runner FAILED with code $RUN_RESULT"
  fi
else
  fail "Cannot execute lab runner"
fi

section "Summary"
echo "Warnings: $WARN"
echo "Failures: $FAIL"

if [[ $FAIL -gt 0 ]]; then
  echo "Skill result: FAIL"
  exit 1
else
  echo "Skill result: OK"
  exit 0
fi
