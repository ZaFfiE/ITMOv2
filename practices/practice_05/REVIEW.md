# Review and Reconciliation: UI vs Backend Logic

This review reconciles UI-SPEC.md and LOGIC-SPEC.md with the approved feature specification and the current implementation.

## Disagreements Found

1. Clear Control Scope
   - UI-SPEC (initial): Clear action reset search input and optional filters (status, tags).
   - LOGIC-SPEC: Did not specify clearing behavior; contract requires only clearing q.

## Decisions

1. Clear Control Resets Only q
   - Decision: The Clear action resets only the title search (q). Status and tags remain unchanged. This aligns with the feature requirement ("A way to clear the search") while preserving user-applied filters.
   - Changes applied: UI-SPEC.md updated to specify that Clear resets only q and preserves status/tags.

## Assumptions (to verify as needed)

1. Duplicate Query Keys
   - Assumption: The router uses the first value per key (consistent with current parse_qs usage). Both specs reference this behavior for q, status, tags.
2. UI Handling of Stale Responses
   - Assumption: UI ignores out-of-order responses from older requests to prevent flicker. This is a UI-internal behavior and does not affect the backend contract.

## Checklist: Spec Alignment with CONTRACT.md

- [x] Method and endpoint (GET /items) consistent
- [x] Query params and semantics: q (trimmed, case-insensitive substring), status (exact), tags (ANY-of)
- [x] Interaction: AND combination, sorting unchanged and optional
- [x] Response format: array of items with id, title, url, tags, status, addedAt, readAt
- [x] HTTP statuses and error behavior aligned (200/400/5xx; no 404 for no matches)
- [x] UI states: loading, empty-results, error handling display of payload.error when present
- [x] Clear behavior: Clear resets only q and preserves status/tags
- [x] Backward compatibility requirements captured
