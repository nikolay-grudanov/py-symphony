# Symphony Yandex Tracker Adapter

Plugin adapter for integrating Yandex Tracker with the Symphony orchestration platform.

## Overview

The `symphony-yandex-tracker` plugin provides a bridge between Symphony and Yandex Tracker, enabling orchestration workflows to interact with Yandex Tracker issues, manage statuses, transitions, and comments.

## Features

- Issue fetching and state management
- Status transitions and workflow control
- Comment management
- Structured logging with required context fields
- Support for OAuth and IAM token authentication
- Plugin auto-discovery via entry points

## Installation

```bash
cd plugins/symphony-yandex-tracker
uv pip install -e .
```

## Configuration

The adapter requires the following configuration parameters:

| Parameter | Description | Required |
|-----------|-------------|----------|
| `api_key` | OAuth or IAM token for authentication | Yes |
| `endpoint` | Yandex Tracker API endpoint URL | Yes |
| `project_slug` | Yandex Tracker queue key (e.g., "PROJ") | Yes |
| `timeout` | Request timeout in seconds (default: 30) | No |
| `active_states` | List of states considered "active" for issue fetching | No |

### Environment Variables

- `YANDEX_TRACKER_API_KEY` - API token
- `YANDEX_TRACKER_ENDPOINT` - API endpoint (default: https://api.tracker.yandex.net)
- `YANDEX_TRACKER_ORG_ID` - Organization ID for Yandex 360
- `YANDEX_TRACKER_PROJECT_SLUG` - Queue key

## Usage Example

```python
from symphony_yandex_tracker import YandexTrackerAdapter

# Initialize adapter
adapter = YandexTrackerAdapter(
    api_key="your-oauth-token",
    endpoint="https://api.tracker.yandex.net",
    project_slug="PROJ",
    active_states=["open", "in_progress"],
)

# Authenticate
await adapter.authenticate()

# Fetch candidate issues
issues = await adapter.fetch_candidate_issues()

# Get specific issue
issue = await adapter.get_issue("PROJ-123")

# Update issue
from symphony_yandex_tracker.models import UpdateIssueRequest
request = UpdateIssueRequest(summary="Updated summary")
await adapter.update_issue("PROJ-123", request)

# Transition issue
transitions = await adapter.list_transitions("PROJ-123")
await adapter.transition_issue("PROJ-123", transitions[0].id)

# Add comment
await adapter.add_comment("PROJ-123", "Task completed!")
```

## Development

### Setup

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run formatter
ruff format .

# Run type checker
mypy .
```

## Plugin Information

This plugin is auto-discovered via entry points in the `symphony.trackers` group.
The adapter class provides metadata through the `__plugin_info__` class attribute.

### `__plugin_info__` Structure

The adapter class defines a `__plugin_info__` dictionary with the following fields:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Plugin package name: `"symphony-yandex-tracker"` |
| `version` | `str` | Plugin version: `"0.1.0"` |
| `tracker_kind` | `str` | Tracker kind identifier: `"yandex_tracker"` |
| `description` | `str` | Human-readable plugin description |
| `author` | `str` | Plugin author/team: `"py-symphony team"` |

### Entry Points

```toml
[project.entry-points."symphony.trackers"]
yandex_tracker = "symphony_yandex_tracker.adapter:YandexTrackerAdapter"
```

When `TrackerRegistry.discover_from_entry_points()` is called, it:
1. Scans `symphony.trackers` entry point group
2. Loads each adapter class via `importlib.metadata.entry_points()`
3. Validates the class is a `TrackerClient` subclass
4. Extracts metadata from `__plugin_info__`
5. Registers the adapter with `source="entry_point"`

### TrackerClient Interface

The adapter implements the `TrackerClient` interface from `runtime.tracker.base`:
- `tracker_kind` → returns `"yandex_tracker"`
- `authenticate()` → validates API token
- `fetch_candidate_issues()` → returns active issues
- `fetch_issues_by_states(states)` → filters issues by state
- `get_issue(key)` → single issue lookup
- `update_issue(key, ...)` → update issue fields
- `add_comment(key, text)` → add comment
- `list_transitions(key)` → available transitions
- `transition_issue(key, transition_id)` → execute transition

## License

MIT License - see LICENSE file for details.