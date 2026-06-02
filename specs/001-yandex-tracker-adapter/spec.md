# Feature Specification: Yandex Tracker Adapter Plugin

**Feature Branch**: `[#1-yandex-tracker-adapter]`  
**Created**: 2026-04-13  
**Status**: Draft  
**Input**: User description: "Implement a new tracker adapter plugin `symphony-yandex-tracker` that integrates Yandex Tracker with the Symphony orchestration platform. This is Step 1 of the end-to-end testing MVP — the adapter only, no live e2e tests yet."

## Clarifications

### Session 2026-04-13

- Q: Yandex Tracker API endpoint, version, and authentication mechanism? → A: https://api.tracker.yandex.net/v3, OAuth 2.0 (Authorization: OAuth <token>) or IAM (Authorization: Bearer <token>), headers: X-Org-ID or X-Cloud-Org-ID
- Q: What logging context fields are required for observability? → A: issue_id, action, outcome, duration_ms, error_message, stack_trace
- Q: What fields should be included in UpdateIssueRequest for PATCH operations? → A: Full Issue entity with all supported fields including system fields, special array operations (add/remove/set/null), custom fields, and metadata

### Session 2026-04-14

- Q: Why is fetch_issue_states_by_ids() missing from spec? → A: This method is required by SPEC.md Section 11.1 for active-run reconciliation and was added to resolve the production blocker

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Yandex Tracker as Issue Tracker (Priority: P1)

Orchestrator operator needs to configure Yandex Tracker as the issue tracking system for Symphony workflows.

**Why this priority**: This is the foundational capability that enables all other user scenarios. Without tracker configuration, the orchestration platform cannot function with Yandex Tracker.

**Independent Test**: Can be fully tested by configuring the adapter with valid credentials and verifying that the tracker type identifier returns "yandex_tracker".

**Acceptance Scenarios**:

1. **Given** valid OAuth token and organization ID, **When** adapter is initialized, **Then** adapter is created without errors and tracker type returns "yandex_tracker"
2. **Given** empty authentication token, **When** adapter is initialized with missing token, **Then** initialization succeeds (lazy authentication) but subsequent API calls fail with proper error
3. **Given** configured adapter, **When** authentication method is called with valid credentials, **Then** returns user info from the authentication endpoint

---

### User Story 2 - Fetch Candidate Issues for Orchestration (Priority: P2)

Orchestrator needs to fetch active issues from Yandex Tracker queue for potential dispatch to agent execution.

**Why this priority**: This is the core workflow for the orchestration platform — identifying work items that are ready to be processed.

**Independent Test**: Can be fully tested by mocking Yandex Tracker API response and verifying that issues are returned in the normalized format with id, identifier, title, state, priority, created_at, labels, blocked_by fields.

**Acceptance Scenarios**:

1. **Given** configured queue key and active statuses, **When** candidate issues fetching is invoked, **Then** returns list of normalized issues from the queue in active states
2. **Given** empty queue key, **When** candidate issues fetching is invoked, **Then** raises tracker API error with message about missing queue key
3. **Given** no issues in active states, **When** candidate issues fetching is invoked, **Then** returns empty list

---

### User Story 3 - Query Issues by State (Priority: P2)

Orchestrator needs to fetch issues filtered by specific states for state machine operations.

**Why this priority**: Required for reconciliation logic and state-aware workflow decisions.

**Independent Test**: Can be fully tested by calling issues fetching filtered by state list and verifying filtered results.

**Acceptance Scenarios**:

1. **Given** state filter containing specific states, **When** issues are fetched by state, **Then** returns only issues in those states
2. **Given** empty state list, **When** issues are fetched by state, **Then** returns empty list
3. **Given** non-existent state, **When** issues are fetched by state, **Then** returns empty list (no error)

---

### User Story 4 - Fetch Issue States by IDs (Priority: P2)

Orchestrator needs to fetch current states for specific issue IDs for active-run reconciliation.

**Why this priority**: Required for active-run reconciliation to stop runs when issue states become terminal or no longer active. This is a critical production blocker required by SPEC.md Section 11.1.

**Independent Test**: Can be fully tested by calling fetch_issue_states_by_ids() with a list of issue IDs and verifying the returned dictionary mapping issue_id → current_state.

**Acceptance Scenarios**:

1. **Given** list of valid issue IDs, **When** issue states are fetched by IDs, **Then** returns dictionary mapping each issue_id to its current_state
2. **Given** empty list of issue IDs, **When** issue states are fetched by IDs, **Then** returns empty dictionary
3. **Given** list with mix of valid and non-existent issue IDs, **When** issue states are fetched by IDs, **Then** returns dictionary with states for only valid issue IDs
4. **Given** API error occurs during fetch, **When** issue states are fetched by IDs, **Then** raises TrackerApiError with appropriate error message

---

### User Story 5 - Get and Update Individual Issues (Priority: P2)

Orchestrator needs to fetch and modify specific issue details for workflow execution.

**Why this priority**: Required for fetching issue details before execution and updating status/fields after processing.

**Independent Test**: Can be fully tested by calling issue retrieval with specific key and issue update method.

**Acceptance Scenarios**:

1. **Given** valid issue key, **When** issue is retrieved, **Then** returns full issue details
2. **Given** non-existent issue key, **When** issue is retrieved, **Then** raises resource not found error
3. **Given** valid issue key and fields to update, **When** issue is updated, **Then** updates issue and returns updated issue data

---

### User Story 6 - Manage Issue Comments (Priority: P3)

Orchestrator needs to add comments to issues for communication with human operators.

**Why this priority**: Enables audit trail and operator communication during agent execution.

**Independent Test**: Can be fully tested by calling comment creation method and verifying comment is created.

**Acceptance Scenarios**:

1. **Given** valid issue key and comment text, **When** comment is added, **Then** creates comment and returns comment data
2. **Given** non-existent issue key, **When** comment is added, **Then** raises resource not found error

---

### User Story 7 - Transition Issue Status (Priority: P3)

Orchestrator needs to move issues through workflow states via transitions.

**Why this priority**: Required for automated status management as part of workflow execution.

**Independent Test**: Can be fully tested by calling transition listing, status finding, and issue transition methods to move an issue to a target status.

**Acceptance Scenarios**:

1. **Given** valid issue, **When** transitions are listed, **Then** returns list of available transitions
2. **Given** valid issue and target status name, **When** transition is searched by status, **Then** returns transition identifier
3. **Given** valid issue and non-existent target status, **When** transition is searched by status, **Then** raises tracker API error with available transitions
4. **Given** valid issue and target status, **When** issue status is transitioned, **Then** executes transition and returns success

---

### User Story 8 - Plugin Entry Point Registration (Priority: P1)

System needs to register the adapter as a discoverable plugin via the platform's plugin system.

**Why this priority**: Enables dynamic tracker adapter discovery by the orchestration platform.

**Independent Test**: Can be fully tested by installing the package and verifying plugin is available.

**Acceptance Scenarios**:

1. **Given** installed package, **When** plugin system is queried, **Then** adapter is registered under the tracker plugins group
2. **Given** package installed, **When** import is attempted, **Then** adapter class is importable by the orchestration platform

---

### User Story 9 - Plugin Auto-Discovery (Priority: P1)

System needs to automatically discover and register the Yandex Tracker adapter via the platform's plugin system without manual configuration.

**Why this priority**: This is critical for the adapter to work with the TrackerFactory. Without proper entry point registration, the adapter will not be discoverable and cannot be instantiated from WORKFLOW.md configuration.

**Independent Test**: Can be tested by installing the plugin package and verifying that the TrackerRegistry discovers the adapter when `discover_from_entry_points()` is called.

**Acceptance Scenarios**:

1. **Given** installed plugin package with entry point configuration, **When** the TrackerRegistry scans for plugins via `discover_from_entry_points()`, **Then** the Yandex Tracker adapter is discovered and registered
2. **Given** plugin package installed, **When** the adapter class is loaded, **Then** the `__plugin_info__` attribute is correctly extracted and metadata is available
3. **Given** valid tracker.kind="yandex_tracker" in WORKFLOW.md, **When** TrackerFactory attempts to create an adapter instance, **Then** the YandexTrackerAdapter is successfully instantiated
4. **Given** plugin without entry point configuration, **When** plugin is installed, **Then** discovery fails with appropriate warning and adapter is not registered

---

### Integration & External Dependencies

**Yandex Tracker API v3:**

- **Base URL**: `https://api.tracker.yandex.net/v3`
- **Authentication Methods**:
  - OAuth 2.0: `Authorization: OAuth <token>` (token starts with `y0__`)
  - IAM Token: `Authorization: Bearer <token>` (token starts with `t1.`)
- **Required Headers**:
  - `Authorization`: OAuth or IAM token
  - `X-Org-ID`: Organization ID (for Yandex 360)
  - `X-Cloud-Org-ID`: Organization ID (for Yandex Cloud)
- **Response Format**: JSON
- **HTTP Methods**: GET, POST, PATCH, DELETE
- **Pagination**:
  - Query parameters: `perPage` (default 50), `page` (default 1)
  - Response headers: `X-Total-Pages`, `X-Total-Count`
- **Timezone**: UTC±00:00 for all timestamps
- **Rate Limits**: Dependent on Yandex Tracker quota limits

### Non-Functional Requirements

#### Observability

The adapter MUST provide structured logging with the following context fields:

**Required Context Fields:**
- `issue_id` / `issue_identifier`: Tracker issue identifier (for log correlation)
- `action`: Operation being performed (e.g., `fetch_candidate_issues`, `update_issue`, `add_comment`, `fetch_issue_states_by_ids`)
- `outcome`: Result of operation (e.g., `completed`, `failed`, `timeout`)
- `duration_ms`: Execution time in milliseconds (for API calls and performance monitoring)
- `error_message`: Error description when operation fails
- `stack_trace`: Stack trace for debugging when errors occur

**Logging Best Practices:**
- All API calls MUST log with full context (all required fields)
- Log level MUST be appropriate: INFO for normal operations, ERROR for failures, DEBUG for detailed troubleshooting
- Sensitive information (OAuth tokens, organization IDs) MUST NOT be logged
- Structured logging format (JSON preferred) for automated analysis
- Logs MUST be timestamped in UTC±00:00

### Edge Cases

- **Empty queue**: Returns empty list when no issues match filters — no error raised
- **Invalid OAuth token**: Returns authentication error — wrapped in appropriate tracker error class
- **Network timeout**: Request timeout after configured duration — wrapped in timeout error class
- **Rate limiting**: API rate limit hit — wrapped in rate limit error class with retry information
- **Missing queue_key for candidate fetching**: Must raise tracker API error — this is a configuration validation error
- **Issue key case sensitivity**: Yandex Tracker keys are case-sensitive — pass through as-is to API
- **Empty issue_ids list**: Returns empty dictionary when fetch_issue_states_by_ids() is called with empty list — no error raised
- **Partial failure in issue states fetch**: Returns dictionary with states for valid issue IDs, logs errors for failed ones

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The adapter MUST implement all abstract methods from the tracker client base interface
- **FR-002**: The adapter MUST communicate with Yandex Tracker API using approved HTTP client methods (NOT raw HTTP requests)
- **FR-003**: The adapter MUST return "yandex_tracker" from the tracker type property
- **FR-004**: The adapter MUST normalize Yandex Tracker issues using standardized normalization utilities consistent with other tracker adapters
- **FR-005**: The adapter MUST define local error classes: tracker API error, request error, status error, rate limit error, timeout error, resource not found error
- **FR-006**: The adapter MUST require project_slug (queue key) for candidate issues fetching and raise error if empty
- **FR-007**: The adapter MUST be registered as a discoverable plugin in the orchestration platform's plugin system
- **FR-008**: The adapter MUST expose plugin information including name, version, tracker type, description, author
- **FR-009**: Constructor MUST accept: api_key (OAuth or IAM token), endpoint (Yandex Tracker API URL, default: https://api.tracker.yandex.net/v3), timeout (default 30 seconds), active_states (list of state names, default: ["open", "in progress"]), project_slug (queue key for Yandex Tracker, default: empty). The adapter MUST: Use api_key as OAuth or IAM token (pass through to Authorization header), Use project_slug as Yandex Tracker queue key for filtering issues (e.g., "QUEUE-1") AND as organization ID for X-Org-ID/X-Cloud-Org-ID headers (e.g., "1234567890"). The same value is used for both purposes - no separate organization_id parameter is needed. Support Yandex 360 (X-Org-ID) and Yandex Cloud (X-Cloud-Org-ID) organization types by detecting which header to use based on token format or configuration, Accept both organization ID types and use the appropriate header for all API calls
- **FR-010**: Authentication MUST call the authentication endpoint to validate api_key and return user information
- **FR-011**: All API calls MUST include required authentication headers: Authorization header with api_key (OAuth or IAM token), and X-Org-ID (for Yandex 360) or X-Cloud-Org-ID (for Yandex Cloud) header derived from project_slug (organization ID)
- **FR-012**: The adapter MUST use Yandex Tracker API v3 (not v2)
- **FR-013**: The adapter MUST support pagination using perPage (default 50) and page (default 1) parameters
- **FR-014**: The adapter MUST handle IAM token expiration (12 hour max lifetime). When an IAM token expires (401 Unauthorized response), the adapter MUST raise a TokenExpiredError with clear message indicating token needs refresh. The refresh mechanism is the responsibility of the user - they must obtain a new IAM token and re-initialize the adapter. The adapter does NOT implement automatic token refresh.
- **FR-015**: The adapter MUST parse JSON responses from Yandex Tracker API
- **FR-016**: The adapter MUST log all operations with required context fields: issue_id/issue_identifier, action, outcome, duration_ms, error_message, stack_trace
- **FR-017**: The adapter MUST NOT log sensitive information (OAuth tokens, organization IDs, full user details)
- **FR-018**: The adapter MUST support PATCH operations with full Issue entity including all supported Yandex Tracker API v3 fields. Validation must ensure: (1) Only supported Yandex Tracker API v3 fields are included, (2) Array operations (add, remove, set, null) are properly formatted, (3) Custom fields use extKey format (e.g., extKey1, extKey2), (4) Version field is included for optimistic locking (see FR-021), (5) Unsupported fields are stripped before sending to API to avoid 400 errors.
- **FR-019**: The adapter MUST support array operations for followers: add (append), remove (delete items), set (overwrite), null (clear array)
- **FR-020**: The adapter MUST handle custom fields (extKey format) in update requests
- **FR-021**: The adapter MUST support optimistic locking using version field for concurrent updates. The version field is obtained from the Issue entity retrieved via get_issue() or fetch_candidate_issues(). When sending an update request, the version field from the current Issue state MUST be included. If another client has modified the issue, Yandex Tracker API returns 409 Conflict error, which the adapter MUST raise as a ConcurrencyError with appropriate message.
- **FR-022**: The adapter MUST validate UpdateIssueRequest structure before sending to API (remove unsupported fields, format special operations correctly)
- **FR-023**: The adapter MUST implement `fetch_issue_states_by_ids(issue_ids: List[str]) -> Dict[str, str]` method that returns a dictionary mapping issue_id to current_state, raises TrackerApiError on API failures, handles empty lists by returning empty dictionary, and gracefully handles partial failures by returning states for valid issue IDs
- **FR-024**: The adapter MUST map standard tracker configuration fields to Yandex Tracker-specific requirements: tracker.api_key → OAuth or IAM token for Authorization header, tracker.endpoint → Yandex Tracker API v3 endpoint (default: https://api.tracker.yandex.net/v3), tracker.active_states → Yandex Tracker state names for active issues, tracker.project_slug → Yandex Tracker queue key (for filtering issues, e.g., "QUEUE-1") AND organization ID (for X-Org-ID/X-Cloud-Org-ID headers, e.g., "1234567890"). Support Yandex 360 (X-Org-ID) and Yandex Cloud (X-Cloud-Org-ID) organization types by detecting which header to use based on token format: tokens starting with "y0__" use X-Org-ID header, tokens starting with "t1." use X-Cloud-Org-ID header. If token format is unrecognized, default to X-Org-ID header and log a warning.
- **FR-025**: The adapter MUST be registered as a discoverable plugin via Python entry points in the `symphony.trackers` group. The package MUST include an entry point configuration that registers the YandexTrackerAdapter class with kind identifier "yandex_tracker". The adapter class MUST define a `__plugin_info__` attribute containing metadata including name, version, tracker_kind (must be "yandex_tracker"), description, and author fields.

### Key Entities

- **YandexTrackerAdapter**: Main adapter class implementing tracker client interface
- **Queue**: Yandex Tracker queue for filtering issues
- **Issue**: Yandex Tracker issue with key, summary, status, priority
- **Transition**: Available status transitions for an issue
- **Comment**: Issue comment posted via API
- **__plugin_info__**: Plugin metadata dictionary containing name, version, tracker_kind, description, author fields
- **Entry Point**: Python entry point configuration for automatic plugin discovery in `symphony.trackers` group
- **UpdateIssueRequest**: Full Issue entity for PATCH operations supporting all Yandex Tracker API v3 fields including:
  - **Basic fields**: summary, description, status, priority, type, assignee, deadline, createdAt, updatedAt
  - **Array operations**: followers (supports add, remove, set, null), attachments, tags
  - **Custom fields**: extKey fields (e.g., extKey1, extKey2) for custom field values
  - **System fields**: id, key, queue, version (for optimistic locking)
  - **Relationships**: parent (link to parent issue), depends (blocking links), follows (following links)
  - **Metadata**: workflow settings, transitions, permissions
  - **Special operations**: Null values to clear fields, empty objects for no-change

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Adapter plugin is properly structured and installed in the plugin system
- **SC-002**: Adapter class successfully implements all tracker client interface methods without errors
- **SC-003**: Adapter can be imported and instantiated by the orchestration platform
- **SC-004**: Basic unit tests pass without failures
- **SC-005**: Tracker type returns "yandex_tracker" when called on adapter instance
- **SC-006**: Candidate issues fetching raises appropriate error when project_slug (queue key) is empty
- **SC-007**: Issues normalized via standardized utilities contain all required fields: id, identifier, title, state, priority, created_at, labels, blocked_by
- **SC-008**: Documentation includes configuration examples and setup instructions
- **SC-009**: Package installs without conflicts
- **SC-010**: Adapter uses approved HTTP client library for API communication
- **SC-011**: All adapter operations log with required context fields (verified via log inspection)
- **SC-012**: Sensitive information is not logged (verified via log inspection and security audit)
- **SC-013**: API response times are logged with duration_ms for performance monitoring. Target performance: <100ms p95 for API calls as specified in plan.md line 20. Responses exceeding this threshold should be logged at WARN level with context (issue_id, endpoint, duration_ms). Responses exceeding 500ms should be logged at ERROR level.
- **SC-014**: PATCH operations support all Issue fields including system fields, custom fields, and array operations
- **SC-015**: Array operations (add/remove/set/null) work correctly for followers field
- **SC-016**: Optimistic locking prevents concurrent update conflicts when using version field
- **SC-017**: Custom fields (extKey format) are properly formatted and sent in update requests
- **SC-018**: fetch_issue_states_by_ids() method correctly returns issue_id → state mapping, handles empty lists and non-existent issue IDs correctly, and properly wraps API errors in TrackerApiError
- **SC-019**: Plugin package includes entry point registration in `symphony.trackers` group for YandexTrackerAdapter class with kind "yandex_tracker", and adapter class exposes `__plugin_info__` attribute with required metadata fields
- **SC-020**: IAM token expiration raises TokenExpiredError with clear message requiring manual token refresh.

## Assumptions

- **Yandex Tracker API**: Assumes Yandex Tracker REST API is stable and backward compatible
- **OAuth token**: Token is pre-obtained via Yandex OAuth (not implementing OAuth 2.0 flow)
- **Network**: User has network access to Yandex Tracker API
- **Permissions**: Token has read and write scopes for tracker
- **Testing**: Unit tests use mocked responses, no live API calls in test suite
- **Python version**: Target Python 3.11+ (required by constitution §2).
- **Dependencies**: Approved HTTP client library is available on package repositories
- **API Version**: Uses Yandex Tracker API v3 (recommended current version)
- **IAM Token Lifetime**: IAM tokens have maximum 12 hour lifetime, adapter should handle refresh
- **Organization Types**: Supports both Yandex 360 (X-Org-ID) and Yandex Cloud (X-Cloud-Org-ID)
- **PATCH Semantics**: Yandex Tracker API v3 supports partial updates — only explicitly specified fields are modified, null values clear fields
- **Issue States by IDs**: Yandex Tracker API supports querying multiple issues by their IDs in a single request for efficient state reconciliation

## Status Tracking

> **Workflow:** Agents must update this section after spec phases (draft → review → approved)

| Date | Agent | Status | Changes | Artifacts | Next Steps |
|------|-------|--------|---------|-----------|-----------|
| 2026-04-13 | doc-writer | draft | Initial spec created from GitHub issue #1 | spec.md | Review by architecture-review |
| 2026-04-14 | platform-architect | draft | Added User Story 4 (Fetch Issue States by IDs), FR-023, SC-018, renumbered existing User Stories 4-7 to 5-8 to resolve SPEC.md Section 11.1 production blocker | spec.md | Review by code-reviewer |
| 2026-04-14 | platform-architect | draft | Fixed Issue #2: Updated FR-006, FR-009, FR-010, FR-011, SC-006 to align with TrackerFactory standard configuration, added FR-024 for configuration mapping between standard tracker config and Yandex-specific fields | spec.md | Review by code-reviewer |
| 2026-04-14 | platform-architect | draft | Fixed Critical Issues #1 and #2: Removed terminal_states from FR-009 and FR-024 (TrackerFactory doesn't pass this parameter), clarified organization ID handling in FR-009, FR-011, and FR-024 to explicitly state that project_slug serves dual purposes as queue key and organization ID for X-Org-ID/X-Cloud-Org-ID headers | spec.md | Review by code-reviewer |
| 2026-04-14 | integration-architect | draft | Added Issue #3 requirements: FR-025 for plugin entry point registration, User Story 9 for plugin auto-discovery, SC-019 for plugin metadata, added Key Entities for __plugin_info__ and Entry Point | spec.md | Review by code-reviewer |

States: `draft` → `in_review` → `approved` | `rejected` → `escalation`
