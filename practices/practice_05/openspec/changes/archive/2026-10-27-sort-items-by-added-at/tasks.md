# Tasks

## 1. API and Sorting Logic

- [x] 1.1 Implement `sort` handling in `ReadingList.list` (accept `addedAt`/`-addedAt`) and verify ordering with manual curl calls
- [x] 1.2 Return HTTP 400 with `{ "error": "invalid sort" }` on unknown or empty `sort` and verify via curl `GET /items?sort=foo`
- [x] 1.3 Ensure sorting composes with `status` and `tags` filters and verify combined queries (e.g., `?status=planned&sort=-addedAt`, `?tags=ml,nlp&sort=addedAt`)
- [x] 1.4 Ensure invalid sort does not mutate state (no create/update/delete) by comparing list before and after the request

## 2. Documentation and Spec

- [x] 2.1 Update OpenAPI: add `sort` query parameter (enum: `addedAt`, `-addedAt`) and 400 error for invalid sort; verify `openspec validate practices/practice_05/specs/openapi.yaml` or alternative validator passes
- [x] 2.2 Update README with examples for `sort=addedAt` and `sort=-addedAt`; verify examples run

## 3. Verification

- [x] 3.1 Baseline: create 3 items with delays, confirm default order matches insertion order via `GET /items`
- [x] 3.2 Verify ascending and descending responses match expected sequences by comparing `addedAt` values and ids as tie-breakers
- [x] 3.3 Negative tests: invalid sort value and empty sort return 400 with JSON error; confirm state unchanged

## Workflow follow-up

- Archive the change after review if specs and docs align with implementation.
