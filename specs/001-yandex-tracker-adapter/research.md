# Research: Yandex Tracker Adapter Plugin

**Feature**: Yandex Tracker Adapter Plugin  
**Date**: 2026-04-14  
**Purpose**: Resolve technical unknowns from implementation plan

---

## Research 1: HTTP Client Library Selection

**Question**: Which HTTP client library should be used for Yandex Tracker API v3 integration?

### Decision: httpx

**Rationale**:
- Modern async/sync API (supports both modes out of the box)
- HTTP/2 and HTTP/1.1 support (future-proof)
- Connection pooling and keep-alive (performance optimization)
- Type hints and extensive documentation
- Well-maintained and widely adopted in Python ecosystem
- Better timeout handling and retry mechanisms compared to requests
- Compatible with uv package management

### Alternatives Considered

1. **requests** (REJECTED)
   - **Pros**: Widely known, extensive community
   - **Cons**: No async support (blocking I/O), HTTP/2 support limited, older architecture
   - **Why rejected**: Py-symphony aims for modern, async-capable architecture. requests blocks event loop and limits performance potential.

2. **httpx** (SELECTED)
   - **Pros**: Async/sync support, HTTP/2, modern API, type hints, excellent docs
   - **Cons**: Slightly more complex API than requests
   - **Why selected**: Modern, future-proof, enables async operations without extra libraries

3. **aiohttp** (REJECTED)
   - **Pros**: Mature async HTTP client
   - **Cons**: API complexity, async-only (no sync mode), steeper learning curve
   - **Why rejected**: httpx provides simpler API with both async and sync modes.

### Implementation Notes

- Use synchronous client initially (matches existing tracker adapters)
- Design allows future async migration without library changes
- Configure default timeout: 30 seconds (from FR-009)
- Add retry logic for transient errors
- Connection pooling for API calls
- Support X-Org-ID and X-Cloud-Org-ID headers via `headers` parameter

---

## Research 2: Python Entry Points for Plugin Registration

**Question**: How to register Yandex Tracker adapter as a discoverable plugin via Python entry points?

### Decision: pyproject.toml entry_points configuration

**Rationale**:
- Standard Python packaging mechanism (PEP 621)
- Automatic discovery via `importlib.metadata` (built-in since Python 3.8)
- No runtime configuration required
- Supports metadata for plugin information extraction
- Compatible with uv package management

### Alternatives Considered

1. **Manual plugin registration** (REJECTED)
   - **Pros**: Full control over registration process
   - **Cons**: Requires manual configuration, prone to human error, not discoverable automatically
   - **Why rejected**: TrackerFactory requires automatic discovery via `discover_from_entry_points()`.

2. **pyproject.toml entry_points** (SELECTED)
   - **Pros**: Standard PEP 621 mechanism, automatic discovery, supports metadata
   - **Cons**: Requires proper package structure
   - **Why selected**: Required by TrackerFactory for auto-discovery mechanism.

### Implementation Notes

- Entry point group: `symphony.trackers`
- Entry point name: `yandex_tracker`
- Entry point reference: `symphony_yandex_tracker.adapter:YandexTrackerAdapter`
- Metadata via `__plugin_info__` attribute on adapter class
- Metadata fields: `name`, `version`, `tracker_kind` (must be "yandex_tracker"), `description`, `author`

### Example Configuration

```toml
[project]
name = "symphony-yandex-tracker"
version = "0.1.0"
description = "Yandex Tracker adapter for Symphony orchestration platform"
authors = ["py-symphony team"]

[project.entry-points."symphony.trackers"]
yandex_tracker = "symphony_yandex_tracker.adapter:YandexTrackerAdapter"
```

---

## Research 3: OAuth 2.0 and IAM Token Authentication

**Question**: How to handle OAuth 2.0 and IAM token authentication for Yandex Tracker API v3?

### Decision: Pass-through authentication with header detection

**Rationale**:
- Both token types use same `Authorization` header format
- Token format detection is simple: OAuth starts with `y0__`, IAM starts with `t1.`
- Token refresh is out of scope (FR-014: "adapter should handle refresh" - but implementation is token-level, not adapter-level)
- Keeps adapter simple and focused on API communication
- Matches SPEC.md assumption: "Token is pre-obtained via Yandex OAuth (not implementing OAuth 2.0 flow)"

### Alternatives Considered

1. **Full OAuth 2.0 flow implementation** (REJECTED)
   - **Pros**: Complete token lifecycle management
   - **Cons**: Complex, requires OAuth client credentials, redirect handling, state management
   - **Why rejected**: SPEC.md explicitly states OAuth flow is out of scope ("Token is pre-obtained").

2. **IAM token refresh mechanism** (REJECTED)
   - **Pros**: Handles 12-hour token lifetime (FR-014)
   - **Cons**: Requires Yandex Cloud SDK, adds complexity, out of adapter scope
   - **Why rejected**: FR-014 mentions "should handle" but implementation should be at token management level, not adapter level. Adapter can provide mechanism for token refresh callback if needed.

3. **Pass-through authentication with header detection** (SELECTED)
   - **Pros**: Simple, follows SPEC.md assumption, no external SDK dependencies
   - **Cons**: Token refresh is caller's responsibility
   - **Why selected**: Aligns with SPEC.md assumptions and keeps adapter focused on API communication.

### Implementation Notes

- Detect token format by prefix:
  - `y0__` → OAuth token, header: `Authorization: OAuth <token>`
  - `t1.` → IAM token, header: `Authorization: Bearer <token>`
- Authentication endpoint: GET /v2/myself (returns user info, validates token)
- Pass token directly to `Authorization` header for all API calls
- No token refresh in adapter (document this in README)
- Optional: Provide `on_token_refresh` callback parameter for future extensibility

---

## Research 4: Issue Normalization Strategy

**Question**: How to normalize Yandex Tracker issues to standardized format?

### Decision: Use standardized normalization utilities from runtime/tracker/normalization.py

**Rationale**:
- Ensures consistency across all tracker adapters
- Single source of truth for normalized issue structure
- Reduces code duplication
- Matches FR-004: "using standardized normalization utilities consistent with other tracker adapters"
- Enables predictable behavior for orchestration platform

### Alternatives Considered

1. **Custom normalization in adapter** (REJECTED)
   - **Pros**: Full control over normalization logic
   - **Cons**: Duplicates code, inconsistent with other adapters, harder to maintain
   - **Why rejected**: FR-004 explicitly requires using standardized utilities.

2. **Standardized utilities from runtime/normalization.py** (SELECTED)
   - **Pros**: Consistent across adapters, single source of truth, maintained centrally
   - **Cons**: May need adaptation for Yandex-specific fields
   - **Why selected**: Required by FR-004 and aligns with tracker-agnostic architecture.

### Implementation Notes

- Check if `runtime/tracker/normalization.py` exists and provides utilities
- If not exists, this is a task for implementation engineer to create
- Normalized fields (from SPEC.md requirements):
  - `id`: Internal issue ID
  - `identifier`: Issue key (e.g., "QUEUE-123")
  - `title`: Issue summary
  - `state`: Current status name
  - `priority`: Priority level
  - `created_at`: UTC timestamp
  - `labels`: List of tags/labels
  - `blocked_by`: List of blocking issue identifiers
- Map Yandex Tracker API fields to normalized format:
  - Yandex: `self`, `key`, `summary`, `status/self`, `priority/key`, `createdAt`, `tags`, `dependencies`
- Handle missing fields gracefully (set to None or default value)

---

## Research 5: Structured Logging Requirements

**Question**: How to implement structured logging with required context fields?

### Decision: Use Python standard logging with custom Formatter and structuredjson library

**Rationale**:
- Python logging is built-in and universally available
- Structured JSON logging for automated analysis (FR-016 requirement)
- Custom Formatter ensures all required fields are present
- No additional dependencies beyond standard library + structuredjson (lightweight)
- Meets FR-016: "structured logging format (JSON preferred) for automated analysis"

### Alternatives Considered

1. **Print statements** (REJECTED)
   - **Pros**: Simple, no dependencies
   - **Cons**: No structure, no context fields, not production-ready
   - **Why rejected**: FR-016 requires structured logging with specific context fields.

2. **Third-party logging library (structlog, loguru)** (REJECTED)
   - **Pros**: Rich features, async support
   - **Cons**: Adds dependency, violates "minimal dependencies" principle
   - **Why rejected**: Python standard logging + custom formatter is sufficient.

3. **Python logging + custom Formatter + structuredjson** (SELECTED)
   - **Pros**: Built-in, structured JSON, meets requirements, lightweight
   - **Cons**: Requires custom formatter implementation
   - **Why selected**: Balances functionality and minimalism, meets all FR-016 requirements.

### Implementation Notes

- Required context fields (from FR-016 and SPEC.md):
  - `issue_id` / `issue_identifier`: Tracker issue identifier
  - `action`: Operation being performed
  - `outcome`: `completed`, `failed`, `timeout`
  - `duration_ms`: Execution time in milliseconds
  - `error_message`: Error description on failure
  - `stack_trace`: Stack trace for debugging
- Log levels (FR-016):
  - `INFO`: Normal operations
  - `ERROR`: Failures
  - `DEBUG`: Detailed troubleshooting
- Sensitive information protection (FR-017):
  - Mask OAuth tokens and organization IDs
  - Do not log full user details
- UTC timestamping (FR-016):
  - Configure logger to use UTC±00:00 for all timestamps
- Custom formatter class:
  - Inherits from `logging.Formatter`
  - Converts log record to JSON with required fields
  - Adds `duration_ms` for API calls (measured with `time.perf_counter()`)

---

## Research 6: PATCH Operations and Array Field Updates

**Question**: How to handle PATCH operations with array field operations (add/remove/set/null)?

### Decision: Implement custom JSON encoder and field transformation logic

**Rationale**:
- Yandex Tracker API v3 supports special operations for array fields
- Requires JSON structure with nested objects for operations
- Custom encoder ensures correct API formatting
- Matches FR-018: "PATCH operations support all Issue fields including array operations"

### Alternatives Considered

1. **Direct JSON manipulation** (REJECTED)
   - **Pros**: Simple implementation
   - **Cons**: Error-prone, hard to maintain, no type safety
   - **Why rejected**: Complex nested structures require careful handling, custom encoder is safer.

2. **Custom JSON encoder + transformation logic** (SELECTED)
   - **Pros**: Type-safe, maintainable, handles edge cases
   - **Cons**: More complex than direct manipulation
   - **Why selected**: Ensures correct API formatting and provides type safety.

### Implementation Notes

- Array field operations (from FR-019):
  - `add`: Append to array
  - `remove`: Delete items from array
  - `set`: Overwrite array entirely
  - `null`: Clear array (empty array)
- Implementation approach:
  - Define dataclasses for UpdateIssueRequest with typed fields
  - Custom JSON encoder that serializes array operations to correct format
  - Example encoding:
    ```json
    {
      "followers": {
        "add": ["user1", "user2"],
        "remove": ["user3"]
      }
    }
    ```
- Optimistic locking (FR-021):
  - Include `version` field in PATCH requests
  - API returns 409 Conflict if version mismatch
  - Handle conflict by retrying with updated issue data
- Validation (FR-022):
  - Validate structure before sending to API
  - Remove unsupported fields
  - Format special operations correctly
  - Raise `ValidationError` if invalid

---

## Summary

All technical unknowns from the implementation plan have been resolved:

1. ✅ **HTTP Client**: httpx (modern, async/sync support, HTTP/2)
2. ✅ **Plugin Registration**: pyproject.toml entry_points under `symphony.trackers`
3. ✅ **Authentication**: Pass-through with token type detection (OAuth/IAM)
4. ✅ **Issue Normalization**: Use standardized utilities from `runtime/tracker/normalization.py`
5. ✅ **Structured Logging**: Python logging + custom JSON formatter
6. ✅ **PATCH Operations**: Custom JSON encoder with array field transformation

**No further clarifications needed.** Ready for Phase 1 design phase.