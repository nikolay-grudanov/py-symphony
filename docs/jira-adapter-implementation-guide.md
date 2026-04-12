# Jira Adapter Implementation Guide

This guide provides condensed, implementation-ready documentation for building the Jira adapter (`runtime/tracker/jira.py`) to integrate with the Symphony orchestration platform.

**Reference Implementation**: See `runtime/tracker/linear.py` (424 lines) for patterns, error handling, and structure.

---

## Table of Contents

1. [Quick Reference Table](#1-quick-reference-table)
2. [Authentication Setup](#2-authentication-setup)
3. [ADF Format Reference](#3-adf-format-reference)
4. [JQL Query Examples](#4-jql-query-examples)
5. [Pagination Pattern](#5-pagination-pattern)
6. [Error Handling](#6-error-handling)
7. [Transition Workflow](#7-transition-workflow)
8. [Field Updates](#8-field-updates)
9. [Rate Limiting Best Practices](#9-rate-limiting-best-practices)
10. [Implementation Notes](#10-implementation-notes)

---

## 1. Quick Reference Table

### `authenticate()`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `GET /rest/api/3/myself` |
| **HTTP Method** | GET |
| **Auth Header** | `Authorization: Basic <base64(email:api_token)>` |
| **Purpose** | Validate credentials and get user info |
| **Response** | User object with accountId, email, displayName |
| **Error Handling** | 401 if invalid credentials |

### `fetch_issues(query: str)`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `POST /rest/api/3/search` ⚠️ **DEPRECATED** |
| **HTTP Method** | POST |
| **Required Params** | `jql` (string), `startAt`, `maxResults`, `fields` |
| **Request Body** | `{"jql": "project=KEY AND status='To Do'", "startAt": 0, "maxResults": 50, "fields": ["summary", "status", ...]}` |
| **Response** | `{ "issues": [...], "total": 100, "startAt": 0, "maxResults": 50 }` |
| **Pagination** | Use `startAt` offset, NOT cursor-based |
| **⚠️ Warning** | Endpoint scheduled for removal May 1, 2025 |

### `get_issue(issue_id: str)`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `GET /rest/api/3/issue/{issueIdOrKey}` |
| **HTTP Method** | GET |
| **Required Params** | `issueIdOrKey` (e.g., "PROJ-123") |
| **Response** | Full issue object with fields, transitions, metadata |
| **Optional Fields** | `fields`, `expand`, `properties` |

### `update_issue(issue_id: str, fields: dict)`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `PUT /rest/api/3/issue/{issueIdOrKey}` |
| **HTTP Method** | PUT |
| **Request Body** | `{ "fields": { "summary": "...", "assignee": {"accountId": "..."} } }` |
| **Response** | Updated issue object |
| **Common Fields** | summary, description, assignee, priority, labels, components |
| **404** | Issue not found |

### `add_comment(issue_id: str, body: str)`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `POST /rest/api/3/issue/{issueIdOrKey}/comment` |
| **HTTP Method** | POST |
| **Request Body** | `{ "body": { "type": "doc", "version": 1, "content": [...] } }` |
| **Body Format** | ADF (Atlassian Document Format) - see Section 3 |
| **Response** | Created comment object |

### `list_transitions(issue_id: str)`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `GET /rest/api/3/issue/{issueIdOrKey}/transitions` |
| **HTTP Method** | GET |
| **Response** | `{ "transitions": [{ "id": "123", "name": "To Do", "to": { "name": "To Do" } }, ...] }` |
| **Use Case** | Get available transitions before transitioning |

### `transition_issue(issue_id: str, transition_id: str)`

| Aspect | Details |
|--------|---------|
| **Endpoint** | `POST /rest/api/3/issue/{issueIdOrKey}/transitions` |
| **HTTP Method** | POST |
| **Request Body** | `{ "transition": { "id": "123" } }` |
| **Response** | Updated issue object |
| **Prerequisite** | Call `list_transitions` first to get valid `transition_id` |

---

## 2. Authentication Setup

### Environment Variables

```python
import os

JIRA_URL = os.getenv("JIRA_URL", "https://company.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "user@company.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "your-api-token")
```

### Basic Auth Header Format

```python
import base64
import requests

# Create Basic Auth header
def get_auth_header(email: str, api_token: str) -> dict:
    credentials = f"{email}:{api_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

# Usage
headers = get_auth_header(JIRA_EMAIL, JIRA_API_TOKEN)
headers["Content-Type"] = "application/json"

response = requests.get(
    f"{JIRA_URL}/rest/api/3/myself",
    headers=headers,
    timeout=30
)
```

### Authentication Validation

```python
def authenticate(self) -> None:
    """Initialize connection and validate credentials."""
    response = self._request("GET", "/rest/api/3/myself")
    if response.status_code == 401:
        raise TrackerApiStatusError("Invalid Jira credentials")
    self._user = response.json()
```

### OAuth2 Scopes (Future Support)

If OAuth2 is needed in the future, these are the required scopes:

| Scope | Description |
|-------|-------------|
| `read:jira-work` | Read issue data |
| `write:jira-work` | Modify issue data |
| `read:jira-user` | Read user data |
| `offline_access` | Refresh tokens |

---

## 3. ADF Format Reference

### Plain Text to ADF Conversion

```python
def text_to_adf(text: str) -> dict:
    """Convert plain text to Atlassian Document Format."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    }

# Example
adf = text_to_adf("This is a comment")
# {
#     "type": "doc",
#     "version": 1,
#     "content": [
#         {
#             "type": "paragraph",
#             "content": [{"type": "text", "text": "This is a comment"}]
#         }
#     ]
# }
```

### ADF for Bold Text

```python
def bold_text_to_adf(text: str) -> dict:
    """Convert bold text to ADF."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "marks": [{"type": "strong"}]
                    }
                ]
            }
        ]
    }
```

### ADF for Multi-line Content

```python
def multiline_to_adf(lines: list[str]) -> dict:
    """Convert multiple lines to ADF."""
    content = []
    for line in lines:
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": line}]
        })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }
```

### ADF Schema Summary

| Element | Type | Structure |
|---------|------|------------|
| Document | `doc` | `{type, version, content: [...], attrs?}` |
| Paragraph | `paragraph` | `{type, content: [inline]}` |
| Text | `text` | `{type, text, marks?: [{type}]}` |
| Bold | `strong` | `marks: [{type: "strong"}]` |
| Italic | `em` | `marks: [{type: "em"}]` |
| Code | `code` | `marks: [{type: "code"}]` |

---

## 4. JQL Query Examples

### Common Queries Matching Linear Patterns

```python
# Active issues (equivalent to Linear's "Todo", "In Progress")
JQL_ACTIVE = 'project = {project_key} AND status IN ("To Do", "In Progress")'

# All issues in project
JQL_ALL = 'project = {project_key} ORDER BY created DESC'

# Issues assigned to current user
JQL_MY_ISSUES = 'assignee = currentUser() AND status != Done'

# Issues updated recently (last 24 hours)
JQL_RECENTLY_UPDATED = 'project = {project_key} AND updated >= -24h'

# Find by specific status
JQL_BY_STATUS = 'project = {project_key} AND status = "In Progress"'

# Find by priority
JQL_HIGH_PRIORITY = 'project = {project_key} AND priority IN (Highest, High)'

# Find by labels
JQL_WITH_LABEL = 'project = {project_key} AND labels = "needs-review"'

# Combine multiple conditions
JQL_COMPLEX = 'project = {project_key} AND status IN ("To Do", "In Progress") AND priority = High ORDER BY created DESC'
```

### Project-Specific Queries

```python
# Filter by project key (required for most queries)
def build_project_query(project_key: str, statuses: list[str]) -> str:
    status_list = ", ".join([f'"{s}"' for s in statuses])
    return f'project = {project_key} AND status IN ({status_list})'
```

### Status-Based Queries

```python
# Standard Jira statuses
JIRA_STATUSES = {
    "to_do": "To Do",
    "in_progress": "In Progress", 
    "in_review": "In Review",
    "done": "Done",
    "cancelled": "Cancelled"
}

# Build status filter
def build_status_filter(status_names: list[str]) -> str:
    quoted = [f'"{s}"' for s in status_names]
    return f"status IN ({', '.join(quoted)})"
```

---

## 5. Pagination Pattern

### ⚠️ Critical: Deprecated Endpoint Warning

The `/rest/api/3/search` endpoint is **DEPRECATED** and scheduled for removal on **May 1, 2025**.

**Recommended Alternative**: Use issue-specific endpoints with the `fields` parameter when possible, or implement server-side pagination with `startAt`.

### Offset-Based Pagination

```python
def fetch_all_issues(self, jql: str, max_results: int = 50) -> list[dict]:
    """Fetch all issues with pagination."""
    all_issues = []
    start_at = 0
    
    while True:
        response = self._request(
            "POST",
            "/rest/api/3/search",
            data={
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": ["key", "summary", "status", "priority", "created", "updated"]
            }
        )
        
        data = response.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)
        
        # ⚠️ IMPORTANT: data["total"] is total available, NOT all issues
        # The total field represents total matching issues, not cumulative fetched
        if start_at + len(issues) >= data.get("total", 0):
            break
            
        start_at += max_results
    
    return all_issues
```

### Important: Total Field Semantics

⚠️ **Critical Note**: The `total` field in the response represents the **total number of matching issues**, not the cumulative count. The response structure is:

```json
{
    "startAt": 0,
    "maxResults": 50,
    "total": 150,  // Total matching issues
    "issues": [/* 50 items */]
}
```

**Correct pagination logic**:
```python
fetched = start_at + len(issues)
if fetched >= total:
    break  # All items fetched
```

---

## 6. Error Handling

### ErrorCollection Response Structure

```json
{
    "errorMessages": ["Error message 1", "Error message 2"],
    "errors": {
        "fieldName": "Error description for specific field"
    }
}
```

### Parsing Errors

```python
def parse_error_response(response) -> str:
    """Parse Jira ErrorCollection response."""
    try:
        data = response.json()
        if "errorMessages" in data:
            return "; ".join(data["errorMessages"])
        if "errors" in data:
            errors = [f"{k}: {v}" for k, v in data["errors"].items()]
            return "; ".join(errors)
    except:
        pass
    return response.text[:500]
```

### Common HTTP Status Codes

| Status | Meaning | Handling |
|--------|---------|----------|
| 200 | Success | Return JSON |
| 400 | Bad Request | Parse ErrorCollection, fix request |
| 401 | Unauthorized | Re-authenticate |
| 403 | Forbidden | Check permissions/scopes |
| 404 | Not Found | Issue doesn't exist |
| 409 | Conflict | Resource modified, retry |
| 429 | Rate Limited | Wait and retry (see below) |
| 500 | Server Error | Retry with backoff |

### Rate Limiting Handling

```python
def handle_rate_limit(response) -> None:
    """Handle 429 rate limit response."""
    if response.status_code == 429:
        # Check Retry-After header
        retry_after = response.headers.get("Retry-After", "60")
        raise TrackerApiRateLimitError(
            f"Rate limited. Retry after {retry_after} seconds"
        )
```

### Retry Logic with Exponential Backoff

```python
import time

MAX_RETRIES = 3
INITIAL_DELAY = 1  # seconds

def with_retry(self, func):
    """Execute function with exponential backoff."""
    delay = INITIAL_DELAY
    
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except TrackerApiRateLimitError as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(delay)
            delay *= 2  # Exponential backoff
```

---

## 7. Transition Workflow

### List Available Transitions

```python
def list_transitions(self, issue_id: str) -> list[dict]:
    """Get available transitions for issue."""
    response = self._request(
        "GET",
        f"/rest/api/3/issue/{issue_id}/transitions"
    )
    
    data = response.json()
    return [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "to": t.get("to", {}).get("name")
        }
        for t in data.get("transitions", [])
    ]
```

### Find Transition ID by Status Name

```python
def find_transition_by_status(self, issue_id: str, target_status: str) -> str:
    """Find transition ID for target status."""
    transitions = self.list_transitions(issue_id)
    
    for t in transitions:
        # Match by transition name or target status
        if t.get("name", "").lower() == target_status.lower() or \
           t.get("to", "").lower() == target_status.lower():
            return t["id"]
    
    raise TrackerAPIError(
        f"No transition found for status '{target_status}'. "
        f"Available: {[t['name'] for t in transitions]}"
    )
```

### Execute Transition

```python
def transition_issue(self, issue_id: str, transition_id: str) -> dict:
    """Transition issue to new status."""
    response = self._request(
        "POST",
        f"/rest/api/3/issue/{issue_id}/transitions",
        data={"transition": {"id": transition_id}}
    )
    
    return response.json()
```

### Complete Transition Example

```python
def move_to_status(self, issue_id: str, target_status: str) -> dict:
    """Move issue to target status."""
    # Find the transition ID
    transition_id = self.find_transition_by_status(issue_id, target_status)
    
    # Execute the transition
    return self.transition_issue(issue_id, transition_id)
```

---

## 8. Field Updates

### Common Field Update Patterns

```python
# Update summary
UPDATE_SUMMARY = {
    "fields": {
        "summary": "New summary text"
    }
}

# Update assignee (requires accountId)
UPDATE_ASSIGNEE = {
    "fields": {
        "assignee": {
            "accountId": "abc123def456"
        }
    }
}

# Clear assignee
CLEAR_ASSIGNEE = {
    "fields": {
        "assignee": None
    }
}

# Update priority (by ID)
UPDATE_PRIORITY = {
    "fields": {
        "priority": {
            "id": "3"  # High priority
        }
    }
}
```

### Label Updates

```python
# Add labels
def add_labels(self, issue_id: str, labels: list[str]) -> dict:
    """Add labels to issue."""
    # Get current labels first
    issue = self.get_issue(issue_id)
    current_labels = issue.get("fields", {}).get("labels", [])
    
    # Merge with new labels
    new_labels = list(set(current_labels + labels))
    
    return self.update_issue(issue_id, {"labels": new_labels})

# Remove labels
def remove_labels(self, issue_id: str, labels_to_remove: list[str]) -> dict:
    """Remove labels from issue."""
    issue = self.get_issue(issue_id)
    current_labels = issue.get("fields", {}).get("labels", [])
    
    new_labels = [l for l in current_labels if l not in labels_to_remove]
    
    return self.update_issue(issue_id, {"labels": new_labels})

# Set labels (replace all)
def set_labels(self, issue_id: str, labels: list[str]) -> dict:
    """Replace all labels on issue."""
    return self.update_issue(issue_id, {"labels": labels})
```

### Component Updates

```python
# Update components
def update_components(self, issue_id: str, components: list[dict]) -> dict:
    """Update components (requires component id)."""
    return self.update_issue(issue_id, {"components": components})

# Add component example
ADD_COMPONENT = {
    "fields": {
        "components": [
            {"id": "10001"}  # Component ID
        ]
    }
}
```

### Full Update Issue Example

```python
def update_issue(self, issue_id: str, fields: dict) -> dict:
    """Update issue fields."""
    response = self._request(
        "PUT",
        f"/rest/api/3/issue/{issue_id}",
        data={"fields": fields}
    )
    return response.json()

# Usage
self.update_issue("PROJ-123", {
    "summary": "Updated summary",
    "priority": {"id": "3"},
    "labels": ["priority-high", "review-needed"]
})
```

---

## 9. Rate Limiting Best Practices

### Quota Thresholds to Monitor

Jira uses a 3-tier rate limiting system:

| Tier | Limit | Reset |
|------|-------|-------|
| Standard | 10 requests/minute | Per minute |
| Burst | Up to 20 requests | Short window |
| Per-issue writes | 30 writes/issue/minute | Per issue |

### Monitor Response Headers

```python
def check_rate_limit_headers(response) -> dict:
    """Extract rate limit info from response headers."""
    return {
        "remaining": response.headers.get("X-RateLimit-Remaining"),
        "limit": response.headers.get("X-RateLimit-Limit"),
        "retry_after": response.headers.get("Retry-After")
    }
```

### Handle 429 Responses

```python
def handle_429(self, response) -> None:
    """Handle rate limit exceeded."""
    retry_after = int(response.headers.get("Retry-After", "60"))
    
    # Wait and retry
    time.sleep(retry_after)
    
    # Re-attempt request
    return self._retry_request(response.request)
```

### Best Practices Summary

1. **Cache transitions**: Transitions rarely change; cache for 5-10 minutes
2. **Cache field metadata**: Cache field schemas to reduce API calls
3. **Batch requests**: Use batch operations where available
4. **Implement backoff**: Exponential backoff on 429 errors
5. **Monitor X-RateLimit-Remaining**: Proactively slow down when low

---

## 10. Implementation Notes

### Key Differences from Linear Adapter

| Aspect | Linear | Jira |
|--------|--------|------|
| API Type | GraphQL | REST |
| Authentication | API Key header | Basic Auth (base64) |
| Pagination | Cursor-based | Offset-based |
| Issue ID | Internal UUID | Project-key format (PROJ-123) |
| Query Language | GraphQL filter | JQL |
| Comments | Markdown | ADF format |
| Rate Limiting | Simple 429 | 3-tier system |

### Use `requests` (Same as Linear)

```python
import requests

# Use same library as Linear for consistency
class JiraTracker(TrackerClient):
    def _request(self, method: str, path: str, data: dict = None) -> requests.Response:
        url = f"{self._endpoint}{path}"
        
        response = requests.request(
            method=method,
            url=url,
            json=data,
            headers=self._headers,
            timeout=30
        )
        
        if response.status_code == 429:
            raise TrackerApiRateLimitError("Rate limit exceeded")
        
        if response.status_code >= 400:
            raise TrackerApiStatusError(f"API error: {response.status_code}")
        
        return response
```

### Caching Recommendations

```python
# Cache transition metadata (rarely changes)
from functools import lru_cache

@lru_cache(maxsize=100)
def get_transitions_cached(self, issue_id: str) -> list[dict]:
    """Cache transitions for 5 minutes."""
    return self.list_transitions(issue_id)

# Cache field metadata
@lru_cache(maxsize=50)
def get_fields_metadata(self) -> dict:
    """Cache field metadata."""
    response = self._request("GET", "/rest/api/3/field")
    return {f["id"]: f for f in response.json()}
```

### Testing Strategy

```python
# Option 1: Use responses library for mocking
import responses

@responses.activate
def test_fetch_issues():
    responses.add(
        responses.POST,
        "https://company.atlassian.net/rest/api/3/search",
        json={"issues": [...], "total": 1},
        status=200
    )
    
    tracker = JiraTracker(api_key="...", endpoint="https://company.atlassian.net", ...)
    issues = tracker.fetch_issues("project=TEST")
    assert len(issues) == 1

# Option 2: Use pytest-mock for integration tests
def test_with_real_jira(mocker):
    # Mock the requests layer, test adapter logic
    pass
```

### Minimal Implementation Checklist

- [ ] Implement `authenticate()` with `/rest/api/3/myself` validation
- [ ] Implement `fetch_issues()` with JQL and pagination
- [ ] Implement `get_issue()` with field selection
- [ ] Implement `update_issue()` with field validation
- [ ] Implement `add_comment()` with ADF conversion
- [ ] Implement `list_transitions()` for workflow
- [ ] Implement `transition_issue()` for status changes
- [ ] Add error handling for all HTTP status codes
- [ ] Add rate limit handling (429 with Retry-After)
- [ ] Add unit tests with mocked responses

---

## Quick Start Code Template

```python
"""Jira REST API tracker adapter - Implementation Template."""

import base64
import requests
from typing import Any, Dict, List, Optional

from .base import TrackerClient
from .factory import (
    TrackerAPIError,
    TrackerApiRequestError,
    TrackerApiStatusError,
    TrackerApiRateLimitError,
    TrackerApiTimeoutError,
)

DEFAULT_TIMEOUT = 30
MAX_RESULTS = 50


class JiraTracker(TrackerClient):
    """Jira issue tracker adapter implementing TrackerClient interface."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        project_key: str = "",
        username: str = "",
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._project_key = project_key
        self._username = username
        self._timeout = timeout
        self._session = None
        self._user = None

    @property
    def tracker_kind(self) -> str:
        return "jira"

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header."""
        credentials = f"{self._username}:{self._api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _request(
        self, method: str, path: str, data: dict = None, params: dict = None
    ) -> requests.Response:
        """Execute HTTP request with error handling."""
        url = f"{self._endpoint}{path}"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise TrackerApiRateLimitError(
                    f"Rate limited. Retry after {retry_after}s"
                )

            if response.status_code == 401:
                raise TrackerApiStatusError("Invalid credentials (401)")

            if response.status_code == 404:
                raise TrackerApiStatusError(f"Resource not found: {path}")

            if response.status_code >= 400:
                raise TrackerApiStatusError(
                    f"API error {response.status_code}: {response.text[:500]}"
                )

            return response

        except requests.exceptions.Timeout as e:
            raise TrackerApiTimeoutError(f"Request timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            raise TrackerApiRequestError(f"Request failed: {e}") from e

    def authenticate(self) -> None:
        """Validate credentials."""
        response = self._request("GET", "/rest/api/3/myself")
        self._user = response.json()

    def fetch_issues(self, query: str) -> List[Dict[str, Any]]:
        """Fetch issues using JQL."""
        all_issues = []
        start_at = 0

        while True:
            response = self._request(
                "POST",
                "/rest/api/3/search",
                data={
                    "jql": query,
                    "startAt": start_at,
                    "maxResults": MAX_RESULTS,
                    "fields": ["key", "summary", "status", "priority", "created", "updated", "labels"],
                },
            )

            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            total = data.get("total", 0)
            if start_at + len(issues) >= total:
                break

            start_at += MAX_RESULTS

        return all_issues

    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get full issue details."""
        response = self._request(
            "GET",
            f"/rest/api/3/issue/{issue_id}",
            params={"fields": "summary,status,priority,assignee,labels,components"},
        )
        return response.json()

    def update_issue(self, issue_id: str, fields: dict) -> Dict[str, Any]:
        """Update issue fields."""
        response = self._request(
            "PUT",
            f"/rest/api/3/issue/{issue_id}",
            data={"fields": fields},
        )
        return response.json()

    def add_comment(self, issue_id: str, body: str) -> Dict[str, Any]:
        """Add comment in ADF format."""
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": body}],
                }
            ],
        }

        response = self._request(
            "POST",
            f"/rest/api/3/issue/{issue_id}/comment",
            data={"body": adf_body},
        )
        return response.json()

    def list_transitions(self, issue_id: str) -> List[Dict[str, Any]]:
        """Get available transitions."""
        response = self._request("GET", f"/rest/api/3/issue/{issue_id}/transitions")
        return response.json().get("transitions", [])

    def transition_issue(self, issue_id: str, transition_id: str) -> Dict[str, Any]:
        """Transition issue to new status."""
        response = self._request(
            "POST",
            f"/rest/api/3/issue/{issue_id}/transitions",
            data={"transition": {"id": transition_id}},
        )
        return response.json()

    # Additional interface methods for base.py
    def fetch_candidate_issues(self) -> List[Dict[str, Any]]:
        """Fetch active issues in project."""
        if not self._project_key:
            raise TrackerAPIError("project_key required for fetch_candidate_issues")
        
        jql = f'project = {self._project_key} AND status IN ("To Do", "In Progress")'
        return self.fetch_issues(jql)

    def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]:
        """Fetch issues by state names."""
        if not self._project_key:
            raise TrackerAPIError("project_key required for fetch_issues_by_states")
        
        states = ", ".join([f'"{s}"' for s in state_names])
        jql = f"project = {self._project_key} AND status IN ({states})"
        return self.fetch_issues(jql)

    def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch states for specific issues."""
        if not issue_ids:
            return {}
        
        keys = ", ".join([f'"{k}"' for k in issue_ids])
        jql = f"key IN ({keys})"
        
        issues = self.fetch_issues(jql)
        return {issue["key"]: issue["fields"]["status"]["name"] for issue in issues}
```

---

## See Also

- 🔗 `runtime/tracker/linear.py` - Reference implementation
- 🔗 `runtime/tracker/base.py` - TrackerClient interface
- 🔗 `runtime/tracker/factory.py` - Tracker factory with validation
- 🔗 `docs/jira-api.json` - Full OpenAPI specification (72,577 lines)
- 🔗 `integrations/jira-adapter-spec.md` - Original specification document