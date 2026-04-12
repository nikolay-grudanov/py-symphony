# Symphony Jira Tracker Adapter

A plugin adapter that integrates Jira issue tracking with Symphony orchestration platform.

## Overview

The `symphony-jira` plugin provides seamless integration between Symphony and Jira, enabling the orchestrator to fetch, manage, and track issues from Jira projects.

## Installation

```bash
pip install symphony-jira
```

## Configuration

### Workflow Configuration (YAML)

Add the Jira tracker configuration to your workflow file:

```yaml
tracker:
  kind: jira
  api_key: ${JIRA_API_TOKEN}
  endpoint: https://company.atlassian.net
  project_key: MYPROJECT
  username: ${JIRA_USERNAME}
  timeout: 30
  active_states:
    - To Do
    - In Progress
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_API_TOKEN` | Jira API token for authentication | Yes |
| `JIRA_USERNAME` | Jira username/email | Yes |

To obtain a Jira API token:
1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Set the `JIRA_API_TOKEN` environment variable

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | Required | Jira API token |
| `endpoint` | string | Required | Jira instance URL |
| `project_key` | string | Required | Jira project key |
| `username` | string | Optional | Jira username/email (for basic auth) |
| `timeout` | integer | `30` | Request timeout in seconds |
| `active_states` | list | `['To Do', 'In Progress']` | States considered active |

## Features

- **REST API Integration**: Uses Jira's REST API for efficient querying
- **JQL Support**: Leverage Jira Query Language for powerful filtering
- **Issue Fetching**: Fetch candidate issues in active states
- **State Filtering**: Query issues by specific states
- **Bulk State Lookup**: Get current states for multiple issues
- **Plugin Architecture**: Fully integrated with Symphony's plugin system
- **Entry Point Discovery**: Automatic discovery via `symphony.trackers` entry point

## Plugin Information

- **Entry Point**: `symphony.trackers.jira`
- **Tracker Kind**: `jira`
- **Package**: `symphony_jira.adapter:JiraAdapter`

## Development Setup

### Prerequisites

- Python 3.9+
- pip or poetry

### Local Development

```bash
# Clone the repository
git clone https://github.com/symphony-dev/symphony-jira.git
cd symphony-jira

# Install in development mode
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=symphony_jira
```

### Project Structure

```
symphony-jira/
├── pyproject.toml           # Package configuration
├── README.md                # This file
├── symphony_jira/
│   ├── __init__.py          # Package initialization
│   └── adapter.py           # Jira adapter implementation
└── tests/
    ├── __init__.py
    └── test_jira_adapter.py
```

## Usage Example

```python
from symphony_jira import JiraAdapter

# Create adapter instance
adapter = JiraAdapter(
    api_key="your-api-token",
    endpoint="https://company.atlassian.net",
    project_key="MYPROJECT",
    username="your-email@company.com",
)

# Fetch candidate issues
issues = adapter.fetch_candidate_issues()

# Fetch issues by specific states
todo_issues = adapter.fetch_issues_by_states(["To Do"])

# Get current states for specific issues
states = adapter.fetch_issue_states_by_ids(["MYPROJECT-123", "MYPROJECT-456"])
```

## Error Handling

The adapter uses error classes from `runtime.tracker.factory`:

- `TrackerAPIError` - Base exception for API errors
- `TrackerApiRequestError` - Network/transport failures
- `TrackerApiStatusError` - Non-200 HTTP responses
- `TrackerApiTimeoutError` - Request timeouts
- `TrackerApiRateLimitError` - Rate limit errors (429)
- `TrackerApiResourceNotFoundError` - Resource not found (404)

## License

MIT License - see LICENSE file for details.

## Support

- Issues: https://github.com/symphony-dev/symphony-jira/issues
- Documentation: https://docs.symphony.dev/trackers/jira