#!/usr/bin/env bash

# Runner for Practice 4 lab: performs basic validation and emits human-readable output.
# - Checks required files
# - Validates JSON configs (lab/opencode.json)
# - Ensures expected structure exists
# - Emits logs to ./proofs/checks/

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$LAB_DIR/proofs/checks"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

# Tee all output to log file as well as stdout
exec > >(tee -a "$LOG_FILE") 2>&1

FAILURES=0
WARNINGS=0

section() { echo "== $1 =="; }
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES+1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS+1)); }

have() { command -v "$1" >/dev/null 2>&1; }

json_validate() {
  local file="$1"
  if have node; then
    node -e 'const fs=require("fs");const p=process.argv[1];JSON.parse(fs.readFileSync(p,"utf8"));' "$file" 2>/dev/null
    return $?
  elif have python3; then
    python3 - <<PY "$file" 2>/dev/null
import sys, json
json.load(open(sys.argv[1]))
PY
    return $?
  elif have python; then
    python - <<PY "$file" 2>/dev/null
import sys, json
json.load(open(sys.argv[1]))
PY
    return $?
  else
    warn "No Node.js or Python found to validate JSON; skipping strict JSON validation for $file"
    return 0
  fi
}

json_assert_opencode_lab() {
  # Asserts specific expectations in lab/opencode.json using Node if available
  local file="$1"
  if have node; then
    node - <<'NODE' "$file"
const fs=require('fs');
const p=process.argv[1];
const j=JSON.parse(fs.readFileSync(p,'utf8'));
let ok=true;
function requireArrayIncludes(arr, val, label){
  if(!Array.isArray(arr) || !arr.includes(val)) { console.log(`[EXPECT] ${label}: missing "${val}"`); ok=false; }
}
requireArrayIncludes(j.instructions, 'AGENTS.md', 'instructions');
const sp = j.skills && Array.isArray(j.skills.paths) ? j.skills.paths : (j.skills && j.skills.paths) || [];
if(!Array.isArray(sp) || !sp.includes('./skills')) { console.log('[EXPECT] skills.paths should include ./skills'); ok=false; }
// env placeholders recommended
const vs=j.provider && j.provider.vsellm;
if(vs && vs.options){
  const { baseURL, apiKey } = vs.options;
  if(!(typeof baseURL==='string' && baseURL.includes('{env:'))) console.log('[EXPECT] provider.vsellm.options.baseURL should use {env:...}');
  if(!(typeof apiKey==='string' && apiKey.includes('{env:'))) console.log('[EXPECT] provider.vsellm.options.apiKey should use {env:...}');
}
process.exit(ok?0:1);
NODE
    return $?
  else
    # Fallback to python3 assertions if Node.js is unavailable
    if have python3; then
      python3 - <<'PY' "$file"
import sys, json
p = sys.argv[1]
j = json.load(open(p, 'r', encoding='utf-8'))
ok = True

def expect(cond, msg):
    global ok
    if not cond:
        print(f"[EXPECT] {msg}")
        ok = False

instructions = j.get('instructions')
expect(isinstance(instructions, list) and 'AGENTS.md' in instructions, "instructions must include 'AGENTS.md'")

skills = j.get('skills', {})
paths = skills.get('paths') if isinstance(skills, dict) else None
expect(isinstance(paths, list) and './skills' in paths, "skills.paths should include ./skills")

provider = j.get('provider', {})
vs = provider.get('vsellm') if isinstance(provider, dict) else None
opts = vs.get('options') if isinstance(vs, dict) else None
if isinstance(opts, dict):
    baseURL = opts.get('baseURL')
    apiKey = opts.get('apiKey')
    expect(isinstance(baseURL, str) and '{env:' in baseURL, "provider.vsellm.options.baseURL should use {env:...}")
    expect(isinstance(apiKey, str) and '{env:' in apiKey, "provider.vsellm.options.apiKey should use {env:...}")

sys.exit(0 if ok else 1)
PY
      return $?
    else
      warn "Node.js and python3 not found; skipping deep opencode.json assertions"
      return 0
    fi
  fi
}

QUIET=0
if [[ ${1:-} == "--quiet" ]]; then QUIET=1; fi

if [[ $QUIET -eq 0 ]]; then
  section "Environment"
  if [[ -z "${VSELLM_BASE_URL:-}" ]]; then warn "VSELLM_BASE_URL is not set"; else pass "VSELLM_BASE_URL is set"; fi
  if [[ -z "${VSELLM_API_KEY:-}" ]]; then warn "VSELLM_API_KEY is not set"; else pass "VSELLM_API_KEY is set"; fi
fi

section "Required files"
if [[ -f "$LAB_DIR/AGENTS.md" ]]; then pass "AGENTS.md present"; else fail "AGENTS.md is missing"; fi
if [[ -f "$LAB_DIR/opencode.json" ]]; then pass "opencode.json present"; else fail "opencode.json is missing"; fi
if [[ -d "$LAB_DIR/skills" ]]; then pass "skills directory present"; else fail "skills directory missing"; fi
if [[ -d "$LAB_DIR/hooks" ]]; then pass "hooks directory present"; else fail "hooks directory missing"; fi
if [[ -d "$LAB_DIR/proofs" ]]; then pass "proofs directory present"; else fail "proofs directory missing"; fi

section "JSON validation"
if [[ -f "$LAB_DIR/opencode.json" ]]; then
  if json_validate "$LAB_DIR/opencode.json"; then
    pass "opencode.json is valid JSON"
    if json_assert_opencode_lab "$LAB_DIR/opencode.json"; then
      pass "opencode.json has expected fields (instructions, skills.paths)"
    else
      fail "opencode.json missing expected fields (see above EXPECT messages)"
    fi
  else
    fail "opencode.json is invalid JSON"
  fi
fi

section "Runner integrity"
if [[ -x "$SCRIPT_DIR/run_checks.sh" ]]; then pass "run_checks.sh is executable"; else warn "run_checks.sh is not executable (chmod +x)"; fi

section "MCP checks"
if [[ -d "$LAB_DIR/mcp" ]]; then
  if ls -1 "$LAB_DIR/mcp" | grep -q .; then
    pass "MCP project detected"
    # Liveness: start server with --selftest
    if have python3; then
      if python3 "$LAB_DIR/mcp/itmo-mcp/server.py" --selftest >/dev/null 2>&1; then
        pass "MCP server selftest OK"
      else
        fail "MCP server selftest FAILED"
      fi
    else
      warn "python3 not found; skipping MCP selftest"
    fi
  else
    warn "MCP directory exists but empty; skipping"
  fi
else
  warn "No MCP directory yet; skipping MCP checks"
fi

section "Summary"
echo "Warnings: $WARNINGS"
echo "Failures: $FAILURES"

if [[ $FAILURES -gt 0 ]]; then
  echo "Result: FAIL"
  exit 1
else
  echo "Result: PASS"
  exit 0
fi
