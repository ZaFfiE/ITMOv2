# Shared Contract: Title Search in Reading List

This contract reconciles the approved feature specification, UI-SPEC.md, LOGIC-SPEC.md, and the current Reading List implementation.

## 1. HTTP Method and Endpoint

- Method: GET
- Endpoint: /items

## 2. Query Parameters and Semantics

- q (optional, string):
  - Trim leading and trailing whitespace before use.
  - If empty after trimming, treat as absent (no title search applied).
  - When non-empty, perform case-insensitive substring match against item.title.
- status (optional, string):
  - Exact match against item.status when provided.
- tags (optional, string):
  - Comma-separated list; items match if they contain ANY of the provided tags.
- sort (optional, string; existing behavior):
  - "addedAt" or "-addedAt" are valid.
  - Omitted → default ordering (current insertion order effect).
  - Empty string or any other value → 400 with {"error": "invalid sort"}.

Query parsing notes (based on current router): only the first value per key is read; blank values are preserved (e.g., "?q=" yields q = "").

## 3. Interaction Between q, status, and tags

- All provided conditions combine via logical AND:
  - Title search (q) must match item.title.
  - Status must equal item.status, if provided.
  - Tags must intersect ANY of the provided tags, if provided.
- Sorting, when present and valid, applies to the filtered set; otherwise, default ordering applies.

## 4. JSON Response Format

- Success response body is a JSON array of items (possibly empty).
- Each item includes existing fields only:
  - id (number)
  - title (string)
  - url (string)
  - tags (array of strings)
  - status (string)
  - addedAt (string timestamp)
  - readAt (string or null)

No new fields are introduced by title search.

## 5. HTTP Status Codes and Error Behavior

- 200 OK: Successful query (including when no items match → []).
- 400 Bad Request: Existing validation applies (e.g., invalid sort value including empty string). Error body is {"error": "..."}.
- 5xx: Uncaught server errors return JSON with {"error": "...", "type": "..."} as per current behavior.
- 404 Not Found is not used for GET /items with filters yielding no matches.

## 6. UI Representation of States

- Loading: Shown while a request to GET /items is in flight. The Search button may be temporarily disabled; inputs remain usable.
- Empty Results: When the server returns 200 with an empty array, show a user-visible message indicating no matches.
- API Errors: Show an error message. If the response JSON has an "error" field, display its value; otherwise, show a generic error. The UI should not clear previously successful results solely due to an error.

## 7. Clearing the Search

- The UI Clear action resets only the title search (q) to empty and immediately fetches GET /items with the current status and tags filters unchanged. The UI omits q from the request when empty.

## 8. Backward Compatibility Requirements

- Requests without q, or with q that is empty after trimming, behave identically to current GET /items behavior.
- Existing status, tags, sort semantics and error formats remain unchanged.
- Response item shape and top-level array format remain unchanged.
