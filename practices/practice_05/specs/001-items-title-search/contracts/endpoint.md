# Contract: GET /items with q

Method: GET
Endpoint: /items

Query Parameters
- q: optional; trimmed; case-insensitive substring match on title; omit when empty
- status: optional; exact match on status
- tags: optional; comma-separated; ANY-of
- sort: optional; "addedAt" or "-addedAt"; invalid/empty → 400 {"error": "invalid sort"}
- 200 OK: JSON array of items (possibly empty)
  - Each item fields: id, title, url, tags, status, addedAt, readAt
- 400 Bad Request: {"error": "invalid sort"} for invalid sort values
- 5xx: {"error": "...", "type": "..."} for unhandled errors

Notes
- Filters combine with AND; tags is ANY-of set membership.
- Sorting applies after filtering; default ordering when sort omitted.
