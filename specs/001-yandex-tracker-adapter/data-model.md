# Data Model: Yandex Tracker Adapter

**Feature**: Yandex Tracker Adapter Plugin  
**Date**: 2026-04-14  
**Purpose**: Define entities and relationships for Yandex Tracker adapter implementation

---

## Overview

The Yandex Tracker adapter operates as a stateless HTTP client that communicates with Yandex Tracker API v3. The adapter does not persist data locally — all entities are transient representations of API requests and responses.

---

## Core Entities

### 1. YandexTrackerAdapter

**Description**: Main adapter class implementing the tracker client base interface from `runtime/tracker/base.py`. Handles authentication, API communication, and issue normalization.

**Properties**:
- `__plugin_info__` (Dict[str, Any]): Plugin metadata (name, version, tracker_kind, description, author)
- `tracker_type` (str): Returns "yandex_tracker"
- `api_key` (str): OAuth token (starts with `y0__`) or IAM token (starts with `t1.`)
- `endpoint` (str): Yandex Tracker API v3 URL (default: `https://api.tracker.yandex.net/v3`)
- `timeout` (int): Request timeout in seconds (default: 30)
- `active_states` (List[str]): List of state names for filtering active issues (default: ["open", "in progress"])
- `project_slug` (str): Yandex Tracker queue key AND organization ID (used for both filtering and headers)

**Validation Rules**:
- FR-009: Constructor accepts api_key, endpoint, timeout, active_states, project_slug
- FR-011: api_key passed to Authorization header (OAuth or IAM token)
- FR-011: project_slug used for X-Org-ID (Yandex 360) or X-Cloud-Org-ID (Yandex Cloud) headers
- FR-006: Raises error if project_slug is empty when fetching candidate issues
- FR-003: tracker_type returns "yandex_tracker"

**Methods**:
- `__init__(api_key, endpoint, timeout, active_states, project_slug)`
- `authenticate() -> Dict[str, Any]`: Validates token via GET /v2/myself, returns user info
- `fetch_candidate_issues() -> List[Dict[str, Any]]`: Fetches issues from queue in active states
- `fetch_issues_by_state(states: List[str]) -> List[Dict[str, Any]]`: Fetches issues filtered by state list
- `fetch_issue_states_by_ids(issue_ids: List[str]) -> Dict[str, str]`: Returns issue_id → state mapping
- `get_issue(issue_key: str) -> Dict[str, Any]`: Fetches single issue details
- `update_issue(issue_key: str, request: UpdateIssueRequest) -> Dict[str, Any]`: Updates issue via PATCH
- `add_comment(issue_key: str, text: str) -> Dict[str, Any]`: Adds comment to issue
- `list_transitions(issue_key: str) -> List[Dict[str, Any]]`: Lists available status transitions
- `find_transition_by_status(issue_key: str, status_name: str) -> Optional[str]`: Finds transition ID by target status
- `transition_issue(issue_key: str, transition_id: str) -> Dict[str, Any]`: Executes status transition

**Relationships**:
- Implements: `TrackerClient` base interface (from `runtime/tracker/base.py`)
- Uses: `UpdateIssueRequest` for update operations
- Returns: Normalized issues (via `runtime/tracker/normalization.py`)

---

### 2. Queue (Yandex Tracker Queue)

**Description**: Yandex Tracker queue (project) used for filtering and organizing issues. Each queue has a unique key (e.g., "DESIGN", "BACKEND").

**Properties**:
- `key` (str): Unique queue identifier (e.g., "BACKEND")
- `name` (str): Human-readable queue name (e.g., "Backend Team")

**Usage**:
- `project_slug` in adapter config = queue key + organization ID
- Used in API calls: `GET /v2/issues?queue={queue_key}`
- Used in headers: `X-Org-ID: {queue_key}` or `X-Cloud-Org-ID: {queue_key}`

**Validation Rules**:
- Queue key must be non-empty (FR-006)
- Queue key is case-sensitive (SPEC.md edge cases)

---

### 3. Issue (Yandex Tracker Issue)

**Description**: Yandex Tracker issue entity representing a work item. Issues are fetched from API and normalized to standard format.

**Properties** (Yandex Tracker API fields):
- `id` (str): Internal issue UUID
- `key` (str): Unique issue identifier (e.g., "BACKEND-123")
- `summary` (str): Issue title/description
- `description` (str): Detailed issue description (markdown)
- `status` (Dict[str, Any]): Status object with `self` (status name) and `id`
- `priority` (Dict[str, Any]): Priority object with `key` (priority name) and `id`
- `type` (Dict[str, Any]): Issue type object
- `assignee` (Dict[str, Any]): Assigned user object (optional)
- `deadline` (str): Deadline timestamp (ISO 8601, optional)
- `createdAt` (str): Creation timestamp (ISO 8601, UTC±00:00)
- `updatedAt` (str): Last update timestamp (ISO 8601, UTC±00:00)
- `version` (int): Optimistic locking version number
- `queue` (Dict[str, Any]): Queue object with `self` (queue key)
- `followers` (List[Dict[str, Any]]): List of follower user objects
- `attachments` (List[Dict[str, Any]]): List of attachment objects
- `tags` (List[Dict[str, Any]]): List of tag objects
- `parent` (Dict[str, Any]): Parent issue link object (optional)
- `depends` (List[Dict[str, Any]]): List of blocking dependency links
- `follows` (List[Dict[str, Any]]): List of following link objects
- `extKey1`, `extKey2`, etc. (Dict[str, Any]): Custom field values
- `workflow` (Dict[str, Any]): Workflow settings object
- `transitions` (List[Dict[str, Any]]): List of available transition objects
- `permissions` (Dict[str, Any]): Permissions object

**Properties** (Normalized format, from `runtime/tracker/normalization.py`):
- `id` (str): Internal issue ID
- `identifier` (str): Issue key (e.g., "BACKEND-123")
- `title` (str): Issue summary
- `state` (str): Current status name
- `priority` (str): Priority level
- `created_at` (str): Creation timestamp (ISO 8601)
- `labels` (List[str]): List of tag/label names
- `blocked_by` (List[str]): List of blocking issue identifiers

**Validation Rules**:
- FR-007: Normalized issues must contain all required fields (id, identifier, title, state, priority, created_at, labels, blocked_by)
- FR-004: Normalization uses standardized utilities
- Missing fields in Yandex Tracker API response set to None or default value
- All timestamps in UTC±00:00 (SPEC.md integration requirements)

**Relationships**:
- Belongs to: Queue (via queue.key)
- May have: Parent issue (via parent)
- May depend on: Other issues (via depends)
- May have: Followers (via followers array)

---

### 4. Transition

**Description**: Available status transition for an issue. Transitions represent possible state changes in Yandex Tracker workflow.

**Properties**:
- `id` (str): Transition unique identifier (e.g., "transitions_1")
- `name` (str): Human-readable transition name
- `target_status` (str): Target status name after transition execution

**Usage**:
- List transitions: GET /v2/issues/{issue_key}/transitions
- Find transition by status: Search list for `target_status == status_name`
- Execute transition: POST /v2/issues/{issue_key}/transitions/{transition_id}

**Validation Rules**:
- Transition ID required for execution
- If transition not found for target status, raise TrackerApiError (FR-027)

**Relationships**:
- Associated with: Issue
- Leads to: Target status

---

### 5. Comment

**Description**: User comment posted to an issue. Comments provide communication trail and audit history.

**Properties**:
- `id` (str): Comment unique identifier
- `text` (str): Comment body (markdown)
- `createdBy` (Dict[str, Any]): User object who posted comment
- `createdAt` (str): Creation timestamp (ISO 8601)
- `updatedAt` (str): Last update timestamp (ISO 8601)

**Validation Rules**:
- Comment text must be non-empty
- Issue key must exist (else raise resource not found error)

**Relationships**:
- Associated with: Issue
- Created by: User (createdBy)

---

### 6. __plugin_info__ (Plugin Metadata)

**Description**: Class-level attribute containing plugin metadata for automatic discovery and documentation.

**Properties**:
- `name` (str): Plugin name (e.g., "symphony-yandex-tracker")
- `version` (str): Plugin version (e.g., "0.1.0")
- `tracker_kind` (str): Must be "yandex_tracker" (FR-025 requirement)
- `description` (str): Plugin description
- `author` (str): Plugin author/team

**Validation Rules**:
- FR-025: `tracker_kind` must be "yandex_tracker"
- FR-025: Defined as class attribute on YandexTrackerAdapter
- FR-031: Extracted by TrackerRegistry during plugin discovery

**Usage**:
- Automatically read by `importlib.metadata` via entry points
- Used by TrackerFactory for plugin information display
- Required for plugin auto-discovery (User Story 9)

---

### 7. Entry Point Configuration

**Description**: Python entry point configuration in `pyproject.toml` for automatic plugin registration.

**Configuration** (in `pyproject.toml`):
```toml
[project.entry-points."symphony.trackers"]
yandex_tracker = "symphony_yandex_tracker.adapter:YandexTrackerAdapter"
```

**Properties**:
- Entry point group: `symphony.trackers` (required by TrackerFactory)
- Entry point name: `yandex_tracker` (used as tracker kind identifier)
- Entry point reference: `symphony_yandex_tracker.adapter:YandexTrackerAdapter`

**Validation Rules**:
- FR-025: Entry point must be under `symphony.trackers` group
- FR-025: YandexTrackerAdapter must be importable via entry point reference
- FR-025: `__plugin_info__` attribute must be present on class

**Usage**:
- TrackerFactory calls `discover_from_entry_points()` to find all plugins
- Plugins loaded via `importlib.metadata.entry_points()`
- Each plugin's `__plugin_info__` extracted and registered

---

### 8. UpdateIssueRequest

**Description**: Full Issue entity for PATCH operations, supporting all Yandex Tracker API v3 fields including array operations.

**Properties**:

**Basic fields** (Optional):
- `summary` (str): Issue title
- `description` (str): Detailed description (markdown)
- `status` (str): Status name
- `priority` (str): Priority name
- `type` (str): Type name
- `assignee` (str): Assigned user ID
- `deadline` (str): Deadline timestamp (ISO 8601)
- `createdAt` (str): Creation timestamp
- `updatedAt` (str): Last update timestamp

**Array operations** (special nested objects):
- `followers` (Dict[str, Any]): Array operations for followers
  - `add` (List[str]): Append user IDs to array
  - `remove` (List[str]): Delete user IDs from array
  - `set` (List[str]): Overwrite array entirely
  - `null` (None): Clear array (empty array)

- `attachments` (Dict[str, Any]): Array operations for attachments
  - `add` (List[str]): Append attachment IDs
  - `remove` (List[str]): Delete attachment IDs
  - `set` (List[str]): Overwrite attachments entirely
  - `null` (None): Clear attachments

- `tags` (Dict[str, Any]): Array operations for tags
  - `add` (List[str]): Append tag names
  - `remove` (List[str]): Delete tag names
  - `set` (List[str]): Overwrite tags entirely
  - `null` (None): Clear tags

**Custom fields**:
- `extKey1`, `extKey2`, etc. (Any): Custom field values (extKey format from Yandex Tracker)

**System fields** (read-only in PATCH, but can be included for context):
- `id` (str): Internal issue UUID (ignored in PATCH)
- `key` (str): Issue key (ignored in PATCH)
- `queue` (str): Queue key (ignored in PATCH)
- `version` (int): Optimistic locking version (required for PATCH)

**Relationships**:
- `parent` (Dict[str, Any]): Parent issue link (self reference to issue)
- `depends` (List[Dict[str, Any]]): Blocking dependency links
- `follows` (List[Dict[str, Any]]): Following links

**Validation Rules**:
- FR-018: Supports all Yandex Tracker API v3 fields
- FR-019: Array operations support add, remove, set, null
- FR-020: Supports custom fields (extKey format)
- FR-021: Optimistic locking using `version` field
- FR-022: Validate structure before sending to API

**Example Usage**:
```python
# Append followers
request = UpdateIssueRequest(
    followers={"add": ["user1", "user2"]},
    version=5
)

# Remove tags and add new ones
request = UpdateIssueRequest(
    tags={"remove": ["deprecated"], "add": ["new-feature"]},
    version=5
)

# Clear followers
request = UpdateIssueRequest(
    followers=None,  # null operation
    version=5
)
```

---

## Relationships Summary

```
YandexTrackerAdapter
├── Uses → UpdateIssueRequest (for PATCH operations)
├── Returns → Issue (normalized via runtime/tracker/normalization.py)
├── Uses → Queue (via project_slug for filtering and headers)
├── Lists → Transition (for status changes)
├── Creates → Comment (via add_comment)
└── Has → __plugin_info__ (metadata)
    └── Registered via → Entry Point (pyproject.toml)

Issue
├── Belongs to → Queue
├── May have → Parent (Issue)
├── Depends on → Issue (via depends)
├── Follows → Issue (via follows)
├── Has → Followers (array of User)
├── Has → Tags (array of Tag)
└── Has → Transitions (array of Transition)

Transition
├── Associated with → Issue
└── Leads to → Target status

Comment
├── Associated with → Issue
└── Created by → User
```

---

## Data Flow

```
1. Initialization:
   TrackerFactory → Entry Point Discovery → YandexTrackerAdapter
   → Constructor (api_key, endpoint, timeout, active_states, project_slug)

2. Authentication:
   YandexTrackerAdapter.authenticate() → GET /v2/myself
   → Validate token → Return user info

3. Fetch Issues:
   YandexTrackerAdapter.fetch_candidate_issues() → GET /v2/issues?queue={queue_key}
   → Normalize issues → Return List[NormalizedIssue]

4. Update Issue:
   YandexTrackerAdapter.update_issue(key, UpdateIssueRequest)
   → PATCH /v2/issues/{key} → Validate version → Return updated issue

5. Status Transition:
   YandexTrackerAdapter.transition_issue(key, transition_id)
   → POST /v2/issues/{key}/transitions/{transition_id}
   → Return success result
```

---

## Validation Rules Summary

| Entity | Validation Rule | Requirement Reference |
|---------|----------------|----------------------|
| YandexTrackerAdapter | Constructor accepts api_key, endpoint, timeout, active_states, project_slug | FR-009 |
| YandexTrackerAdapter | tracker_type returns "yandex_tracker" | FR-003 |
| YandexTrackerAdapter | Raises error if project_slug empty when fetching candidate issues | FR-006 |
| YandexTrackerAdapter | Uses project_slug for X-Org-ID/X-Cloud-Org-ID headers | FR-011 |
| Issue | Normalized fields: id, identifier, title, state, priority, created_at, labels, blocked_by | FR-007 |
| Issue | Normalization via standardized utilities | FR-004 |
| UpdateIssueRequest | Supports all Yandex Tracker API v3 fields | FR-018 |
| UpdateIssueRequest | Array operations: add, remove, set, null | FR-019 |
| UpdateIssueRequest | Supports custom fields (extKey) | FR-020 |
| UpdateIssueRequest | Optimistic locking via version field | FR-021 |
| UpdateIssueRequest | Validate structure before API call | FR-022 |
| __plugin_info__ | tracker_kind must be "yandex_tracker" | FR-025 |
| Entry Point | Registered under symphony.trackers group | FR-025 |