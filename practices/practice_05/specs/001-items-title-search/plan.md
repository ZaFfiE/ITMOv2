# Implementation Plan: Items Title Search

**Branch**: `001-items-title-search` | **Date**: 2026-10-27 | **Spec**: specs/001-items-title-search/spec.md

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Add optional title search to GET /items via query parameter q with case-insensitive substring match after trimming whitespace. Combine with existing status and tags filters; preserve sort semantics; return 200 with [] when no matches; maintain backward compatibility. Add a minimal HTML UI served by the existing server that calls the real API.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.x (stdlib http.server)

**Primary Dependencies**: Python standard library only

**Storage**: In-memory within ReadingList

**Testing**: unittest (extend existing suite)

**Target Platform**: Linux server

**Project Type**: Minimal HTTP service with HTML

**Performance Goals**: 95% of search responses under 1s for <=1,000 items

**Constraints**: No new dependencies; backward compatible API

**Scale/Scope**: Single-process educational service

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No explicit constraints in constitution.md. Proceed with minimal changes and tests.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
└── service.py              # HTTP server, Router, ReadingList

tests/
├── test_sorting.py         # Existing tests
├── test_search.py          # New backend tests (to be added)
└── test_ui_search.py       # New E2E tests (to be added)
```

**Structure Decision**: Single-module service with tests under tests/. Extend app/service.py minimally; add new tests as separate files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
