# Spec Delta

## Purpose
Provide server-side sorting of reading list items by creation time (`addedAt`) so clients can request oldest-first or newest-first ordering without client-side processing.

## ADDED Requirements

### Requirement: Items can be sorted by addedAt
The system SHALL support an optional query parameter `sort` on `GET /items` to control the order of returned items by their `addedAt` timestamp.

#### Scenario: Ascending order (oldest to newest)
- **WHEN** client calls `GET /items?sort=addedAt`
- **THEN** the response array is ordered by `addedAt` ascending

#### Scenario: Descending order (newest to oldest)
- **WHEN** client calls `GET /items?sort=-addedAt`
- **THEN** the response array is ordered by `addedAt` descending

#### Scenario: Sorting with status filter
- **WHEN** client calls `GET /items?status=planned&sort=-addedAt`
- **THEN** only items with `status=planned` are returned
- **AND** the response array is ordered by `addedAt` descending

#### Scenario: Sorting with tags filter (ANY-of semantics)
- **WHEN** client calls `GET /items?tags=ml,nlp&sort=addedAt`
- **THEN** only items whose tags intersect {"ml","nlp"} are returned
- **AND** the response array is ordered by `addedAt` ascending

#### Scenario: Absent sort keeps prior default
- **WHEN** client calls `GET /items` without `sort`
- **THEN** the order matches the current default behavior (insertion order)

#### Scenario: Invalid sort value
- **WHEN** client calls `GET /items?sort=foo`
- **THEN** the server responds with HTTP 400 and a JSON error body

#### Scenario: Deterministic order when timestamps are equal
- **WHEN** multiple items share the same `addedAt` value
- **AND** client calls `GET /items?sort=addedAt`
- **THEN** items with equal timestamps are ordered by increasing `id`

#### Scenario: Deterministic order when timestamps are equal (descending)
- **WHEN** multiple items share the same `addedAt` value
- **AND** client calls `GET /items?sort=-addedAt`
- **THEN** items with equal timestamps are ordered by decreasing `id`

#### Scenario: Invalid sort does not change state
- **WHEN** client calls `GET /items?sort=` with an empty or unsupported value
- **THEN** the server responds with HTTP 400 and a JSON error body
- **AND** no items are created, updated, or deleted
