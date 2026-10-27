# Feature Specification: Items Title Search

**Feature Branch**: `[items-title-search]`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Add title search to the existing Reading List API.

The API already supports:
- GET /items with optional status and tags filters.
- GET /items/{id}.
- POST /items.
- PATCH /items/{id}.
- DELETE /items/{id}.

Add an optional query parameter q to GET /items.

Requirements:
1. Search item titles using a case-insensitive substring match.
2. Trim leading and trailing whitespace from q.
3. Allow q to be combined with the existing status and tags filters.
4. If q is missing or empty after trimming, preserve the existing listing behavior.
5. If no items match, return HTTP 200 with an empty JSON array.
6. Preserve existing API behavior for clients that do not use q.
7. Do not introduce a database or unrelated dependencies.
8. Keep the existing project architecture and coding style.

This is an existing brownfield project. Inspect the current code before proposing changes. Do not implement the feature yet. Focus on observable behavior and acceptance criteria. "

## User Scenarios & Testing (mandatory)

### User Story 1 - Find Items by Title (Priority: P1)

As an API consumer, I can search items by a partial title so that I quickly find relevant entries without knowing the exact title.

**Why this priority**: Enables direct value discovery; core to the feature request and highest user impact.

**Independent Test**: Create multiple items with distinct titles. Call GET /items?q=substring and verify only items whose titles contain the substring (case-insensitive) are returned in HTTP 200.

**Acceptance Scenarios**:

1. Given items titled "Deep Learning" and "Natural Language Processing", When GET /items?q=learn, Then response is 200 with only "Deep Learning" included.
2. Given items titled "Kotlin In Action" and "kOTLIN Coroutines", When GET /items?q=kotlin, Then response is 200 including both items (case-insensitive match).
3. Given items exist, When GET /items?q=   Learn   (with leading/trailing spaces), Then results are identical to q=Learn (whitespace trimmed).
4. Given no items match the substring, When GET /items?q=zzzz, Then response is 200 with an empty JSON array [].

---

### User Story 2 - Combine Search with Filters (Priority: P2)

As an API consumer, I can combine title search with status and tags so that I narrow results to relevant subsets.

**Why this priority**: Maintains existing filtering power while adding search; supports focused queries.

**Independent Test**: Seed items with varying titles, statuses, and tags. Call GET /items with q plus status and/or tags, and verify results satisfy all requested conditions.

**Acceptance Scenarios**:

1. Given items where some have status=done and include "NLP" in the title, When GET /items?q=nlp&status=done, Then response is 200 with only done items whose titles contain "nlp" (case-insensitive).
2. Given items tagged ["ml"], ["nlp"], and titles including "learning" or not, When GET /items?q=learn&tags=ml,nlp, Then response is 200 with items whose titles contain "learn" and that contain any of the requested tags (ANY-of), consistent with existing tags filter semantics.
3. Given sort is provided, When GET /items?q=read&sort=-addedAt, Then response is 200 and sorted exactly as defined by existing sort behavior, applied to the filtered set.

---

### User Story 3 - Preserve Behavior When q Missing/Empty (Priority: P3)

As an API consumer, if I omit q or provide it empty after trimming, the listing behaves exactly as it does today (filters and sorting unaffected, no new errors).

**Why this priority**: Ensures backward compatibility and avoids breaking existing clients.

**Independent Test**: Compare responses for GET /items and GET /items?q= (or q="   ") and confirm identical results and status codes for the same dataset and query filters.

**Acceptance Scenarios**:

1. Given existing items, When GET /items with no q, Then response is unchanged from current behavior (e.g., default order, filters and sort rules apply as today).
2. Given existing items, When GET /items?q= (empty string) or q consisting only of spaces, Then response is identical to GET /items without q.
3. Given invalid sort inputs are currently rejected, When GET /items?q=read&sort=foo, Then response remains a 400 error with the same error semantics as today (search does not change error handling of unrelated parameters).

### Edge Cases

- q is provided but contains only whitespace characters: treat as empty; listing behavior is unchanged.
- q includes mixed case and non-alphanumeric characters: match is based on case-insensitive substring, not on tokens or regex.
- Multiple query parameters combined (q with status and/or tags): results must satisfy search plus existing filter semantics.
- No items exist: searching returns 200 with [].
- Duplicate query keys (e.g., multiple q values): only one value is considered per standard query parsing; behavior is consistent with how existing parameters are read.
- Sorting with q: sort behavior and validation are unchanged and applied to the filtered set.

## Requirements (mandatory)

### Functional Requirements

- FR-001: GET /items MUST accept an optional query parameter q.
- FR-002: If q is provided and non-empty after trimming leading/trailing whitespace, the response MUST include only items whose title contains q as a case-insensitive substring.
- FR-003: The system MUST trim leading and trailing whitespace from q before evaluating matches.
- FR-004: Title search via q MUST be combinable with existing filters: status (exact match) and tags (ANY-of semantics). All specified conditions MUST be satisfied for an item to appear in the response.
- FR-005: If q is missing or empty after trimming, the listing MUST behave exactly as it does today (no search applied). Existing filter and sort behavior, including error handling for invalid sort values, MUST remain unchanged.
- FR-006: If no items match the search (with or without additional filters), the API MUST return HTTP 200 with an empty JSON array [].
- FR-007: Search MUST NOT implicitly change result ordering; ordering is controlled only by existing sort semantics.
- FR-008: Existing clients that do not use q MUST experience no behavior changes (backward compatible). Requests without q (or with q empty after trimming) MUST return the same results as before this feature.

### Key Entities

- Item: Represents a reading list entry with at least the following fields relevant to this feature: id, title, url, tags (array of strings), status, addedAt, readAt. Title is the field considered for q-based matching.

## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: For datasets up to 1,000 items, at least 95% of search requests (GET /items with q) return results in under 1 second.
- SC-002: Functional verification demonstrates that for a representative dataset, 100% of expected matching titles are included and 0% of non-matching titles are included for given q values (case-insensitive, trimmed) across scenarios defined above.
- SC-003: When q is omitted or empty after trimming, responses (status code, items returned, and ordering) are identical to current behavior for the same inputs to other parameters.
- SC-004: Combining q with status and/or tags yields results that satisfy all specified conditions, verified across at least the scenarios listed.

## Assumptions

- Search applies only to the title field (not to url, tags, or status text).
- Case-insensitive substring matching follows conventional user expectations (no tokenization, no stemming, no regex).
- If multiple q parameters are provided, only one value is considered, consistent with existing request parsing of other parameters.
- No new storage or external dependencies are introduced; existing simple, in-memory behavior remains.
- Existing tags filter semantics (ANY-of) and status equality match semantics are unchanged.
