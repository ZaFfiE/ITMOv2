# Reflection: Title Search Assignment

1. Why GitHub Spec Kit was chosen (SDD framework)
- Observations:
- The repo already contains .specify/ templates and scripts (spec, plan, tasks), so Spec Kit is natively integrated.
- We used the provided scripts to generate plan/tasks under specs/001-items-title-search/.
- Assumptions:
- Using Spec Kit keeps alignment with existing governance and avoids introducing a parallel framework.
2. How its workflow compares with OpenSpec
- Observations:
- Spec Kit in this project followed a linear, document-first flow: specify → plan → tasks → implement, anchored to a feature directory.
- No .specify/extensions.yml file existed, so no hooks ran.
- Assumptions:
- OpenSpec focuses on change artifacts (proposals, delta specs, sync/archive) whereas Spec Kit emphasizes templated docs (spec.md, plan.md, tasks.md). Given this repo’s scaffolding, Spec Kit fit better.
3. How UI and logic specs were created independently
- Observations:
- UI-SPEC.md defined UI elements (search, list), loading/empty/error states, submission and clear behaviors.
- LOGIC-SPEC.md defined GET /items with q (trimmed, case-insensitive substring), combination with status and tags, and status codes.
- Both were written before implementation and referenced app/service.py and the approved feature spec.
- Assumptions:
- The two specs were authored with minimal cross-influence to preserve independence prior to reconciliation.
4. Disagreements found and how they were resolved
- Observations:
- Clear behavior: UI initially implied clearing q, status, and tags. CONTRACT.md standardized: Clear resets only q, preserving status/tags. UI-SPEC.md was updated. Decision recorded in REVIEW.md.
- A UI test assertion was refined to check the constructed API URL line (const url = "/items" ...) instead of a specific fetch("/items" substring.
- Assumptions:
- None beyond the documented resolution.
5. How the shared contract helped implementation
- Observations:
- CONTRACT.md clarified endpoint, query param semantics, AND-combination rules, response shape (existing fields), status codes, UI states, clear behavior, and backward compatibility.
- Enabled a smallest-diff implementation: add q-filtering to ReadingList.list and a minimal HTML route, without new dependencies.
- Assumptions:
- Having the contract up front reduced ambiguity and focused tests on observable behavior.
6. What was learned and what could be improved
- Observations:
- Single-file service and unittest tests made incremental change straightforward.
- Tests were executed with unittest discovery: python3 -m unittest discover -s tests -p "test*.py" -q. Result: 16 tests passed after adding new tests and a minor adjustment.
- The minimal UI calls the real API and exposes loading, empty, and error states.
- Assumptions:
- Possible improvements: add headless browser tests for DOM state transitions (would add dependencies); extract shared test helpers into a module; automate checklist gates to reflect Spec Kit quality checks.