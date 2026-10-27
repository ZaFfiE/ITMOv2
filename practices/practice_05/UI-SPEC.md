# UI Specification: Reading List – Title Search

Purpose: Define a minimal web interface for searching reading list items by title, using the existing backend API and approved feature specification. This document describes user-visible behavior and states only; it does not prescribe implementation details.

## Data Source

- Backend endpoint: GET /items
- Supported query parameters relevant to this UI:
  - q: optional; case-insensitive substring match on title; leading/trailing whitespace is ignored by the backend.
  - status: optional; exact match filter on item status (free-form string).
  - tags: optional; comma-separated list; matches items that contain ANY of the provided tags.
- Response shape (array of items), per existing API:
  - id: number
  - title: string
  - url: string
  - tags: array of strings
  - status: string
  - addedAt: string (timestamp)
  - readAt: string or null

Note: The UI shall only display title, url, status, and tags (as required). Other fields MAY be used for internal sorting or future enhancements but are not displayed in this minimal scope.

## Interface Elements

1. Search input: single-line text input labeled "Search by title".
2. Search button: labeled "Search"; submits the current query.
3. Clear control: labeled "Clear"; clears only the search input and then refreshes results accordingly. Status and Tags inputs, if present, remain unchanged.
4. Optional filters (to support combination behavior):
   - Status input: single-line text input labeled "Status (exact)". Empty means no status filter.
   - Tags input: single-line text input labeled "Tags (comma-separated)". Empty means no tag filter.
   These controls are included to allow combining the title search with existing filters without prescribing specific status/tag vocabularies.
5. Results list: a vertical list of items; each item shows:
   - Title: plain text
   - URL: the item url as a clickable link (uses the url field)
   - Status: plain text
   - Tags: rendered as a comma-separated string or badges; content comes from the tags array
6. Loading indicator: non-blocking indicator (e.g., "Loading…") and temporary disabling of the Search button while a request is in progress.
7. Empty-results state: a message when the last request succeeded with an empty array (e.g., "No items match your search.").
8. Error state: a message area for request failures (e.g., network error or non-200 HTTP). If the response contains an "error" field, display its value; otherwise show a generic error message.

Accessibility and usability:
- The Search button is focusable and activatable with Enter or Space. Pressing Enter in the Search input triggers search.
- Clear control is focusable; activating it resets inputs and refreshes results.
- Labels are programmatically associated with their inputs.

## States and Behaviors

### Initial Load

- Behavior: On first render, the UI fetches GET /items without q, status, or tags to show the current list (default listing behavior). The Loading indicator appears during the request.
- Success: Show the list of items. If the array is empty, show the Empty-results state.
- Error: Show the Error state. Keep inputs enabled for retry.

### Empty Search Input

- Definition: The search input is empty or contains only whitespace after trimming.
- Behavior on submission: Do not include q in the request. The UI requests GET /items with any other filters provided (status, tags). This preserves existing listing behavior, consistent with the backend’s rule that empty q should not change results.
- Result rendering: Same as Initial Load but with any active non-q filters applied.

### Search Submission

- Trigger conditions:
  - User clicks the Search button, or
  - User presses Enter while focused in the Search input.
- Request construction:
  - Trim leading/trailing whitespace from the search input value.
  - If the trimmed value is non-empty, include q=<trimmed value> as a query parameter.
  - If the Status input is non-empty, include status=<raw value> (exact match on the backend).
  - If the Tags input is non-empty, include tags=<value> exactly as typed; users enter a comma-separated list, aligning with backend expectations.
- During request: Show Loading indicator. Disable the Search button until the request completes. Inputs remain editable for convenience; submitting again will start a new request (see Repeated Searches).
- On success (HTTP 200):
  - Render the Results list with the returned items.
  - If the array is empty, show the Empty-results state.
- On error (non-200 or network failure):
  - Show the Error state with the server-provided message if available (payload.error), else a generic message.
  - Do not replace the last successful results; the results region shows either the previous list (if any) or remains empty if no successful request has yet completed.

### No Matching Items

- Definition: The server responds 200 with an empty array for the given q/status/tags.
- Behavior: Show the Empty-results state message. Keep inputs available for refinement. The Clear control is available to remove the search and filters.

### API Errors

- Definition: Any non-200 HTTP response or network error.
- Behavior:
  - Display an error message region.
  - If the response body is JSON with an "error" field, display that string verbatim.
  - Controls remain usable so the user can retry or adjust inputs.
  - The Search button re-enables after the request completes.

### Repeated Searches

- Each submission starts a new request reflecting the current input values.
- If a prior request completes after a newer request has started, the UI displays the results of the latest request only (ignore out-of-order stale responses).
- Loading indicator appears for each request while it is in progress.

### Clearing the Search

- Activating the Clear control resets the Search input to empty. Status and Tags inputs remain as-is.
- Behavior: Immediately fetch GET /items omitting q (since empty) while preserving any non-empty status and tags filters. Show Loading during the request; then render results as for Initial Load with the current filters.

### Combining Search with Status and Tags Filters

- Status behavior: When the Status input is non-empty, include status exactly as entered. Results must match both the title search (if q included) and the status filter.
- Tags behavior: When Tags input is non-empty, include tags as a comma-separated list. Results must match both the title search (if q included) and contain ANY of the provided tags, consistent with backend semantics.
- Empty values: Omitting or leaving either filter empty excludes that filter from the request.

## Result Rendering

For each item in the results array:
- Title: Render as plain text.
- URL: Render using the url field as a clickable link (opens in the same or new tab; choice is out of scope for this spec).
- Status: Render the status field value as-is.
- Tags: Render the tags array joined by commas (e.g., "ml, nlp"). If empty, show nothing for tags.

Ordering:
- The UI does not specify custom sorting; results are displayed in the order returned by the backend.

## Validation Notes

- The UI must not hardcode search results; all data must come from GET /items.
- The UI must not assume additional response fields beyond those defined by the existing API.
- The UI should avoid sending empty query parameters for q; when the search box is empty after trimming, omit q entirely. Status and tags may be omitted when empty.
