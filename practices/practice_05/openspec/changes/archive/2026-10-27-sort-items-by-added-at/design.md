# Design

## Context

- Current API: `GET /items` returns items from in-memory store in insertion order after applying optional `status` and `tags` filters.
- Data model: `Item.addedAt` is an ISO-like UTC timestamp string (e.g., `2026-01-02T03:04:05Z`) generated at creation; lexical order matches chronological order.
- Error handling: JSON errors (`{"error":"..."}`), 400 for invalid inputs, 413 for large bodies, 404 for not found, 500 for unexpected.
- Goal: Add server-side sorting by `addedAt` with minimal code changes and no new dependencies.

## Goals / Non-Goals

**Goals:**
- Support `sort=addedAt` (ascending) and `sort=-addedAt` (descending) on `GET /items`.
- Keep default behavior unchanged when `sort` is absent.
- Sorting composes with existing filters.
- Unknown/empty sort values return 400 with JSON error.
- Deterministic order when timestamps are equal via id tie-breaker.

**Non-Goals:**
- No persistent storage or schema changes.
- No additional sort keys or multi-key sorts beyond `addedAt`.
- No pagination or stability guarantees beyond defined tie-breaker.

## Decisions

- Location: implement sorting in `ReadingList.list` after filters, before serialization, to localize behavior without touching routing.
- Sort key: primary by `addedAt` string; tie-breaker by `id` to ensure deterministic order.
  - Ascending: `(addedAt ASC, id ASC)`
  - Descending: `(addedAt DESC, id DESC)`
- Validation: accept only `"addedAt"` and `"-addedAt"` (case-sensitive); any other value (including empty) → 400 with `{ "error": "invalid sort" }`.
- Query parsing: follow existing pattern (`parse_qs(...)[0]`) — consider only the first value if multiple supplied.
- OpenAPI: document `sort` (enum: `addedAt`, `-addedAt`) and add 400 to responses for invalid sort.
- State safety: validation errors must not mutate state.

## Risks / Trade-offs

- Timestamp precision is seconds; multiple items may share `addedAt` → mitigated by `id` tie-breaker.
- Future change to `addedAt` format could affect lexical ordering → mitigate by keeping format stable (unchanged here).
- Potential behavioral expectation around default order; we explicitly preserve current default.

## Migration Plan

- Implement sorting in `ReadingList.list`.
- Update OpenAPI and README documentation.
- Manual verification via curl; optionally add lightweight tests in a follow-up if the project introduces testing.

## Open Questions

- Exact error message for invalid `sort` value: proposed `"invalid sort"`. Confirm wording if you prefer a different message.
