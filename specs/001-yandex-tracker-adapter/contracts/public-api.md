# Public API Contract: Yandex Tracker Adapter

**Plugin**: symphony-yandex-tracker  
**Version**: 0.1.0  
**Date**: 2026-04-14  
**Purpose**: Defines the public API contract for Yandex Tracker adapter usage by Symphony orchestration platform

---

## Overview

The Yandex Tracker adapter provides a public API for integrating Yandex Tracker issue tracking capabilities with the Symphony orchestration platform. The adapter implements the `TrackerClient` base interface from `runtime/tracker/base.py` and provides methods for fetching, updating, and managing issues.

**Implementation**: `plugins/symphony-yandex-tracker/symphony_yandex_tracker/adapter.py`  
**Base Interface**: `runtime/tracker/base.py:TrackerClient`

---

## Initialization

### Constructor

```python
YandexTrackerAdapter(
    api_key: str,
    endpoint: str = "https://api.tracker.yandex.net/v3",
    timeout: int = 30,
    active_states: List[str] = ["open", "in progress"],
    project_slug: str
) -> None
```

**Parameters**:
- `api_key` (str, required): OAuth token (starts with `y0__`) or IAM token (starts with `t1.`)
- `endpoint` (str, optional): Yandex Tracker API v3 URL. Default: `"https://api.tracker.yandex.net/v3"`
- `timeout` (int, optional): Request timeout in seconds. Default: `30`
- `active_states` (List[str], optional): List of state names for filtering active issues. Default: `["open", "in progress"]`
- `project_slug` (str, required): Yandex Tracker queue key AND organization ID (used for filtering and headers)

**Validation**:
- Raises `ConfigurationError` if `api_key` is empty
- Raises `ConfigurationError` if `project_slug` is empty (lazy validation - may not raise until first API call)
- No validation on `endpoint`, `timeout`, `active_states` (defaults applied)

**Examples**:
```python
# OAuth token
adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop1234567890",
    project_slug="BACKEND"
)

# IAM token (Yandex Cloud)
adapter = YandexTrackerAdapter(
    api_key="t1.9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4",
    project_slug="DESIGN",
    endpoint="https://api.tracker.yandex.net/v3"
)
```

---

## Properties

### tracker_type

```python
adapter.tracker_type -> str
```

**Returns**: `"yandex_tracker"` (string literal)

**Purpose**: Identifies the tracker type for factory instantiation and configuration validation

**Example**:
```python
assert adapter.tracker_type == "yandex_tracker"
```

---

## Methods

### authenticate()

```python
adapter.authenticate() -> Dict[str, Any]
```

**Purpose**: Validates the API key and retrieves user information from Yandex Tracker

**Returns**: Dictionary with user information:
```python
{
    "id": "user123",
    "display_name": "John Doe",
    "login": "johndoe",
    ...
}
```

**Behavior**:
- Calls `GET /v2/myself` endpoint
- Validates that `api_key` is active and valid
- Returns user info on success
- Raises `TrackerApiError` on authentication failure

**Error Handling**:
- `TrackerApiError`: Token invalid, expired, or API error
- `TimeoutError`: Request timeout (after `timeout` seconds)

**Example**:
```python
try:
    user_info = adapter.authenticate()
    print(f"Authenticated as: {user_info['display_name']}")
except TrackerApiError as e:
    print(f"Authentication failed: {e}")
```

---

### fetch_candidate_issues()

```python
adapter.fetch_candidate_issues() -> List[Dict[str, Any]]
```

**Purpose**: Fetches issues from the configured queue that are in active states

**Returns**: List of normalized issue dictionaries. Each issue contains:
```python
{
    "id": "issue-uuid",
    "identifier": "BACKEND-123",
    "title": "Fix authentication bug",
    "state": "open",
    "priority": "high",
    "created_at": "2026-04-14T10:30:00Z",
    "labels": ["bug", "urgent"],
    "blocked_by": ["BACKEND-122"]
}
```

**Behavior**:
- Filters issues by `project_slug` (queue key)
- Filters issues by `active_states` list
- Normalizes issues via `runtime/tracker/normalization.py`
- Supports pagination (fetches all pages automatically)

**Validation**:
- Raises `TrackerApiError` if `project_slug` is empty (FR-006)
- Raises `TrackerApiError` on API failure

**Error Handling**:
- `TrackerApiError`: Queue not found, API error, network failure
- `TimeoutError`: Request timeout (after `timeout` seconds)

**Example**:
```python
try:
    issues = adapter.fetch_candidate_issues()
    print(f"Found {len(issues)} candidate issues")
    for issue in issues:
        print(f"  - {issue['identifier']}: {issue['title']}")
except TrackerApiError as e:
    print(f"Failed to fetch issues: {e}")
```

---

### fetch_issues_by_state()

```python
adapter.fetch_issues_by_state(states: List[str]) -> List[Dict[str, Any]]
```

**Purpose**: Fetches issues filtered by specific state names

**Parameters**:
- `states` (List[str], required): List of state names to filter by

**Returns**: List of normalized issue dictionaries (same format as `fetch_candidate_issues()`)

**Behavior**:
- Filters issues by `project_slug` (queue key)
- Filters issues by provided `states` list
- Returns empty list if no issues match states (no error raised)
- Supports pagination (fetches all pages automatically)

**Error Handling**:
- `TrackerApiError`: API error, network failure
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    in_progress_issues = adapter.fetch_issues_by_state(["in progress"])
    print(f"Found {len(in_progress_issues)} issues in progress")
except TrackerApiError as e:
    print(f"Failed to fetch issues: {e}")
```

---

### fetch_issue_states_by_ids()

```python
adapter.fetch_issue_states_by_ids(issue_ids: List[str]) -> Dict[str, str]
```

**Purpose**: Fetches current states for specific issue IDs (for active-run reconciliation)

**Parameters**:
- `issue_ids` (List[str], required): List of issue identifiers (e.g., ["BACKEND-123", "BACKEND-124"])

**Returns**: Dictionary mapping issue identifier to current state:
```python
{
    "BACKEND-123": "in progress",
    "BACKEND-124": "open"
}
```

**Behavior**:
- Fetches issues by their identifiers
- Returns state for valid issue IDs only
- Returns empty dictionary if `issue_ids` is empty (no error raised)
- Logs errors for failed issue IDs but returns states for valid ones

**Validation**:
- Handles empty `issue_ids` list by returning empty dictionary (no error)
- Handles non-existent issue IDs by excluding them from result (no error)
- Raises `TrackerApiError` on API failures

**Error Handling**:
- `TrackerApiError`: API error, network failure
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    issue_ids = ["BACKEND-123", "BACKEND-124", "BACKEND-999"]
    states = adapter.fetch_issue_states_by_ids(issue_ids)
    # Result: {"BACKEND-123": "in progress", "BACKEND-124": "open"}
    # BACKEND-999 is excluded (doesn't exist)
    print(f"States: {states}")
except TrackerApiError as e:
    print(f"Failed to fetch states: {e}")
```

---

### get_issue()

```python
adapter.get_issue(issue_key: str) -> Dict[str, Any]
```

**Purpose**: Fetches full details for a single issue

**Parameters**:
- `issue_key` (str, required): Issue identifier (e.g., "BACKEND-123")

**Returns**: Full issue dictionary with all Yandex Tracker API fields (not normalized)

**Behavior**:
- Fetches issue by its key
- Returns full issue data (including custom fields, attachments, etc.)
- Issue keys are case-sensitive

**Validation**:
- Raises `ResourceNotFoundError` if issue key doesn't exist

**Error Handling**:
- `ResourceNotFoundError`: Issue key not found (404)
- `TrackerApiError`: Other API errors
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    issue = adapter.get_issue("BACKEND-123")
    print(f"Issue: {issue['summary']}")
    print(f"Status: {issue['status']['self']}")
except ResourceNotFoundError as e:
    print(f"Issue not found: {e}")
except TrackerApiError as e:
    print(f"Failed to fetch issue: {e}")
```

---

### update_issue()

```python
adapter.update_issue(issue_key: str, request: UpdateIssueRequest) -> Dict[str, Any]
```

**Purpose**: Updates an issue via PATCH operation

**Parameters**:
- `issue_key` (str, required): Issue identifier (e.g., "BACKEND-123")
- `request` (UpdateIssueRequest, required): Update request with fields to modify

**Returns**: Updated issue dictionary

**Behavior**:
- Sends PATCH request to `/v2/issues/{issue_key}`
- Updates only fields specified in request
- Supports array operations (add/remove/set/null) for followers, attachments, tags
- Supports custom fields (extKey format)
- Uses optimistic locking via `version` field
- Returns 409 Conflict if version mismatch (concurrent update)

**Validation**:
- Raises `ValidationError` if `request` structure is invalid
- Raises `ResourceNotFoundError` if issue key doesn't exist
- Raises `ConcurrencyError` if version mismatch (409 Conflict)

**Error Handling**:
- `ValidationError`: Invalid request structure
- `ResourceNotFoundError`: Issue key not found (404)
- `ConcurrencyError`: Optimistic lock failure (409 Conflict)
- `TrackerApiError`: Other API errors
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    request = UpdateIssueRequest(
        summary="Updated title",
        followers={"add": ["user1"]},
        version=5
    )
    updated_issue = adapter.update_issue("BACKEND-123", request)
    print(f"Updated issue: {updated_issue}")
except ConcurrencyError as e:
    # Fetch latest version and retry
    latest = adapter.get_issue("BACKEND-123")
    request.version = latest["version"]
    adapter.update_issue("BACKEND-123", request)
except ValidationError as e:
    print(f"Invalid request: {e}")
```

---

### add_comment()

```python
adapter.add_comment(issue_key: str, text: str) -> Dict[str, Any]
```

**Purpose**: Adds a comment to an issue

**Parameters**:
- `issue_key` (str, required): Issue identifier (e.g., "BACKEND-123")
- `text` (str, required): Comment body (markdown format)

**Returns**: Created comment dictionary with ID, text, timestamp, author

**Behavior**:
- Posts comment to issue
- Comment text must be non-empty

**Validation**:
- Raises `ValueError` if `text` is empty
- Raises `ResourceNotFoundError` if issue key doesn't exist

**Error Handling**:
- `ValueError`: Comment text is empty
- `ResourceNotFoundError`: Issue key not found (404)
- `TrackerApiError`: API errors
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    comment = adapter.add_comment("BACKEND-123", "This is a comment")
    print(f"Comment added: {comment['id']}")
except ResourceNotFoundError as e:
    print(f"Issue not found: {e}")
except ValueError as e:
    print(f"Comment text cannot be empty: {e}")
```

---

### list_transitions()

```python
adapter.list_transitions(issue_key: str) -> List[Dict[str, Any]]
```

**Purpose**: Lists available status transitions for an issue

**Parameters**:
- `issue_key` (str, required): Issue identifier (e.g., "BACKEND-123")

**Returns**: List of transition dictionaries:
```python
[
    {
        "id": "transitions_1",
        "name": "Start work",
        "target_status": "in progress"
    },
    {
        "id": "transitions_2",
        "name": "Close",
        "target_status": "closed"
    }
]
```

**Behavior**:
- Fetches all available transitions for issue
- Empty list returned if issue has no available transitions

**Validation**:
- Raises `ResourceNotFoundError` if issue key doesn't exist

**Error Handling**:
- `ResourceNotFoundError`: Issue key not found (404)
- `TrackerApiError`: API errors
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    transitions = adapter.list_transitions("BACKEND-123")
    print(f"Available transitions: {len(transitions)}")
    for transition in transitions:
        print(f"  - {transition['name']}: {transition['target_status']}")
except ResourceNotFoundError as e:
    print(f"Issue not found: {e}")
```

---

### find_transition_by_status()

```python
adapter.find_transition_by_status(issue_key: str, status_name: str) -> Optional[str]
```

**Purpose**: Finds transition ID by target status name

**Parameters**:
- `issue_key` (str, required): Issue identifier (e.g., "BACKEND-123")
- `status_name` (str, required): Target status name to find

**Returns**: Transition ID (string) if found, `None` if not found

**Behavior**:
- Calls `list_transitions(issue_key)` internally
- Searches for transition with `target_status == status_name`
- Returns `None` if no matching transition found

**Error Handling**:
- `TrackerApiError`: Propagated from `list_transitions()`

**Example**:
```python
try:
    transition_id = adapter.find_transition_by_status("BACKEND-123", "closed")
    if transition_id:
        print(f"Transition ID: {transition_id}")
    else:
        print("No transition to 'closed' status found")
except TrackerApiError as e:
    print(f"Failed to find transition: {e}")
```

---

### transition_issue()

```python
adapter.transition_issue(issue_key: str, transition_id: str) -> Dict[str, Any]
```

**Purpose**: Executes a status transition for an issue

**Parameters**:
- `issue_key` (str, required): Issue identifier (e.g., "BACKEND-123")
- `transition_id` (str, required): Transition ID (from `list_transitions()`)

**Returns**: Result dictionary with updated issue data

**Behavior**:
- Executes transition via POST to `/v2/issues/{issue_key}/transitions/{transition_id}`
- Moves issue to target status

**Validation**:
- Raises `ResourceNotFoundError` if issue key doesn't exist
- Raises `TransitionNotFoundError` if transition ID doesn't exist
- Raises `TrackerApiError` on transition failure

**Error Handling**:
- `ResourceNotFoundError`: Issue key not found (404)
- `TransitionNotFoundError`: Transition ID not found for issue
- `TrackerApiError`: Transition failure
- `TimeoutError`: Request timeout

**Example**:
```python
try:
    transitions = adapter.list_transitions("BACKEND-123")
    transition_id = adapter.find_transition_by_status("BACKEND-123", "closed")
    result = adapter.transition_issue("BACKEND-123", transition_id)
    print(f"Issue transitioned: {result}")
except TransitionNotFoundError as e:
    print(f"Transition not found: {e}")
except ResourceNotFoundError as e:
    print(f"Issue not found: {e}")
```

---

## Error Hierarchy

All adapter methods raise errors from the following hierarchy:

```
TrackerError (base)
├── TrackerApiError (API call failures)
├── TimeoutError (Request timeouts)
├── ResourceNotFoundError (Issue not found)
├── TransitionNotFoundError (Transition not found)
├── ValidationError (Invalid request structure)
├── ConcurrencyError (Optimistic lock failure)
└── ConfigurationError (Invalid configuration)
```

**Usage Pattern**:
```python
from symphony_yandex_tracker.errors import (
    TrackerApiError, TimeoutError, ResourceNotFoundError
)

try:
    issue = adapter.get_issue("BACKEND-123")
except ResourceNotFoundError:
    print("Issue doesn't exist")
except TrackerApiError:
    print("API error occurred")
```

---

## Threading Model

The YandexTrackerAdapter is **thread-safe** for read operations (fetch issues, get issue, list transitions). Write operations (update issue, add comment, transition) are **not thread-safe** and should be serialized by the caller.

**Recommendation**: Use a lock or queue for write operations when accessing the same adapter instance from multiple threads.

---

## Logging

All adapter methods log structured JSON with the following context fields (FR-016):

- `issue_id` / `issue_identifier`: Tracker issue identifier
- `action`: Operation being performed (e.g., `fetch_candidate_issues`, `update_issue`)
- `outcome`: `completed`, `failed`, `timeout`
- `duration_ms`: Execution time in milliseconds
- `error_message`: Error description on failure
- `stack_trace`: Stack trace for debugging

**Sensitive Information Protection** (FR-017):
- OAuth tokens and IAM tokens are NOT logged
- Organization IDs are NOT logged
- Full user details are NOT logged

---

## Rate Limiting

Yandex Tracker API enforces rate limits. The adapter does **not** implement retry logic for rate limits. Callers should handle rate limit errors and implement exponential backoff as needed.

**Rate Limit Error Format**:
```python
{
    "error": "Rate limit exceeded",
    "limit": 100,
    "remaining": 0,
    "reset": "2026-04-14T11:00:00Z"
}
```

---

## Version Compatibility

**Adapter Version**: 0.1.0  
**Yandex Tracker API Version**: v3  
**Python Version**: 3.11+  
**Base Interface**: `runtime/tracker/base.py:TrackerClient` (required)

---

## Deprecations

None in version 0.1.0