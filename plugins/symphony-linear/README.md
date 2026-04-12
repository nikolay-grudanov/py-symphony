# Symphony Linear Tracker Adapter

A plugin adapter that integrates Linear issue tracking with Symphony orchestration platform.

## Overview

The `symphony-linear` plugin provides seamless integration between Symphony and Linear, enabling the orchestrator to fetch, manage, and track issues from Linear projects.

## Installation

```bash
pip install symphony-linear
```

## Configuration

### Workflow Configuration (YAML)

Add the Linear tracker configuration to your workflow file:

```yaml
tracker:
  kind: linear
  api_key: ${LINEAR_API_KEY}
  project_slug: my-project
  endpoint: https://api.linear.app/graphql
  timeout: 30
  active_states:
    - Todo
    - In Progress
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINEAR_API_KEY` | Linear API key for authentication | Yes |

To obtain a Linear API key:
1. Go to Linear Settings → API
2. Create a new API key
3. Set the `LINEAR_API_KEY` environment variable

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | Required | Linear API key |
| `project_slug` | string | Required | Linear project slug |
| `endpoint` | string | `https://api.linear.app/graphql` | GraphQL API endpoint |
| `timeout` | integer | `30` | Request timeout in seconds |
| `active_states` | list | `['Todo', 'In Progress']` | States considered active |

## Features

- **GraphQL Integration**: Uses Linear's GraphQL API for efficient querying
- **Issue Fetching**: Fetch candidate issues in active states
- **State Filtering**: Query issues by specific states
- **Bulk State Lookup**: Get current states for multiple issues
- **Plugin Architecture**: Fully integrated with Symphony's plugin system
- **Entry Point Discovery**: Automatic discovery via `symphony.trackers` entry point

## Plugin Information

- **Entry Point**: `symphony.trackers.linear`
- **Tracker Kind**: `linear`
- **Package**: `symphony_linear.adapter:LinearAdapter`

## Development Setup

### Prerequisites

- Python 3.9+
- pip or poetry

### Local Development

```bash
# Clone the repository
git clone https://github.com/symphony-dev/symphony-linear.git
cd symphony-linear

# Install in development mode
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=symphony_linear
```

### Project Structure

```
symphony-linear/
├── pyproject.toml           # Package configuration
├── README.md                # This file
├── symphony_linear/
│   ├── __init__.py          # Package initialization
│   └── adapter.py           # Linear adapter implementation
└── tests/
    ├── __init__.py
    └── test_linear_adapter.py
```

## Usage Example

```python
from symphony_linear import LinearAdapter

# Create adapter instance
adapter = LinearAdapter(
    api_key="lin_api_...",
    project_slug="my-project",
)

# Fetch candidate issues
issues = adapter.fetch_candidate_issues()

# Fetch issues by specific states
todo_issues = adapter.fetch_issues_by_states(["Todo"])

# Get current states for specific issues
states = adapter.fetch_issue_states_by_ids(["LINEAR-123", "LINEAR-456"])
```

## Error Handling

The adapter uses error classes from `runtime.tracker.factory`:

- `TrackerAPIError` - Base exception for API errors
- `TrackerApiRequestError` - Network/transport failures
- `TrackerApiStatusError` - Non-200 HTTP responses
- `TrackerApiTimeoutError` - Request timeouts
- `TrackerApiRateLimitError` - Rate limit errors (429)

## License

MIT License - see LICENSE file for details.

## Support

- Issues: https://github.com/symphony-dev/symphony-linear/issues
- Documentation: https://docs.symphony.dev/trackers/linear