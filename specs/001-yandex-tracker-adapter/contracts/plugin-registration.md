# Plugin Registration Contract: Yandex Tracker Adapter

**Plugin**: symphony-yandex-tracker  
**Version**: 0.1.0  
**Date**: 2026-04-14  
**Purpose**: Defines the plugin registration contract for automatic discovery by TrackerFactory

---

## Overview

The Yandex Tracker adapter is registered as a discoverable plugin via Python entry points under the `symphony.trackers` group. This enables automatic plugin discovery by TrackerFactory without manual configuration.

**Mechanism**: `pyproject.toml` entry_points (PEP 621)  
**Discovery**: `importlib.metadata.entry_points()` (Python 3.8+)  
**Registration Group**: `symphony.trackers`

---

## Entry Point Configuration

### Configuration Location

File: `plugins/symphony-yandex-tracker/pyproject.toml`

### Configuration Format

```toml
[project]
name = "symphony-yandex-tracker"
version = "0.1.0"
description = "Yandex Tracker adapter for Symphony orchestration platform"
authors = ["py-symphony team"]

[project.entry-points."symphony.trackers"]
yandex_tracker = "symphony_yandex_tracker.adapter:YandexTrackerAdapter"
```

### Configuration Fields

**Entry Point Group**: `symphony.trackers`
- **Purpose**: Groups all tracker adapter plugins
- **Required**: Yes (TrackerFactory scans this group)
- **Alternative**: None (fixed by Symphony architecture)

**Entry Point Name**: `yandex_tracker`
- **Purpose**: Unique identifier for the tracker
- **Required**: Yes (used as `tracker.kind` in WORKFLOW.md configuration)
- **Format**: String literal (no spaces, snake_case)
- **Constraint**: Must match `tracker_kind` in `__plugin_info__` attribute

**Entry Point Reference**: `symphony_yandex_tracker.adapter:YandexTrackerAdapter`
- **Purpose**: Importable path to the adapter class
- **Required**: Yes (must be importable after package installation)
- **Format**: `package.module:ClassName`
- **Constraint**: Class must inherit from `TrackerClient` base interface

---

## Plugin Metadata

### __plugin_info__ Attribute

The adapter class must define a class-level attribute `__plugin_info__` containing metadata:

```python
class YandexTrackerAdapter(TrackerClient):
    __plugin_info__ = {
        "name": "symphony-yandex-tracker",
        "version": "0.1.0",
        "tracker_kind": "yandex_tracker",
        "description": "Yandex Tracker adapter for Symphony orchestration platform",
        "author": "py-symphony team"
    }
```

### Metadata Fields

| Field | Type | Required | Description |
|--------|-------|-----------|-------------|
| `name` | str | Yes | Plugin package name |
| `version` | str | Yes | Plugin version (semver format) |
| `tracker_kind` | str | Yes | **Must be "yandex_tracker"** (FR-025) - matches entry point name |
| `description` | str | Yes | Plugin description |
| `author` | str | Yes | Plugin author/team name |

### Validation Rules

- `tracker_kind` **must** be `"yandex_tracker"` (FR-025)
- `tracker_kind` **must** match entry point name (`yandex_tracker`)
- All fields **must** be present (name, version, tracker_kind, description, author)
- Fields **must** be strings (no complex types)

---

## Discovery Workflow

### 1. Installation

```bash
# Install plugin package
uv pip install symphony-yandex-tracker

# Or install in development mode
uv pip install -e plugins/symphony-yandex-tracker
```

### 2. Discovery by TrackerFactory

```python
from runtime.tracker import TrackerFactory

# Discover all tracker plugins
factory = TrackerFactory()
plugins = factory.discover_from_entry_points()

# Result: List of discovered plugins
# [
#     {
#         "kind": "yandex_tracker",
#         "class": YandexTrackerAdapter,
#         "info": {...}
#     },
#     ...
# ]
```

### 3. Instantiation

```python
# Create adapter instance
adapter = factory.create(
    kind="yandex_tracker",
    api_key="y0_abcdefghijklmnop123",
    project_slug="BACKEND"
)

# Or manually instantiate
from symphony_yandex_tracker.adapter import YandexTrackerAdapter
adapter = YandexTrackerAdapter(
    api_key="y0_abcdefghijklmnop123",
    project_slug="BACKEND"
)
```

### 4. Usage in WORKFLOW.md

```yaml
# WORKFLOW.md configuration
tracker:
  kind: yandex_tracker
  api_key: ${YANDEX_TRACKER_TOKEN}
  project_slug: BACKEND
  active_states: ["open", "in progress"]
```

---

## Package Structure

```
plugins/symphony-yandex-tracker/
├── pyproject.toml              # Entry point configuration
├── README.md                   # Plugin documentation
└── symphony_yandex_tracker/
    ├── __init__.py
    ├── adapter.py                # YandexTrackerAdapter class (with __plugin_info__)
    ├── models.py
    ├── errors.py
    └── tests/
        ├── __init__.py
        ├── test_adapter.py
        ├── test_models.py
        └── test_errors.py
```

---

## Versioning Rules

- **Semantic Versioning**: Plugin must follow `MAJOR.MINOR.PATCH` format
- **Backward Compatibility**: Breaking changes require major version bump
- **Metadata Sync**: `__plugin_info__["version"]` must match `pyproject.toml` version
- **Deprecation**: Deprecated features must be documented in `README.md`

---

## Error Handling

### Discovery Failures

If plugin discovery fails, TrackerFactory logs a warning and excludes the plugin:

```python
# Warning example
WARNING: Failed to load plugin 'symphony-yandex-tracker': 
         ImportError: No module named 'symphony_yandex_tracker'
```

### Entry Point Validation

TrackerFactory validates entry points before registration:

| Validation | Failure Behavior |
|------------|------------------|
| Entry point not importable | Log warning, skip plugin |
| Class doesn't inherit from TrackerClient | Log warning, skip plugin |
| __plugin_info__ missing | Log warning, skip plugin |
| tracker_kind != entry point name | Log warning, skip plugin |

---

## Testing

### Entry Point Tests

```python
# Test 1: Entry point exists
import sys
from importlib.metadata import entry_points

trackers = entry_points(group="symphony.trackers")
assert any(ep.name == "yandex_tracker" for ep in trackers)

# Test 2: Class importable
from symphony_yandex_tracker.adapter import YandexTrackerAdapter
assert YandexTrackerAdapter is not None

# Test 3: __plugin_info__ present
assert hasattr(YandexTrackerAdapter, "__plugin_info__")
info = YandexTrackerAdapter.__plugin_info__
assert "tracker_kind" in info
assert info["tracker_kind"] == "yandex_tracker"
```

---

## Dependencies

### Required Dependencies

- `httpx>=0.24.0`: HTTP client for API calls
- `pydantic>=2.0.0`: Data validation (optional but recommended)

### Runtime Dependencies

- `runtime`: TrackerClient base interface (provided by Symphony core)

### Dev Dependencies

- `pytest>=7.0.0`: Testing framework
- `pytest-asyncio>=0.21.0`: Async support (if needed)
- `mypy>=1.5.0`: Type checking
- `ruff>=0.1.0`: Linting

---

## Compliance

### Constitution Compliance (FR-025)

✅ Entry point registered under `symphony.trackers` group  
✅ `tracker_kind` in `__plugin_info__` is `"yandex_tracker"`  
✅ Entry point name matches `tracker_kind`  
✅ Adapter class is importable  
✅ Plugin is separate package (no imports from runtime/)  

### SPEC.md Compliance

✅ Matches TrackerFactory auto-discovery requirements  
✅ Supports configuration via WORKFLOW.md (tracker.kind="yandex_tracker")  
✅ Metadata exposed via `__plugin_info__` attribute  

---

## Examples

### Complete Setup Example

```bash
# 1. Install plugin
cd plugins/symphony-yandex-tracker
uv pip install -e .

# 2. Verify discovery
python -c "
from runtime.tracker import TrackerFactory
factory = TrackerFactory()
print('Discovered trackers:', factory.list_kinds())
"

# 3. Configure WORKFLOW.md
# Add to WORKFLOW.yaml:
# tracker:
#   kind: yandex_tracker
#   api_key: \${YANDEX_TRACKER_TOKEN}
#   project_slug: BACKEND

# 4. Run Symphony
cd elixir && mise exec -- ./bin/symphony ./WORKFLOW.md
```

---

## Deprecations

None in version 0.1.0