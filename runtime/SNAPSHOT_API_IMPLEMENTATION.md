# Snapshot API Implementation

## Overview

The `get_state_snapshot()` method has been implemented in the Python Orchestrator to provide runtime state for observability/dashboards, per SPEC.md Section 13.3.

## Implementation Details

### Files Modified

1. **symphony/orchestrator.py**
   - Added `get_state_snapshot()` method that returns a comprehensive snapshot of orchestrator state
   - Added polling state tracking (`_poll_check_in_progress`, `_next_poll_due_at_ms`)
   - Updated `RunningEntry` dataclass to include `workspace_path` and `codex_app_server_pid`
   - Updated `RetryEntry` dataclass to include `worker_host` and `workspace_path`
   - Updated `_poll_loop()` and `_tick()` methods to track polling state

2. **server/api.py**
   - Updated `get_state()` method to call `orchestrator.get_state_snapshot()`
   - Added route `/api/v1/state` for the snapshot endpoint

3. **orchestrator/state.py** (runtime/orchestrator/ directory)
   - Added `codex_rate_limits` field to `OrchestratorState`

4. **orchestrator/orchestrator.py** (runtime/orchestrator/ directory)
   - Added `get_state_snapshot()` method (for reference implementation)

## Snapshot Structure

The snapshot returns a dict with the following structure:

```python
{
    "running": [
        {
            "issue_id": str,
            "identifier": str,
            "state": str,  # tracker state (Todo, In Progress, etc.)
            "worker_host": Optional[str],
            "workspace_path": Optional[str],
            "session_id": Optional[str],
            "codex_app_server_pid": Optional[str],
            "codex_input_tokens": int,
            "codex_output_tokens": int,
            "codex_total_tokens": int,
            "turn_count": int,
            "started_at": str,  # ISO 8601 timestamp
            "last_codex_timestamp": Optional[str],
            "last_codex_message": Optional[str],
            "last_codex_event": Optional[str],
            "runtime_seconds": float,
        },
        ...
    ],
    "retrying": [
        {
            "issue_id": str,
            "attempt": int,
            "due_in_ms": int,
            "identifier": str,
            "error": Optional[str],
            "worker_host": Optional[str],
            "workspace_path": Optional[str],
        },
        ...
    ],
    "codex_totals": {
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int,
        "seconds_running": float,
    },
    "rate_limits": Optional[dict],  # Latest rate limit payload from Codex
    "polling": {
        "checking?": bool,
        "next_poll_in_ms": Optional[int],
        "poll_interval_ms": int,
    },
}
```

## API Endpoint

### GET /api/v1/state

Returns the current runtime state snapshot.

**Response Format:** JSON

**Example:**
```bash
curl http://localhost:8080/api/v1/state
```

## Async-Safety

The `get_state_snapshot()` method is designed to be async-safe:
- It reads from orchestrator state without modifying it
- All computations are local and don't involve I/O
- Can be called safely from async contexts

## Runtime Computation

The snapshot dynamically computes:
- `runtime_seconds` for each running session based on `started_at` and current time
- `due_in_ms` for each retry entry based on `due_at_ms` and current time
- `next_poll_in_ms` based on `_next_poll_due_at_ms` and current time

## Testing

Comprehensive tests have been added in `tests/test_get_state_snapshot.py`:

1. Empty state snapshot
2. Snapshot with running entries
3. Snapshot with retry entries
4. Snapshot with codex totals
5. Snapshot with rate limits
6. Polling status tracking

All tests pass successfully.

## Compatibility

This implementation mirrors the Elixir reference implementation (`elixir/lib/symphony_elixir/orchestrator.ex` lines 1083-1155) while adapting to Python's async/await patterns and data structures.

## Future Enhancements

Potential future improvements:
- Add workspace_path and codex_app_server_pid to RunningEntry when those values are available
- Add worker_host and workspace_path to RetryEntry when those values are available
- Add historical state tracking for observability trends
- Add filtering options for snapshot endpoints
