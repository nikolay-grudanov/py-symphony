# Quick Start Guide: Yandex Tracker Adapter

**Plugin**: symphony-yandex-tracker  
**Version**: 0.1.0  
**Date**: 2026-04-14  
**Target Audience**: Symphony operators and developers integrating Yandex Tracker

---

## Prerequisites

Before using the Yandex Tracker adapter, ensure you have:

- **Python 3.11+**: Required by py-symphony constitution
- **uv**: Package management tool (required by constitution)
- **Yandex Tracker OAuth or IAM Token**: Obtain from Yandex 360 or Yandex Cloud
- **Organization ID**: Queue key for Yandex Tracker (e.g., "BACKEND", "DESIGN")
- **Yandex Tracker Queue**: Access to at least one queue in Yandex Tracker

### Obtaining OAuth Token

1. Go to Yandex 360: https://passport.yandex.ru/
2. Sign in with your Yandex account
3. Go to: https://passport.yandex.ru/profile
4. Click "Create new token"
5. Select "Tracker" service
6. Copy the token (starts with `y0__`)

### Obtaining IAM Token (Yandex Cloud)

1. Go to Yandex Cloud Console: https://console.cloud.yandex.com/
2. Create service account in IAM
3. Create IAM token for the service account
4. Copy the token (starts with `t1.`)

---

## Installation

### Install Plugin Package

```bash
# From PyPI (when published)
uv pip install symphony-yandex-tracker

# In development mode (local)
cd plugins/symphony-yandex-tracker
uv pip install -e .
```

### Verify Installation

```bash
# Check if plugin is discovered
python -c "
from runtime.tracker import TrackerFactory
factory = TrackerFactory()
print('Available trackers:', factory.list_kinds())
"

# Expected output:
# Available trackers: ['linear', 'jira', 'yandex_tracker', ...]
```

---

## Configuration

### Option 1: WORKFLOW.md Configuration (Recommended)

Add Yandex Tracker configuration to your WORKFLOW.md:

```yaml
tracker:
  kind: yandex_tracker
  api_key: ${YANDEX_TRACKER_TOKEN}
  endpoint: https://api.tracker.yandex.net/v3
  timeout: 30
  active_states: ["open", "in progress"]
  project_slug: BACKEND
```

**Configuration Fields**:
- `kind` (required): Must be `"yandex_tracker"`
- `api_key` (required): OAuth token (`y0__`) or IAM token (`t1.`)
- `endpoint` (optional): API URL. Default: `https://api.tracker.yandex.net/v3`
- `timeout` (optional): Request timeout in seconds. Default: `30`
- `active_states` (optional): List of state names for filtering. Default: `["open", "in progress"]`
- `project_slug` (required): Yandex Tracker queue key AND organization ID

### Option 2: Programmatic Configuration

```python
from symphony_yandex_tracker.adapter import YandexTrackerAdapter

# OAuth token (Yandex 360)
adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop1234567890",
    project_slug="BACKEND",
    endpoint="https://api.tracker.yandex.net/v3",
    timeout=30,
    active_states=["open", "in progress"]
)

# IAM token (Yandex Cloud)
adapter = YandexTrackerAdapter(
    api_key="t1.9e8d7f6a5b4c3d2e1f0a9b8c7d6e5f4",
    project_slug="DESIGN"
)
```

---

## Basic Usage

### 1. Authenticate

Validate your API key and retrieve user information:

```python
from symphony_yandex_tracker.adapter import YandexTrackerAdapter

adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop1234567890",
    project_slug="BACKEND"
)

try:
    user_info = adapter.authenticate()
    print(f"Authenticated as: {user_info['display_name']}")
    print(f"Login: {user_info['login']}")
except Exception as e:
    print(f"Authentication failed: {e}")
```

**Expected Output**:
```
Authenticated as: John Doe
Login: johndoe
```

### 2. Fetch Candidate Issues

Fetch issues from the configured queue in active states:

```python
try:
    issues = adapter.fetch_candidate_issues()
    print(f"Found {len(issues)} candidate issues")
    
    for issue in issues:
        print(f"  - [{issue['identifier']}] {issue['title']}")
        print(f"    State: {issue['state']}")
        print(f"    Priority: {issue['priority']}")
except Exception as e:
    print(f"Failed to fetch issues: {e}")
```

**Expected Output**:
```
Found 5 candidate issues
  - [BACKEND-123] Fix authentication bug
    State: open
    Priority: high
  - [BACKEND-124] Implement new feature
    State: in progress
    Priority: medium
  ...
```

### 3. Fetch Issues by State

Filter issues by specific states:

```python
try:
    in_progress_issues = adapter.fetch_issues_by_state(["in progress"])
    print(f"Found {len(in_progress_issues)} issues in progress")
except Exception as e:
    print(f"Failed to fetch issues: {e}")
```

### 4. Get Issue Details

Fetch full details for a specific issue:

```python
try:
    issue = adapter.get_issue("BACKEND-123")
    print(f"Issue: {issue['summary']}")
    print(f"Description: {issue['description']}")
    print(f"Status: {issue['status']['self']}")
except Exception as e:
    print(f"Failed to fetch issue: {e}")
```

### 5. Update Issue

Update issue fields:

```python
from symphony_yandex_tracker.models import UpdateIssueRequest

try:
    request = UpdateIssueRequest(
        summary="Updated title",
        description="Updated description",
        followers={"add": ["user1"]},
        version=5
    )
    updated_issue = adapter.update_issue("BACKEND-123", request)
    print(f"Updated issue: {updated_issue}")
except Exception as e:
    print(f"Failed to update issue: {e}")
```

**Supported Update Operations**:
- Basic fields: `summary`, `description`, `status`, `priority`, etc.
- Array operations:
  - `followers={"add": ["user1", "user2"]}` - Append followers
  - `followers={"remove": ["user3"]}` - Remove followers
  - `followers={"set": ["user1"]}` - Overwrite followers
  - `followers=None` - Clear followers
  - Same pattern for `attachments` and `tags`
- Custom fields: `extKey1`, `extKey2`, etc.

### 6. Add Comment

Add a comment to an issue:

```python
try:
    comment = adapter.add_comment(
        "BACKEND-123",
        "This is a comment from Symphony agent"
    )
    print(f"Comment added: {comment['id']}")
except Exception as e:
    print(f"Failed to add comment: {e}")
```

### 7. Transition Issue Status

Move issue to a different status:

```python
try:
    # List available transitions
    transitions = adapter.list_transitions("BACKEND-123")
    print("Available transitions:")
    for t in transitions:
        print(f"  - {t['name']}: {t['target_status']}")
    
    # Find transition to target status
    transition_id = adapter.find_transition_by_status("BACKEND-123", "closed")
    
    # Execute transition
    result = adapter.transition_issue("BACKEND-123", transition_id)
    print(f"Transitioned: {result}")
except Exception as e:
    print(f"Failed to transition: {e}")
```

---

## Common Workflows

### Workflow 1: Orchestrate Issues

```python
from symphony_yandex_tracker.adapter import YandexTrackerAdapter

# Initialize adapter
adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop123",
    project_slug="BACKEND",
    active_states=["open", "in progress"]
)

# Fetch candidate issues
issues = adapter.fetch_candidate_issues()
print(f"Found {len(issues)} issues to process")

# Process each issue
for issue in issues:
    print(f"Processing {issue['identifier']}...")
    
    # Fetch full issue details
    full_issue = adapter.get_issue(issue['identifier'])
    
    # Do work (e.g., call AI agent)
    result = process_issue_with_agent(full_issue)
    
    # Update issue with result
    request = UpdateIssueRequest(
        description=result['description'],
        tags={"add": ["processed"]}
    )
    adapter.update_issue(issue['identifier'], request)
    
    # Add comment
    adapter.add_comment(
        issue['identifier'],
        f"Processed by Symphony: {result['status']}"
    )
```

### Workflow 2: Active Run Reconciliation

```python
from symphony_yandex_tracker.adapter import YandexTrackerAdapter

# Initialize adapter
adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop123",
    project_slug="BACKEND"
)

# Get active run issue IDs
active_run_issue_ids = ["BACKEND-123", "BACKEND-124", "BACKEND-125"]

# Fetch current states for all active runs
current_states = adapter.fetch_issue_states_by_ids(active_run_issue_ids)

# Check if any issue is in terminal state
terminal_states = ["closed", "rejected", "cancelled"]
for issue_id, state in current_states.items():
    if state in terminal_states:
        print(f"Stopping run for {issue_id}: issue is in terminal state '{state}'")
        # Stop the active run (implementation-specific)
        stop_active_run(issue_id)
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|--------|--------|----------|
| `ConfigurationError` | `api_key` or `project_slug` is empty | Provide valid credentials and queue key |
| `TrackerApiError` | API call failed (network, rate limit, etc.) | Check network, verify API key, implement retry logic |
| `TimeoutError` | Request timeout (after configured timeout) | Increase timeout, check network connectivity |
| `ResourceNotFoundError` | Issue key doesn't exist (404) | Verify issue key exists in Yandex Tracker |
| `TransitionNotFoundError` | Transition ID not found for issue | List transitions and use correct ID |
| `ValidationError` | Invalid request structure | Check UpdateIssueRequest format |
| `ConcurrencyError` | Optimistic lock failure (409) | Fetch latest version and retry |

### Example Error Handling

```python
from symphony_yandex_tracker.errors import (
    TrackerApiError, TimeoutError, ResourceNotFoundError, ConcurrencyError
)

try:
    issue = adapter.get_issue("BACKEND-123")
    print(f"Issue: {issue['summary']}")
except ResourceNotFoundError:
    print("Issue doesn't exist")
except TimeoutError:
    print("Request timed out - retrying...")
except TrackerApiError as e:
    print(f"API error: {e}")
```

---

## Testing

### Run Unit Tests

```bash
cd plugins/symphony-yandex-tracker

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=symphony_yandex_tracker --cov-report=html

# Run specific test file
uv run pytest tests/test_adapter.py
```

### Run Integration Tests (Mocked)

```bash
# Tests use mocked Yandex Tracker API responses
uv run pytest tests/test_adapter.py -v
```

---

## Troubleshooting

### Issue 1: Plugin Not Discovered

**Symptom**: `factory.list_kinds()` doesn't include "yandex_tracker"

**Solutions**:
1. Verify installation: `uv pip list | grep symphony-yandex-tracker`
2. Check entry point configuration in `pyproject.toml`
3. Verify package is importable: `from symphony_yandex_tracker.adapter import YandexTrackerAdapter`

### Issue 2: Authentication Failure

**Symptom**: `adapter.authenticate()` raises `TrackerApiError`

**Solutions**:
1. Verify token format: OAuth starts with `y0__`, IAM starts with `t1.`
2. Check token hasn't expired (OAuth: valid, IAM: max 12 hours)
3. Verify token has Tracker permissions

### Issue 3: No Issues Returned

**Symptom**: `adapter.fetch_candidate_issues()` returns empty list

**Solutions**:
1. Verify `project_slug` (queue key) exists in Yandex Tracker
2. Check `active_states` match actual state names in Yandex Tracker
3. Verify token has read permissions for the queue

### Issue 4: Update Fails with 409 Conflict

**Symptom**: `adapter.update_issue()` raises `ConcurrencyError`

**Solutions**:
1. Fetch latest issue version before update
2. Include correct `version` in `UpdateIssueRequest`
3. Implement retry logic with version refresh

### Issue 5: Rate Limit Exceeded

**Symptom**: API returns rate limit error

**Solutions**:
1. Implement exponential backoff for retries
2. Reduce request frequency
3. Check Yandex Tracker quota limits

---

## Logging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Logs will include:
# - issue_id / issue_identifier
# - action (e.g., "fetch_candidate_issues")
# - outcome (completed/failed/timeout)
# - duration_ms
# - error_message
# - stack_trace
```

### View Logs

```bash
# Structured JSON logs (recommended)
tail -f symphony.log | jq

# Plain text logs
tail -f symphony.log
```

---

## Advanced Usage

### Custom HTTP Client Configuration

```python
import httpx

# Custom client with connection pooling
client = httpx.Client(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=10)
)

adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop123",
    project_slug="BACKEND",
    _http_client=client  # Pass custom client (if supported)
)
```

### Array Operations for Followers

```python
# Add multiple followers
request = UpdateIssueRequest(
    followers={"add": ["user1", "user2", "user3"]},
    version=5
)

# Remove specific followers
request = UpdateIssueRequest(
    followers={"remove": ["user1", "user2"]},
    version=5
)

# Overwrite all followers
request = UpdateIssueRequest(
    followers={"set": ["user4"]},
    version=5
)

# Clear all followers
request = UpdateIssueRequest(
    followers=None,  # null operation
    version=5
)
```

### Custom Fields

```python
# Update custom field (extKey format)
request = UpdateIssueRequest(
    extKey1="custom value 1",
    extKey2="custom value 2",
    version=5
)
```

---

## Reference

### API Documentation

- **Yandex Tracker API v3**: https://cloud.yandex.ru/docs/tracker/concepts/issues/issues-list
- **Authentication**: https://cloud.yandex.ru/docs/tracker/concepts/authorization/impersonation

### Plugin Documentation

- **Public API**: See `contracts/public-api.md`
- **Plugin Registration**: See `contracts/plugin-registration.md`
- **Data Model**: See `data-model.md`

### Symphony Documentation

- **SPEC.md**: Main system specification
- **Constitution**: System invariants and rules (`.specify/memory/constitution.md`)

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/nikolay-grudanov/py-symphony/issues
- **Discussions**: https://github.com/nikolay-grudanov/py-symphony/discussions

---

## License

See LICENSE file in the py-symphony repository.

---

## Changelog

### Version 0.1.0 (2026-04-14)

**Initial Release**
- ✅ Basic adapter implementation
- ✅ Public API for fetching, updating, and managing issues
- ✅ Plugin registration via entry points
- ✅ OAuth and IAM token support
- ✅ Structured logging with required context fields
- ✅ Array operations for PATCH requests
- ✅ Optimistic locking via version field

---

**Next Steps**: After installing and configuring the adapter, see [User Stories](./spec.md) for feature-specific usage examples.