# Proposal

## Why

Users need deterministic control over the order of items returned by GET /items. Today the list is implicitly in insertion order, which is not explicit, not stable under future changes, and cannot be reversed without client-side sorting. Adding server-side sorting on addedAt improves clarity and enables common views (newest first / oldest first) without changing storage.

## What Changes

- Add optional query parameter `sort` to `GET /items` with two accepted values:
  - `addedAt` — ascending order (oldest to newest)
  - `-addedAt` — descending order (newest to oldest)
- Sorting applies after existing filters (`status`, `tags`).
- Unknown or empty `sort` value returns HTTP 400 with JSON error.
- Default behavior unchanged when `sort` is absent (current insertion order).
- Update OpenAPI to document the `sort` parameter and 400 response for invalid sort.

## Capabilities

### New Capabilities
- reading-list/sorting: Server-side sorting of reading list items by creation time (`addedAt`) with ascending and descending options and validation of the `sort` parameter.

### Modified Capabilities

## Impact

- API surface: `GET /items` gains `sort` parameter; error 400 for invalid value.
- Implementation: minimal changes localized to `ReadingList.list` in `app/service.py`.
- Spec: OpenAPI update for query parameter and error response.
- No new dependencies; storage remains in-memory; error format remains `{ "error": "..." }`.
