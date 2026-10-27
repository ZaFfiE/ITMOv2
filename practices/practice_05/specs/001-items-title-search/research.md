# Phase 0 Research: Items Title Search

## Unknowns and Clarifications

- UI clear behavior scope: Resolved to clearing only q (per CONTRACT.md).
- Query parsing duplicates: Router uses first value per key via parse_qs; document as assumption.
- Minimal HTML UI approach: Serve a single page from existing server; call /items via fetch.

## Decisions

1. Search Matching
   - Decision: Case-insensitive substring on title after trimming q.
   - Rationale: Matches feature spec and keeps logic simple.
   - Alternatives: Regex, tokenization, stemming (rejected as out-of-scope).

2. Combination Semantics
   - Decision: AND across q, status, tags; tags ANY-of.
   - Rationale: Preserves existing behavior and spec requirements.
   - Alternatives: OR across filters (rejected; breaks expectations).

3. UI Integration
   - Decision: Add minimal HTML route and static content served by BaseHTTPRequestHandler path (e.g., GET /) that performs API calls to /items.
   - Rationale: Avoid external dependencies; reuse existing server.
   - Alternatives: Separate static server or framework (rejected as overkill).

## Best Practices Considered

- Input trimming and debouncing on UI side to reduce needless requests; not mandatory but recommended.
- Preserve previous results on errors to avoid flicker; specified in CONTRACT.md.
