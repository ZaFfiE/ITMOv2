# Data Model: Items Title Search

Entity: Item (existing)
- id: int
- title: string
- url: string
- tags: array of strings
- status: string
- addedAt: string (timestamp)
- readAt: string or null

Query Parameters
- q: optional string; trimmed; case-insensitive substring matched against Item.title; empty-after-trim treated as absent
- status: optional string; exact match against Item.status
- tags: optional string; comma-separated list; ANY-of match against Item.tags
- sort: optional string; "addedAt" or "-addedAt"; invalid/empty → 400 with {"error": "invalid sort"}

Relationships: None new introduced by this feature.

Validation Rules
- No new validation for q beyond trimming; other parameter validations unchanged.
