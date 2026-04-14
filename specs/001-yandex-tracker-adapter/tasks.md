---

description: "Task list for Yandex Tracker adapter plugin implementation"
---

# Tasks: Yandex Tracker Adapter Plugin

**Input**: Design documents from `/specs/001-yandex-tracker-adapter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Tests**: Tests are INCLUDED based on SC-004 (Basic unit tests pass without failures)
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Plugin Package**: `plugins/symphony-yandex-tracker/`
- **Source Code**: `symphony_yandex_tracker/` directory within plugin
- **Tests**: `tests/` directory within plugin

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create plugin package structure at plugins/symphony-yandex-tracker/
- [X] T002 Create pyproject.toml with project metadata, dependencies, and entry points in plugins/symphony-yandex-tracker/pyproject.toml
- [X] T003 [P] Create README.md with plugin overview, installation, and usage examples in plugins/symphony-yandex-tracker/README.md
- [X] T004 [P] Create empty test files with __init__.py in plugins/symphony-yandex-tracker/tests/
- [X] T005 Create empty __init__.py files in symphony_yandex_tracker/ and tests/ directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Define error class hierarchy (TrackerError, TrackerApiError, TimeoutError, TokenExpiredError, ResourceNotFoundError, TransitionNotFoundError, ValidationError, ConcurrencyError, ConfigurationError) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/errors.py
- [X] T007 [P] Create UpdateIssueRequest dataclass with fields for basic fields, array operations, and custom fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/models.py
- [X] T008 [P] Implement structured JSON logging formatter with required context fields (issue_id, action, outcome, duration_ms, error_message, stack_trace) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/logger.py
- [X] T009 Initialize httpx client with connection pooling and default timeout configuration in plugins/symphony-yandex-tracker/symphony_yandex_tracker/http_client.py
- [X] T010 Create YandexTrackerAdapter base class with __init__, tracker_type property, and basic configuration in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure Yandex Tracker as Issue Tracker (Priority: P1) 🎯 MVP

**Goal**: Enable Symphony orchestration platform to configure Yandex Tracker as the issue tracking system

**Independent Test**: Initialize adapter with valid OAuth token and organization ID, verify tracker type returns "yandex_tracker", and authentication endpoint returns user info

### Tests for User Story 1

- [X] T011 [P] [US1] Test adapter initialization with valid OAuth token and project_slug in tests/test_adapter.py
- [X] T012 [P] [US1] Test tracker_type property returns "yandex_tracker" in tests/test_adapter.py
- [X] T013 [P] [US1] Test lazy authentication (initialization succeeds, subsequent calls fail) in tests/test_adapter.py
- [X] T014 [P] [US1] Test authentication with valid token returns user info in tests/test_adapter.py

### Implementation for User Story 1

- [X] T015 [US1] Implement constructor with api_key, endpoint, timeout, active_states, project_slug parameters in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [X] T016 [US1] Implement tracker_type property returning "yandex_tracker" in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [X] T017 [US1] Implement token type detection (OAuth vs IAM) based on prefix in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [X] T018 [US1] Implement authenticate() method calling GET /v2/myself endpoint in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [X] T019 [US1] Add structured logging to authenticate() with action="authenticate" and all required context fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [X] T019a [US1] Implement performance monitoring to log duration_ms for all API calls in plugins/symphony-yandex-tracker/symphony_yandex_tracker/logger.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fetch Candidate Issues for Orchestration (Priority: P2)

**Goal**: Enable orchestrator to fetch active issues from Yandex Tracker queue for potential dispatch to agent execution

**Independent Test**: Configure adapter with queue key and active statuses, invoke candidate issues fetching, verify normalized issues are returned with id, identifier, title, state, priority, created_at, labels, blocked_by fields

### Tests for User Story 2

- [ ] T020 [P] [US2] Test fetch_candidate_issues returns list of normalized issues in tests/test_adapter.py
- [ ] T021 [P] [US2] Test fetch_candidate_issues raises error when project_slug is empty in tests/test_adapter.py
- [ ] T022 [P] [US2] Test fetch_candidate_issues returns empty list when no issues in active states in tests/test_adapter.py

### Implementation for User Story 2

- [ ] T023 [US2] Implement fetch_candidate_issues() method with queue and state filtering in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T024 [US2] Add validation to raise TrackerApiError if project_slug is empty before calling API in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T025 [US2] Implement pagination handling for API responses (perPage, page parameters) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T026 [US2] Integrate issue normalization using runtime/tracker/normalization.py utilities in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T027 [US2] Add structured logging to fetch_candidate_issues() with action="fetch_candidate_issues" and all required context fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Query Issues by State (Priority: P2)

**Goal**: Enable orchestrator to fetch issues filtered by specific states for state machine operations

**Independent Test**: Call issues fetching filtered by state list, verify filtered results are returned

### Tests for User Story 3

- [ ] T028 [P] [US3] Test fetch_issues_by_state returns filtered issues by state list in tests/test_adapter.py
- [ ] T029 [P] [US3] Test fetch_issues_by_state returns empty list for empty state list in tests/test_adapter.py
- [ ] T030 [P] [US3] Test fetch_issues_by_state returns empty list for non-existent state (no error) in tests/test_adapter.py

### Implementation for User Story 3

- [ ] T031 [US3] Implement fetch_issues_by_state(states: List[str]) method with state filtering in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T032 [US3] Add structured logging to fetch_issues_by_state() with action="fetch_issues_by_state" and all required context fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: User Story 4 - Fetch Issue States by IDs (Priority: P2)

**Goal**: Enable orchestrator to fetch current states for specific issue IDs for active-run reconciliation

**Independent Test**: Call fetch_issue_states_by_ids() with list of issue IDs, verify returned dictionary maps issue_id to current_state, handles empty list, and handles partial failures gracefully

### Tests for User Story 4

- [ ] T033 [P] [US4] Test fetch_issue_states_by_ids returns dictionary mapping issue_id to state in tests/test_adapter.py
- [ ] T034 [P] [US4] Test fetch_issue_states_by_ids returns empty dictionary for empty issue_ids list in tests/test_adapter.py
- [ ] T035 [P] [US4] Test fetch_issue_states_by_ids handles mix of valid and non-existent issue IDs in tests/test_adapter.py
- [ ] T036 [P] [US4] Test fetch_issue_states_by_ids raises TrackerApiError on API failures in tests/test_adapter.py

### Implementation for User Story 4

- [ ] T037 [US4] Implement fetch_issue_states_by_ids(issue_ids: List[str]) -> Dict[str, str] method in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T038 [US4] Add validation to return empty dictionary for empty issue_ids list in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T039 [US4] Implement partial failure handling (return states for valid issue IDs, log errors for failed ones) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T040 [US4] Add structured logging to fetch_issue_states_by_ids() with action="fetch_issue_states_by_ids" and all required context fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently

---

## Phase 7: User Story 5 - Get and Update Individual Issues (Priority: P2)

**Goal**: Enable orchestrator to fetch and modify specific issue details for workflow execution

**Independent Test**: Call issue retrieval with specific key and issue update method, verify full issue details are returned and updates are applied correctly

### Tests for User Story 5

- [ ] T041 [P] [US5] Test get_issue returns full issue details for valid key in tests/test_adapter.py
- [ ] T042 [P] [US5] Test get_issue raises ResourceNotFoundError for non-existent issue key in tests/test_adapter.py
- [ ] T043 [P] [US5] Test update_issue successfully updates issue and returns updated data in tests/test_adapter.py
- [ ] T044 [P] [US5] Test update_issue supports array operations (add, remove, set, null) for followers field in tests/test_adapter.py
- [ ] T045 [P] [US5] Test update_issue uses optimistic locking with version field (409 Conflict) in tests/test_adapter.py

### Implementation for User Story 5

- [ ] T046 [US5] Implement get_issue(issue_key: str) method fetching full issue details in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T047 [US5] Implement update_issue(issue_key: str, request: UpdateIssueRequest) method with PATCH operations in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T048 [US5] Implement custom JSON encoder for UpdateIssueRequest with array field transformation (add, remove, set, null) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/models.py
- [ ] T049 [US5] Add validation for UpdateIssueRequest structure before sending to API in plugins/symphony-yandex-tracker/symphony_yandex_tracker/models.py
- [ ] T050 [US5] Implement optimistic locking using version field (handle 409 Conflict) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T051 [US5] Add structured logging to get_issue() and update_issue() with action="get_issue"/"update_issue" and all required context fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 5 should be fully functional and testable independently

---

## Phase 8: User Story 6 - Manage Issue Comments (Priority: P3)

**Goal**: Enable orchestrator to add comments to issues for communication with human operators

**Independent Test**: Call comment creation method and verify comment is created

### Tests for User Story 6

- [ ] T052 [P] [US6] Test add_comment creates comment and returns comment data for valid issue key in tests/test_adapter.py
- [ ] T053 [P] [US6] Test add_comment raises ResourceNotFoundError for non-existent issue key in tests/test_adapter.py

### Implementation for User Story 6

- [ ] T054 [US6] Implement add_comment(issue_key: str, text: str) method in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T055 [US6] Add validation to raise ValueError if comment text is empty in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T056 [US6] Add structured logging to add_comment() with action="add_comment" and all required context fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 6 should be fully functional and testable independently

---

## Phase 9: User Story 7 - Transition Issue Status (Priority: P3)

**Goal**: Enable orchestrator to move issues through workflow states via transitions

**Independent Test**: Call transition listing, status finding, and issue transition methods to move an issue to a target status

### Tests for User Story 7

- [ ] T057 [P] [US7] Test list_transitions returns list of available transitions for valid issue in tests/test_adapter.py
- [ ] T058 [P] [US7] Test find_transition_by_status returns transition ID for existing status in tests/test_adapter.py
- [ ] T059 [P] [US7] Test find_transition_by_status returns None for non-existent status in tests/test_adapter.py
- [ ] T060 [P] [US7] Test transition_issue executes transition and returns success in tests/test_adapter.py
- [ ] T061 [P] [US7] Test transition_issue raises TransitionNotFoundError for non-existent transition ID in tests/test_adapter.py

### Implementation for User Story 7

- [ ] T062 [US7] Implement list_transitions(issue_key: str) method fetching available transitions in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T063 [US7] Implement find_transition_by_status(issue_key: str, status_name: str) -> Optional[str] method searching transitions by target status in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T064 [US7] Implement transition_issue(issue_key: str, transition_id: str) method executing status transition in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T065 [US7] Add structured logging to list_transitions(), find_transition_by_status(), and transition_issue() with action fields and all required context in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 7 should be fully functional and testable independently

---

## Phase 10: User Story 8 - Plugin Entry Point Registration (Priority: P1) 🎯 MVP

**Goal**: Enable system to register the adapter as a discoverable plugin via the platform's plugin system

**Independent Test**: Install plugin package, verify plugin is available under tracker plugins group, verify adapter class is importable

### Tests for User Story 8

- [ ] T066 [P] [US8] Test entry point exists in symphony.trackers group in tests/test_adapter.py
- [ ] T067 [P] [US8] Test YandexTrackerAdapter is importable from symphony_yandex_tracker.adapter in tests/test_adapter.py
- [ ] T068 [P] [US8] Test __plugin_info__ attribute is present and contains required fields in tests/test_adapter.py

### Implementation for User Story 8

- [ ] T069 [US8] Define __plugin_info__ class attribute on YandexTrackerAdapter with name, version, tracker_kind, description, author fields in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T070 [US8] Configure entry_points in pyproject.toml under symphony.trackers group with name "yandex_tracker" pointing to symphony_yandex_tracker.adapter:YandexTrackerAdapter in plugins/symphony-yandex-tracker/pyproject.toml
- [ ] T071 [US8] Ensure tracker_kind in __plugin_info__ matches entry point name ("yandex_tracker") in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py

**Checkpoint**: At this point, User Story 8 should be fully functional and testable independently

---

## Phase 11: User Story 9 - Plugin Auto-Discovery (Priority: P1) 🎯 MVP

**Goal**: Enable automatic discovery and registration of Yandex Tracker adapter via platform's plugin system without manual configuration

**Independent Test**: Install plugin package, verify TrackerRegistry discovers adapter when discover_from_entry_points() is called, verify plugin metadata is correctly extracted

### Tests for User Story 9

- [ ] T072 [P] [US9] Test TrackerRegistry discovers YandexTrackerAdapter when discover_from_entry_points() is called in tests/test_adapter.py
- [ ] T073 [P] [US9] Test plugin metadata is correctly extracted from __plugin_info__ attribute in tests/test_adapter.py
- [ ] T074 [P] [US9] Test valid tracker.kind="yandex_tracker" in WORKFLOW.md successfully instantiates YandexTrackerAdapter in tests/test_adapter.py

### Implementation for User Story 9

- [ ] T075 [US9] Verify YandexTrackerAdapter class is properly defined with __plugin_info__ attribute in plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py
- [ ] T076 [US9] Verify pyproject.toml entry point configuration is correct and plugin is discoverable in plugins/symphony-yandex-tracker/pyproject.toml
- [ ] T077 [US9] Add plugin metadata documentation in README.md explaining __plugin_info__ structure and entry point configuration in plugins/symphony-yandex-tracker/README.md

**Checkpoint**: At this point, User Story 9 should be fully functional and testable independently

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T078 [P] Update README.md with configuration examples, setup instructions, and troubleshooting guide in plugins/symphony-yandex-tracker/README.md
- [ ] T079 [P] Add sensitive information protection to logging (mask OAuth tokens, organization IDs) in plugins/symphony-yandex-tracker/symphony_yandex_tracker/logger.py
- [ ] T080 [P] Configure pytest in pyproject.toml with test discovery and coverage settings in plugins/symphony-yandex-tracker/pyproject.toml
- [ ] T081 [P] Configure mypy in pyproject.toml for type checking with strict mode in plugins/symphony-yandex-tracker/pyproject.toml
- [ ] T082 [P] Configure ruff in pyproject.toml for linting and formatting in plugins/symphony-yandex-tracker/pyproject.toml
- [ ] T083 Run quickstart.md validation to ensure all examples work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-11)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 7 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 8 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 9 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services (if applicable)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- In Phase 12: T078, T079, T080, T081, T082 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Test adapter initialization with valid OAuth token and project_slug in tests/test_adapter.py"
Task: "Test tracker_type property returns 'yandex_tracker' in tests/test_adapter.py"
Task: "Test lazy authentication in tests/test_adapter.py"
Task: "Test authentication with valid token returns user info in tests/test_adapter.py"

# Implementation tasks (sequential - depend on each other):
Task: "Implement constructor with api_key, endpoint, timeout, active_states, project_slug parameters"
Task: "Implement tracker_type property returning 'yandex_tracker'"
Task: "Implement token type detection (OAuth vs IAM) based on prefix"
Task: "Implement authenticate() method calling GET /v2/myself endpoint"
Task: "Add structured logging to authenticate() with action='authenticate'"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 8, 9 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T010) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T011-T019)
4. Complete Phase 10: User Story 8 (T066-T071)
5. Complete Phase 11: User Story 9 (T072-T077)
6. **STOP and VALIDATE**: Test adapter initialization, plugin discovery, and configuration independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP part 1)
3. Add User Story 8 → Test independently → Deploy/Demo (MVP part 2)
4. Add User Story 9 → Test independently → Deploy/Demo (MVP part 3 - MVP COMPLETE!)
5. Add User Story 2 → Test independently → Deploy/Demo
6. Add User Story 3 → Test independently → Deploy/Demo
7. Add User Story 4 → Test independently → Deploy/Demo
8. Add User Story 5 → Test independently → Deploy/Demo
9. Add User Story 6 → Test independently → Deploy/Demo
10. Add User Story 7 → Test independently → Deploy/Demo
11. Complete Phase 12: Polish → Final release
12. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1)
   - Developer B: User Story 8 (P1)
   - Developer C: User Story 9 (P1)
3. MVP stories complete and integrate independently
4. After MVP:
   - Developer A: User Story 2 (P2)
   - Developer B: User Story 3 (P2)
   - Developer C: User Story 4 (P2)
5. Continue with P3 stories (US6, US7)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All API calls must include structured logging with required context fields (FR-016)
- Sensitive information (OAuth tokens, organization IDs) must not be logged (FR-017)
- All code must pass mypy --strict, ruff check, and ruff format (constitution requirements)

---

## Status Updates

> **Workflow:** Agents must update after completing each task group or user story

| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| 2026-04-14 | build-orchestrator | pending | Initial tasks generated | tasks.md | Begin implementation Phase 1: Setup |
| 2026-04-14 | implementation-engineer | completed | Completed Phase 1 (T001-T005), Phase 2 (T006-T010), Phase 3 (T011-T019a) | tasks.md (updated) | Proceed to Phase 4: User Story 2 |

---

## Summary

- **Total Tasks**: 84 tasks
- **Tasks per User Story**:
  - US1 (P1): 10 tasks
  - US2 (P2): 8 tasks
  - US3 (P2): 5 tasks
  - US4 (P2): 8 tasks
  - US5 (P2): 11 tasks
  - US6 (P3): 5 tasks
  - US7 (P3): 9 tasks
  - US8 (P1): 6 tasks
  - US9 (P1): 6 tasks
- **Parallel Opportunities**: 26 parallel tasks across all phases
- **Independent Test Criteria**: Each user story has clear independent test criteria
- **Suggested MVP Scope**: User Stories 1, 8, 9 (all P1 stories) - 24 tasks total
- **Format Validation**: All tasks follow checklist format with checkbox, ID, labels, and file paths