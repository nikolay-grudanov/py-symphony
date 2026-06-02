# Implementation Plan: Yandex Tracker Adapter Plugin

**Branch**: `[001]` | **Date**: 2026-04-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-yandex-tracker-adapter/spec.md`

**Note**: This template is filled in by `/speckit.plan` command. See `.specify/templates/plan-template.md` for execution workflow.

## Summary

Implement a new tracker adapter plugin `symphony-yandex-tracker` that integrates Yandex Tracker with Symphony orchestration platform. The adapter will provide issue tracking capabilities (fetch issues, update issues, manage comments, transition statuses) via Yandex Tracker API v3. The plugin will be registered as a discoverable Python package using entry points in the `symphony.trackers` group, enabling dynamic plugin discovery by TrackerFactory. Technical approach involves implementing the tracker client base interface from `runtime/tracker/base.py` with normalized issue data, structured logging, and comprehensive error handling.

## Technical Context

**Language/Version**: Python 3.11+ (required by constitution)  
**Primary Dependencies**: httpx (async HTTP client for Yandex Tracker API v3)  
**Storage**: N/A (adapter is stateless, all data comes from Yandex Tracker API)  
**Testing**: pytest (required by constitution)  
**Target Platform**: Linux/macOS/Windows (Python package)  
**Project Type**: library/cli (Python plugin package)  
**Performance Goals**: <100ms p95 for API calls, handle pagination efficiently  
**Constraints**: 
- Tracker-agnostic architecture (no Yandex-specific code in runtime/)
- Plugin isolation (no imports from other tracker plugins)
- Structured logging with required context fields: issue_id, action, outcome, duration_ms, error_message, stack_trace
- OAuth 2.0 or IAM token authentication
- Support for both Yandex 360 (X-Org-ID) and Yandex Cloud (X-Cloud-Org-ID) headers
**Scale/Scope**: Small plugin package (~500-1000 LOC), 9 user stories, 25 functional requirements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Required Quality Gates (per constitution §8):

1. **Gate 1: ADR Creation** 
   - Required for: New plugin (tracker adapter)
   - ADR location: `docs/adr/`
   - ADR structure must include: Status, Context, Alternatives (≥2), Decision, Consequences, SPEC.md compliance

2. **Gate 2: Implementation Quality**
   - `uv run pytest` — all tests green
   - Coverage ≥ 80% (critical modules ≥ 90%)
   - `mypy --strict` — no errors
   - `ruff check` — no errors
   - `ruff format` — no errors

3. **Gate 3: Code Review**
   - code-reviewer must return APPROVED

4. **Gate 4: Verification**
   - verification-agent must return PASSED
   - SPEC.md compliance confirmed

5. **Gate 5: Merge**
   - Only permitted after Gates 1-4 passed

### Constitutional Invariants to Validate (per constitution §3):

**Tracker Agnosticism**:
- ✅ Implementation in `plugins/symphony-yandex-tracker/` (separate package)
- ✅ Entry point registration under `symphony.trackers` group
- ✅ No changes to `runtime/` required
- ✅ Verified: No direct imports - runtime only provides base.py
- ✅ Verified: Factory pattern enables dynamic plugin discovery

**Plugin Isolation** (per constitution §5):
- ✅ Plugin is separate package with independent `pyproject.toml`
- ✅ Verified: Independent package structure

**File Invariants** (per constitution §10):
- ✅ Plugin structure: `plugins/symphony-yandex-tracker/pyproject.toml`, `README.md`, `tests/`
- ✅ No tracker-specific code in `runtime/`
- ✅ No `requirements.txt` (use `uv`)

### Current Status: ✅ PASSED

**Potential Violations**: None identified in current plan

## Project Structure

### Documentation (this feature)

```text
specs/001-yandex-tracker-adapter/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Option 1: Single project (DEFAULT)
plugins/symphony-yandex-tracker/
├── pyproject.toml      # Independent package with entry_points
├── README.md
├── symphony_yandex_tracker/
│   ├── __init__.py
│   ├── adapter.py       # YandexTrackerAdapter class
│   ├── models.py        # Normalized issue models
│   ├── errors.py        # Tracker-specific error classes
│   └── __plugin_info__ # Plugin metadata (name, version, tracker_kind, etc.)
└── tests/
    ├── __init__.py
    ├── test_adapter.py
    ├── test_models.py
    └── test_errors.py

runtime/
├── tracker/
│   ├── __init__.py
│   └── base.py        # TrackerClient base interface (already exists, NO changes required)
```

**Structure Decision**: Selected Option 1 (Single project) - standard plugin structure with adapter, models, errors in one package, separate from runtime to maintain tracker-agnostic architecture.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

**No constitutional violations identified. All design decisions align with tracker-agnostic architecture and plugin isolation requirements.**

## Status Tracking

> **Workflow:** Agents must update this section after each major phase completion

| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| 2026-04-14 | build-orchestrator | pending | Initial plan created from spec.md and constitution | plan.md | Phase 0: Generate research.md |
| 2026-04-14 | build-orchestrator | completed | Phase 0 and Phase 1 design complete | research.md, data-model.md, contracts/, quickstart.md | Post-design constitution evaluation and final report |

States: `pending` → `in_progress` → `completed`
          → `blocked` / `retry_on_error` / `failed`
          → `escalation`