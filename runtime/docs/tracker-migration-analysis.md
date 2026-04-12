# Tracker Migration Analysis: Old vs New Architecture

**Document Version:** 1.0  
**Date:** April 12, 2026  
**Author:** Implementation Engineer  
**Purpose:** Comprehensive analysis for migrating from old tracker to new pluggable tracker

---

## Executive Summary

This document provides a detailed analysis comparing the old issue tracker architecture (`runtime/symphony/tracker.py`) with the new pluggable tracker architecture (`runtime/tracker/`). The analysis identifies critical breaking changes and recommends compatibility strategies for the Orchestrator migration.

### Key Findings

| Category | Old Architecture | New Architecture | Impact |
|----------|------------------|-----------------|--------|
| Domain Model | `Issue` dataclass (11 fields) | `dict` from `normalize_issue()` (8 fields) | **HIGH** |
| Execution Model | Async (`asyncio`/`aiohttp`) | Sync (`requests`) | **MEDIUM** |
| Method Names | `fetch_issue_states()` | `fetch_issue_states_by_ids()` | **MEDIUM** |
| Configuration | Full explicit params | Minimal with defaults | **MEDIUM** |
| Exception Hierarchy | 9 custom exceptions | 10 custom exceptions | **LOW** |
| Factory Pattern | Function (`create_tracker()`) | Class (`TrackerFactory.create()`) | **LOW** |

### Migration Complexity Assessment

- **Domain Model Changes:** High complexity - requires dataclass-to-dict conversion or field access refactoring
- **Async to Sync:** Medium complexity - can use thread pool or facade pattern
- **API Changes:** Medium complexity - mostly naming differences
- **Configuration Changes:** Low complexity - can pass additional params after instantiation

**Overall Risk Level:** MEDIUM-HIGH

---

## 1. Domain Model Comparison

### 1.1 Old Issue Dataclass

**Location:** `runtime/symphony/tracker.py`, lines 17-32

```python
@dataclass
class Issue:
    """Normalized issue record."""

    id: str  # Linear internal UUID
    identifier: str  # Human ticket key (e.g., MT-123)
    title: str
    description: Optional[str]
    priority: Optional[int]  # Lower numbers = higher priority
    state: str
    branch_name: Optional[str]
    url: Optional[str]
    labels: list[str]  # Lowercase
    blocked_by: list[dict]  # [{id, identifier, state}]
    created_at: Optional[str]
    updated_at: Optional[str]
```

**Total Fields:** 11

### 1.2 New Issue Dict Format

**Location:** `runtime/tracker/normalization.py`, lines 16-49

```python
{
    "id": issue_id,                                    # From raw_issue.get("id") or raw_issue.get("identifier")
    "identifier": raw_issue.get("identifier") or issue_id,
    "title": raw_issue.get("title") or raw_issue.get("summary", ""),
    "state": NormalizationUtils.normalize_state(...),  # Lowercase
    "priority": NormalizationUtils._normalize_priority(...),  # Integer 0-4
    "created_at": NormalizationUtils._parse_timestamp(...),  # datetime or None
    "labels": NormalizationUtils._normalize_labels(...),  # List[str] lowercase
    "blocked_by": raw_issue.get("blocked_by") or raw_issue.get("blockedBy", []),
}
```

**Total Fields:** 8

### 1.3 Field-by-Field Comparison

| # | Old Field | Type | New Field | Type | Status | Notes |
|---|----------|------|----------|------|-------|-------|
| 1 | `id` | `str` | `id` | `str` | ✅ Same | Identical |
| 2 | `identifier` | `str` | `identifier` | `str` | ✅ Same | Identical |
| 3 | `title` | `str` | `title` | `str` | ✅ Same | Identical |
| 4 | `description` | `Optional[str]` | — | — | ❌ Missing | New tracker doesn't extract description |
| 5 | `priority` | `Optional[int]` | `priority` | `Optional[int]` | ✅ Same | Now normalized to 0-4 |
| 6 | `state` | `str` | `state` | `str` | ✅ Same | Now normalized to lowercase |
| 7 | `branch_name` | `Optional[str]` | — | — | ❌ Missing | Not in dict format |
| 8 | `url` | `Optional[str]` | — | — | ❌ Missing | Not in dict format |
| 9 | `labels` | `list[str]` | `labels` | `list[str]` | ✅ Same | Both lowercase |
| 10 | `blocked_by` | `list[dict]` | `blocked_by` | `list[dict]` | ✅ Same | Both contain {id, identifier, state} |
| 11 | `created_at` | `Optional[str]` | `created_at` | `Optional[datetime]` | ⚠️ Changed | Now `datetime` instead of `str` |
| 12 | `updated_at` | `Optional[str]` | — | — | ❌ Missing | Not in dict format |

### 1.4 Breaking Changes Summary

**Missing Fields (5):**
- `description` - Optional description text
- `branch_name` - Linear branch name
- `url` - Issue URL
- `updated_at` - Last update timestamp

**Type Changes (1):**
- `created_at`: `str` → `Optional[datetime]`

**Impact Assessment:**
- **Critical:** Fields used in Orchestrator are mostly present (`id`, `identifier`, `title`, `state`, `priority`, `created_at`, `blocked_by`)
- **Low:** Missing fields (`description`, `branch_name`, `url`, `updated_at`) are not core to orchestration logic

---

## 2. API Method Comparison

### 2.1 Abstract Base Class Methods

**Old Tracker (ABC):** `runtime/symphony/tracker.py`, lines 90-106

```python
class Tracker(abc.ABC):
    @abc.abstractmethod
    async def fetch_candidate_issues(self) -> list[Issue]:
        """Fetch issues in active states for the configured project."""
        pass

    @abc.abstractmethod
    async def fetch_issues_by_states(self, states: list[str]) -> list[Issue]:
        """Fetch issues in specified states (for startup cleanup)."""
        pass

    @abc.abstractmethod
    async def fetch_issue_states(self, issue_ids: list[str]) -> dict[str, str]:
        """Fetch current states for specific issue IDs (for reconciliation)."""
        pass
```

**New TrackerClient (ABC):** `runtime/tracker/base.py`, lines 7-52

```python
class TrackerClient(ABC):
    @property
    @abstractmethod
    def tracker_kind(self) -> str:
        """Return the tracker kind identifier (e.g., 'linear', 'jira')."""
        raise NotImplementedError

    @abstractmethod
    def fetch_candidate_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues in active states that are candidates for dispatch."""
        pass

    @abstractmethod
    def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]:
        """Fetch issues matching the specified states."""
        pass

    @abstractmethod
    def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch current states for specific issues."""
        pass
```

### 2.2 Method Signature Comparison

| Method | Old Signature | New Signature | Changes |
|--------|--------------|---------------|----------|
| `fetch_candidate_issues` | `async def fetch_candidate_issues(self) -> list[Issue]` | `def fetch_candidate_issues(self) -> List[Dict[str, Any]]` | Async → Sync, list[Issue] → List[Dict] |
| `fetch_issues_by_states` | `async def fetch_issues_by_states(self, states: list[str]) -> list[Issue]` | `def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]` | Async → Sync, param renamed |
| `fetch_issue_states` | `async def fetch_issue_states(self, issue_ids: list[str]) -> dict[str, str]` | `def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]` | **Method renamed**, Async → Sync |

### 2.3 Key Differences

1. **Async vs Sync Execution Model**
   - **Old:** Uses `aiohttp` for async HTTP requests
   - **New:** Uses `requests` for sync HTTP requests
   - **Impact:** Requires async/sync bridging or refactoring

2. **Method Naming Changes**
   - `fetch_issue_states` → `fetch_issue_states_by_ids`
   - Parameter: `states` → `state_names`
   - **Impact:** Search-and-replace in calling code

3. **Return Type Changes**
   - `list[Issue]` → `List[Dict[str, Any]]`
   - **Impact:** Requires dict access instead of attribute access

---

## 3. Initialization/Configuration Comparison

### 3.1 Old LinearTracker Constructor

**Location:** `runtime/symphony/tracker.py`, lines 169-196

```python
def __init__(
    self,
    endpoint: str,
    api_key: str,
    project_slug: str,
    active_states: list[str],
    terminal_states: list[str],
):
    """Initialize Linear tracker adapter.

    Args:
        endpoint: GraphQL API endpoint URL
        api_key: Linear API key for authentication
        project_slug: Linear project slug ID for filtering
        active_states: List of active issue states
        terminal_states: List of terminal issue states
    """
    if not api_key:
        raise MissingTrackerApiKey("Linear API key is required")
    if not project_slug:
        raise MissingTrackerProjectSlug("Linear project slug is required")

    self.endpoint = endpoint
    self.api_key = api_key
    self.project_slug = project_slug
    self.active_states = active_states
    self.terminal_states = terminal_states
    self._session: Optional[aiohttp.ClientSession] = None
```

**Parameters:** 5 explicit params + 1 internal session

### 3.2 New LinearTracker Constructor

**Location:** `runtime/tracker/linear.py`, lines 37-58

```python
def __init__(
    self,
    api_key: str,
    project_slug: Optional[str] = None,
    active_states: Optional[List[str]] = None,
    endpoint: str = LINEAR_ENDPOINT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
):
    """Initialize Linear tracker adapter.

    Args:
        api_key: Linear API key
        project_slug: Optional project identifier for filtering
        active_states: Optional list of active states for candidate issues
        endpoint: Linear GraphQL API endpoint (default: https://api.linear.app/graphql)
        timeout_seconds: Request timeout in seconds (default: 30)
    """
    self._api_key = api_key
    self._project_slug = project_slug
    self._active_states = active_states or DEFAULT_ACTIVE_STATES
    self._endpoint = endpoint
    self._timeout_seconds = timeout_seconds
```

**Parameters:** 5 params with 3 having defaults

### 3.3 Configuration Parameter Comparison

| Parameter | Old | Default | New | Default | Status |
|-----------|-----|---------|-----|---------|--------|
| `endpoint` | Required | — | Optional | `https://api.linear.app/graphql` | ✅ Has default |
| `api_key` | Required | — | Required | — | ✅ Same |
| `project_slug` | Required | — | Optional | `None` | ⚠️ Now optional |
| `active_states` | Required | — | Optional | `["Todo", "In Progress"]` | ✅ Has default |
| `terminal_states` | Required | — | — | — | ❌ Removed |
| `timeout` | — | — | Optional | `30` | ✅ New |

### 3.4 Breaking Changes

1. **`terminal_states` Removed**
   - New tracker doesn't accept `terminal_states` in constructor
   - Terminal state checking must be done in Orchestrator

2. **`project_slug` Made Optional**
   - Could cause runtime errors if not provided
   - Factory validates but runtime behavior differs

3. **No HTTP Session Management**
   - Old: Manages `aiohttp.ClientSession` lifecycle
   - New: Creates new `requests.Session` per call (implicit)

---

## 4. Factory Comparison

### 4.1 Old Factory Function

**Location:** `runtime/symphony/tracker.py`, lines 505-528

```python
def create_tracker(config: Config) -> Tracker:
    """Factory function to create tracker from config.

    Args:
        config: Typed configuration object

    Returns:
        Tracker instance for the configured kind

    Raises:
        UnsupportedTrackerKind: If tracker kind is not supported
    """
    kind = config.tracker_kind

    if kind == "linear":
        return LinearTracker(
            endpoint=config.tracker_endpoint,
            api_key=config.tracker_api_key or "",
            project_slug=config.tracker_project_slug or "",
            active_states=config.tracker_active_states,
            terminal_states=config.tracker_terminal_states,
        )
    else:
        raise UnsupportedTrackerKind(f"Unsupported tracker kind: {kind}")
```

**Characteristics:**
- Function-based (not a class)
- Direct instantiation with all Config fields
- Raises `UnsupportedTrackerKind`

### 4.2 New Factory Class

**Location:** `runtime/tracker/factory.py`, lines 70-107

```python
class TrackerFactory:
    """Factory for creating tracker adapter instances."""

    @staticmethod
    def create(config: Any) -> TrackerClient:
        """Create a tracker adapter instance from configuration.

        Args:
            config: Configuration object with tracker settings

        Returns:
            TrackerClient instance

        Raises:
            TrackerNotRegisteredError: If tracker kind is not registered
            TrackerConfigError: If configuration is invalid
        """
        kind = config.tracker_kind
        registry = get_tracker_registry()

        # Get adapter class
        adapter_class = registry.get_adapter(kind)
        if adapter_class is None:
            available = registry.list_adapters()
            raise TrackerNotRegisteredError(...)

        # Validate configuration
        TrackerFactory._validate_config(kind, config)

        # Instantiate adapter
        return TrackerFactory._instantiate_adapter(adapter_class, config)
```

**Characteristics:**
- Class-based with static methods
- Uses Registry pattern for adapter lookup
- Two-phase validation: registration + config

### 4.3 Factory Comparison

| Aspect | Old | New |
|--------|-----|-----|
| Pattern | Function | Class (static methods) |
| Registration | Hardcoded if/else | Registry pattern |
| Validation | None | Two-phase |
| Exception | `UnsupportedTrackerKind` | `TrackerNotRegisteredError` + `TrackerConfigError` |
| Adapter params | All Config fields | Limited subset |

### 4.4 Impact on Orchestrator

- **Import changes:** `from runtime.symphony.tracker import create_tracker` → `from runtime.tracker import TrackerFactory`
- **Instantiation:** `create_tracker(config)` → `TrackerFactory.create(config)`
- **Return type:** `Tracker` → `TrackerClient`

---

## 5. Exception Handling Comparison

### 5.1 Old Exception Hierarchy

**Location:** `runtime/symphony/tracker.py`, lines 35-87

```
TrackerError (base)
├── UnsupportedTrackerKind
├── MissingTrackerApiKey
├── MissingTrackerProjectSlug
├── LinearApiRequest
├── LinearApiStatus
├── LinearGraphQLErrors
├── LinearUnknownPayload
└── LinearMissingEndCursor
```

**Total:** 9 exception types

### 5.2 New Exception Hierarchy

**Location:** `runtime/tracker/factory.py`, lines 10-67

```
TrackerFactoryError (base)
├── TrackerNotRegisteredError
├── TrackerConfigError
└── TrackerAPIError (base)
    ├── TrackerApiRequestError
    ├── TrackerApiStatusError
    ├── TrackerApiConflictError
    ├── TrackerApiResourceNotFoundError
    ├── TrackerApiTimeoutError
    └── TrackerApiRateLimitError
```

**Total:** 10 exception types

### 5.3 Exception Mapping

| Old Exception | New Exception | Mapping |
|-------------|--------------|---------|
| `TrackerError` | `TrackerFactoryError` | Base changed |
| `UnsupportedTrackerKind` | `TrackerNotRegisteredError` | ✅ Equivalent |
| `MissingTrackerApiKey` | `TrackerConfigError` | ✅ Equivalent |
| `MissingTrackerProjectSlug` | `TrackerConfigError` | ✅ Equivalent |
| `LinearApiRequest` | `TrackerApiRequestError` | ✅ Equivalent |
| `LinearApiStatus` | `TrackerApiStatusError` | ✅ Equivalent |
| `LinearGraphQLErrors` | `TrackerAPIError` | ✅ Equivalent |
| `LinearUnknownPayload` | — | ❌ Removed |
| `LinearMissingEndCursor` | — | ❌ Removed |
| — | `TrackerApiConflictError` | ✅ New |
| — | `TrackerApiResourceNotFoundError` | ✅ New |
| — | `TrackerApiTimeoutError` | ✅ New |
| — | `TrackerApiRateLimitError` | ✅ New |

### 5.4 Breaking Changes

- **Base exception renamed:** `TrackerError` → `TrackerFactoryError`
- **Generic errors removed:** `LinearUnknownPayload`, `LinearMissingEndCursor`
- **New specific errors:** Conflict, NotFound, Timeout, RateLimit
- **Impact:** Low - mostly new exception types to catch

---

## 6. Orchestrator Usage Patterns

### 6.1 Expected Usage (Based on SPEC.md Analysis)

Based on analysis of the old tracker and config structure, the Orchestrator uses or will use the following patterns:

#### 6.1.1 Method Call Sites

| Line | Method | Usage |
|------|--------|-------|
| 194 | `fetch_candidate_issues()` | Get active issues for dispatch |
| 218 | `fetch_issues_by_states(terminal_states)` | Startup cleanup |
| 247 | `fetch_issue_states(running_ids)` | Active-run reconciliation |
| 766 | `fetch_candidate_issues()` | Periodic polling |

#### 6.1.2 Issue Field Access

| Field | Access Pattern | Status |
|-------|----------------|--------|
| `issue.id` | `issue.id` → `issue["id"]` | ⚠️ Requires change |
| `issue.identifier` | `issue.identifier` → `issue["identifier"]` | ⚠️ Requires change |
| `issue.title` | `issue.title` → `issue["title"]` | ⚠️ Requires change |
| `issue.state` | `issue.state` → `issue["state"]` | ⚠️ Requires change |
| `issue.priority` | `issue.priority` → `issue["priority"]` | ⚠️ Requires change |
| `issue.created_at` | `issue.created_at` → `issue["created_at"]` | ⚠️ Type change |
| `issue.blocked_by` | `issue.blocked_by` → `issue["blocked_by"]` | ⚠️ Requires change |

#### 6.1.3 Config Usage

```python
# Old way
tracker = create_tracker(config)
candidates = await tracker.fetch_candidate_issues()

# Expected new way
tracker = TrackerFactory.create(config)
candidates = tracker.fetch_candidate_issues()  # Sync
```

### 6.2 Orchestrator Integration Points

1. **Initialization:** `TrackerFactory.create(config)` → tracker instance
2. **Candidate polling:** `tracker.fetch_candidate_issues()` → list of issues
3. **State reconciliation:** `tracker.fetch_issue_states_by_ids(issue_ids)` → state map
4. **Terminal cleanup:** `tracker.fetch_issues_by_states(terminal_states)` → terminal issues

---

## 7. Breaking Changes Summary

### 7.1 Complete Breaking Change List

| # | Breaking Change | Category | Risk Level | Orchestrator Impact |
|---|----------------|----------|------------|-------------------|
| 1 | Domain model: dataclass → dict | Domain | **HIGH** | Requires dict access or wrapper |
| 2 | Async → sync execution | API | **MEDIUM** | Requires thread pool or facade |
| 3 | Method rename: fetch_issue_states → fetch_issue_states_by_ids | API | **LOW** | Simple search-replace |
| 4 | Parameter rename: states → state_names | API | **LOW** | Simple search-replace |
| 5 | terminal_states not passed to tracker | Config | **MEDIUM** | Filter in Orchestrator |
| 6 | Exception hierarchy changes | API | **LOW** | Update exception handling |
| 7 | Factory pattern: function → class | API | **LOW** | Change import and call |
| 8 | created_at type: str → datetime | Domain | **MEDIUM** | Type handling |
| 9 | Missing fields (description, branch_name, url, updated_at) | Domain | **LOW** | Not used by Orchestrator |

### 7.2 Risk Assessment Matrix

| Risk Level | Count | Items |
|------------|-------|-------|
| HIGH | 1 | Domain model change (dataclass → dict) |
| MEDIUM | 3 | Async→sync, terminal_states, created_at type |
| LOW | 5 | Method/param names, exceptions, factory pattern |

### 7.3 Migration Complexity by Change

| Change | Complexity | Estimated Effort |
|--------|-----------|---------------|
| Dict access wrapper | 2-4 hours | Create adapter/wrapper class |
| Async→sync bridge | 4-8 hours | Thread pool or facade |
| Method renaming | 1 hour | Search-replace |
| Config filtering | 2 hours | Add terminal state filtering |
| Exception handling | 2 hours | Update try/except blocks |
| Factory integration | 1 hour | Update import/call |

**Total Estimated Effort:** 12-20 hours

---

## 8. Compatibility Strategy Recommendations

### 8.1 Domain Model Compatibility

#### Option 1: Adapter Wrapper (dict → dataclass)

Create a wrapper that converts dict back to dataclass for backward compatibility:

```python
@dataclass
class IssueWrapper:
    """Wraps dict as Issue dataclass for backward compatibility."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.identifier = data.get("identifier", "")
        self.title = data.get("title", "")
        self.description = data.get("description")
        self.priority = data.get("priority")
        self.state = data.get("state", "")
        self.branch_name = None
        self.url = None
        self.labels = data.get("labels", [])
        self.blocked_by = data.get("blocked_by", [])
        
        # Handle datetime conversion
        created_at = data.get("created_at")
        self.created_at = created_at.isoformat() if created_at else None
        self.updated_at = None
```

**Pros:** Zero changes to Orchestrator code  
**Cons:** Additional wrapper layer, potential performance overhead

#### Option 2: Use Dict Directly in Orchestrator

Refactor Orchestrator to use dict access:

```python
# Before (dataclass)
if issue.state not in terminal_states:
    candidate = issue

# After (dict)
if issue["state"] not in terminal_states:
    candidate = issue
```

**Pros:** No additional layers, direct access  
**Cons:** Significant refactoring of Orchestrator

#### Option 3: Compatibility Dataclass

Create a minimal compatibility dataclass:

```python
@dataclass
class IssueDict:
    """Dict-compatible Issue wrapper."""
    
    _data: Dict[str, Any]
    
    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)
```

**Pros:** Minimal code changes, clear intent  
**Cons:** Additional abstraction

**Recommendation:** Option 1 (Adapter Wrapper) - Best balance of compatibility and maintainability

### 8.2 Async/Sync Compatibility

#### Option 1: Thread Pool Facade

Convert sync methods to async using `asyncio.run_in_executor`:

```python
import asyncio

class AsyncTrackerWrapper:
    """Wraps sync tracker as async for backward compatibility."""
    
    def __init__(self, tracker: TrackerClient):
        self._tracker = tracker
    
    async def fetch_candidate_issues(self) -> List[Issue]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._tracker.fetch_candidate_issues
        )
```

**Pros:** No changes to tracker implementation, async-compatible  
**Cons:** Thread pool overhead

#### Option 2: Make New Tracker Async

Refactor new tracker to use `aiohttp`:

**Pros:** Native async performance  
**Cons:** Significant refactoring

#### Option 3: Use Facade for Conversion

Use a simple facade that returns futures:

```python
class TrackerFacade:
    """Facade to wrap sync tracker as async-like."""
    
    def __init__(self, tracker: TrackerClient):
        self._tracker = tracker
    
    def fetch_candidate_issues(self) -> List[Dict]:
        # Sync call - but returns in same interface
        return self._tracker.fetch_candidate_issues()
```

**Recommendation:** Option 1 (Thread Pool Facade) - Quick migration path

### 8.3 Configuration Compatibility

#### Option 1: Pass Config After Creation

```python
def create_tracker(config: Config) -> TrackerClient:
    tracker = TrackerFactory.create(config)
    
    # Post-configure terminal states if needed
    if hasattr(tracker, '_terminal_states'):
        tracker._terminal_states = config.tracker_terminal_states
    
    return tracker
```

#### Option 2: Use Config Object Directly

Pass entire config to tracker:

```python
class LinearTracker(TrackerClient):
    def __init__(self, config: Config):
        self._api_key = config.tracker_api_key
        # ... rest of config
```

**Recommendation:** Option 1 (Post-configure) - Minimal changes

### 8.4 Final Recommended Migration Path

```
Phase 1: Factory Integration
├── Replace create_tracker() import
├── Update to TrackerFactory.create(config)
└── Handle exception changes

Phase 2: Async Bridge  
├── Create AsyncTrackerWrapper class
├── Wrap sync tracker in facade
└── Use run_in_executor for async calls

Phase 3: Domain Model
├── Create IssueWrapper dict→dataclass
├── Use wrapper in all field access
└── Handle datetime conversion

Phase 4: Configuration
├── Add terminal_states filtering in Orchestrator
└── Pass additional config if needed
```

---

## 9. Next Steps (Phase 3 Preparation)

### 9.1 Immediate Actions

1. **Create migrations helper module** in `runtime/tracker/compat.py`
2. **Implement AsyncTrackerWrapper** for async compatibility
3. **Implement IssueWrapper** for dict→dataclass conversion
4. **Update factory** to support full config pass-through

### 9.2 Testing Requirements

- Unit tests for IssueWrapper conversion
- Integration tests for AsyncTrackerWrapper
- End-to-end tests with mock Linear API

### 9.3 Documentation Updates

- Update API references
- Add migration guide
- Document breaking changes in CHANGELOG

---

## Appendix A: File Locations

| Component | Path | Lines |
|-----------|------|-------|
| Old tracker | `runtime/symphony/tracker.py` | 528 |
| New tracker base | `runtime/tracker/base.py` | 52 |
| New tracker factory | `runtime/tracker/factory.py` | 217 |
| New Linear tracker | `runtime/tracker/linear.py` | 424 |
| New Jira tracker | `runtime/tracker/jira.py` | 88 |
| New normalization | `runtime/tracker/normalization.py` | 187 |
| Config | `runtime/symphony/config.py` | 230 |

---

## Appendix B: Code References

### B.1 Old Import
```python
from runtime.symphony.tracker import Issue, Tracker, create_tracker
```

### B.2 New Import
```python
from runtime.tracker import (
    TrackerClient,
    TrackerFactory,
    LinearTracker,
    # Exceptions
    TrackerAPIError,
    TrackerApiRequestError,
    TrackerApiStatusError,
)
```

---

*Document generated: April 12, 2026*