# Backend Logic Specification: Title Search for GET /items

Scope: Define the server-side behavior to add optional title search (q) to GET /items for the existing Reading List API, preserving current architecture and behavior.

## Existing Behavior (Reference)

- Endpoint: GET /items supports query params: status (exact match), tags (comma-separated; ANY-of), sort (addedAt | -addedAt). Unknown/empty sort → 400 with {"error": "invalid sort"}.
- Query parsing: The router parses the URL query using first-value semantics per key and keeps blank values. That is, duplicate keys are reduced to the first value; keys explicitly present with no value are represented as empty strings.
- Response format: On success, returns 200 with a JSON array of items. Each item includes at least: id, title, url, tags (array of strings), status, addedAt, readAt.
- Default ordering: When sort is omitted, results are returned in insertion order (current implementation effect). Sorting applies only if sort is provided and valid.

## New Capability: Title Search (q)

### Request: GET /items?q=...

- Parameter name: q (optional)
- Purpose: Filter items by title using case-insensitive substring matching.

### Normalization and Matching Rules

1. Trimming: The backend trims leading and trailing whitespace from the received q value before evaluating matches.
2. Empty-after-trim: If q is missing or trims to an empty string, title search is not applied. The behavior is identical to omitting q entirely.
3. Case-insensitive substring: An item matches if its title contains the normalized q as a contiguous substring, ignoring letter case. No tokenization, regex, stemming, or diacritics handling is implied beyond case-insensitive comparison.

### Combination with Existing Filters

- Conjunction: When q is applied, it combines with other filters via logical AND.
  - status: Item.status must equal the provided status (exact string match), if status is provided.
  - tags: Item.tags must intersect the provided tag set (ANY-of semantics), if tags is provided as a comma-separated list.
- Sorting: If sort is provided and valid, sorting is applied to the filtered result set according to existing rules. If sort is omitted, existing default ordering applies. Title search does not affect ordering.

### Behavior When q is Missing or Empty


### Behavior When No Items Match

- If, after applying q (and any other filters), no items satisfy the conditions, respond with HTTP 200 and an empty JSON array [].

## HTTP Status Codes and Response Format

- 200 OK: Successful request; returns a JSON array of items, possibly empty.
- 400 Bad Request: Only for existing validation rules, e.g., invalid sort values (including empty sort). The error body remains {"error": "..."} as today.
- 404 Not Found: Unchanged for other endpoints; not applicable to GET /items when filters yield no matches.
- 5xx: Uncaught exceptions produce the existing error shape (e.g., {"error": "...", "type": "..."}). Title search does not alter this behavior.

Response body items include only existing fields: id, title, url, tags, status, addedAt, readAt. No new fields are introduced by title search.

## Backward Compatibility


## Validation and Error Cases

- q content: Any string is accepted; no new validation errors are introduced for q. Trimming is applied; empty-after-trim is treated as absent.
- sort validation: Existing behavior is preserved.
  - sort omitted → no sorting (default behavior)
  - sort = "addedAt" or "-addedAt" → valid
  - sort = "" (empty string) or any other value → 400 with {"error": "invalid sort"}
- tags parsing: As an existing query parameter, tags remains a comma-separated string. Empty or missing tags results in no tag filtering.
- Multiple query keys: Only the first value per key is used by the router; later duplicates are ignored. This applies to q, status, tags, and sort.

## Unit and Integration Test Cases

The following tests specify observable behavior without dictating implementation details. They complement existing sorting tests.

### Unit-Level (ReadingList.list behavior)

1. Title Substring Match (case-insensitive)
   - Given items with titles: "Deep Learning", "Natural Language Processing"; q = "learn" → returns only "Deep Learning".
   - Given titles: "Kotlin In Action", "kOTLIN Coroutines"; q = "kotlin" → returns both items.

2. Trimming Behavior
   - q = "   Learn   " behaves identically to q = "Learn".

3. Empty q Treated as Absent
   - q missing vs q = "" vs q = "   ": identical results for the same dataset and other filters.

4. Combine with status
   - With items across statuses, q filters titles AND status exact match is applied. Only items satisfying both are returned.

5. Combine with tags (ANY-of)
   - With items tagged ["ml"] and ["nlp"], and titles including "learn"; q = "learn", tags = "ml,nlp" → returns items that contain "learn" AND have either tag.

6. Sorting Unchanged
   - With q applied, sort = "addedAt" orders ascending by existing rules; sort = "-addedAt" orders descending; absence of sort preserves default ordering.

7. No Matches → 200 []
   - q = "zzzz" returns 200 with empty array.

8. Invalid Sort with q
   - q provided, sort = "foo" → 400 with {"error": "invalid sort"}; underlying collection is not mutated.

### Integration-Level (HTTP through Router and Handler)

1. Initial List Without q
   - GET /items → 200 with current items in default order.

2. GET /items?q= (Empty Value)
   - Explicit empty q (e.g., "/items?q=") behaves as if q is absent: 200 with same results as GET /items.

3. GET /items?q=learn
   - Returns 200 with only titles containing "learn" (case-insensitive).

4. GET /items?q=learn&status=done
   - Returns 200 with titles containing "learn" and status exactly "done".

5. GET /items?q=learn&tags=ml,nlp
   - Returns 200 with titles containing "learn" and tags intersecting {ml, nlp}.

6. GET /items?q=learn&sort=-addedAt
   - Returns 200 with matching items ordered per existing descending addedAt rules.

7. GET /items?q=read&sort=
   - Returns 400 with {"error": "invalid sort"}.

8. Duplicate q Values
   - /items?q=first&q=second → only the first value ("first") is considered. Behavior aligns with existing query parsing; 200 with results for q=first.

## Non-Goals

- No search of url, tags text, or status text; search applies only to title.
- No introduction of new query parameters or response fields.
- No external dependencies or database; in-memory behavior is preserved.
