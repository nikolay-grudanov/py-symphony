# Per-State Concurrency Limits Implementation Summary

## Overview
Added per-state concurrency limits to the Python Orchestrator implementation as specified in SPEC.md Section 8.3.

## Changes Made

### 1. Configuration (`runtime/symphony/config.py`)

#### Added field to Config dataclass:
- `agent_max_concurrent_agents_by_state: dict[str, int]` - per-state concurrency limits

#### Added default value:
```python
"agent": {
    "max_concurrent_agents": 10,
    "max_concurrent_agents_by_state": {},  # NEW
    "max_retry_backoff_ms": 300000,
    "max_turns": 20,
}
```

#### Added validation function:
- `parse_per_state_limits()` - validates and normalizes per-state limits
  - Ignores non-positive values
  - Normalizes state keys to lowercase for consistent lookup

### 2. Orchestrator (`runtime/symphony/orchestrator.py`)

#### Added helper function:
- `_normalize_issue_state(state: str) -> str` - normalizes state names to lowercase

#### Added methods:
- `_running_issue_count_for_state(running, issue_state) -> int`
  - Counts running issues for a specific state
  - Normalizes both running entry states and query state for comparison
  - Case-insensitive matching

- `_state_slots_available(issue, running) -> bool`
  - Checks if there are available slots for the issue's state
  - Returns True if state limit not configured (fallback to global)
  - Returns True if limit configured and slots available
  - Returns False if state limit reached

#### Modified methods:
- `_can_dispatch(issue: Optional[Issue] = None) -> bool`
  - Now accepts optional issue parameter
  - Checks per-state limits if issue provided and limits configured
  - Maintains backward compatibility (works without issue parameter)

- `_tick()` - Updated to pass issue to `_can_dispatch(issue)`

- `_fire_retry()` - Updated to pass issue to `_can_dispatch(found)`

### 3. Tests (`runtime/tests/test_per_state_concurrency.py`)

Created comprehensive test suite with 14 test cases covering:
1. State normalization
2. Counting running issues by state
3. Case-insensitive state matching
4. State slot availability with/without limits
5. Independent state limits (different states have different limits)
6. Case-insensitive limit lookup
7. Fallback to global limit when state not configured
8. Integration with `_can_dispatch()`
9. Global limit takes precedence over state limits
10. Full dispatch loop simulation

Also updated existing test file (`test_worker_hosts.py`) to include new config field.

## Behavior

### Per SPEC.md Section 8.3:

**Global limit:**
```python
available_slots = max(max_concurrent_agents - running_count, 0)
```

**Per-state limit:**
```python
if state in max_concurrent_agents_by_state:
    limit = max_concurrent_agents_by_state[state]
    used = running_count_for_state(state)
    return limit > used
else:
    # Fallback to global limit
    return True
```

**State normalization:**
- All state keys normalized to lowercase for consistent lookup
- Case-insensitive matching for both configuration and runtime states

**Validation:**
- Invalid entries (non-positive, non-numeric) are silently ignored
- Empty dict means no per-state limits (fallback to global limit)

## Test Results

All tests pass:
- 14 new per-state concurrency tests
- 11 existing worker host tests (updated)
- Total: 25 tests passed

## Compatibility

- Backward compatible: existing code continues to work
- Default behavior unchanged (empty dict for per-state limits)
- Optional feature: only activates when configured

## Configuration Example

```yaml
agent:
  max_concurrent_agents: 10
  max_concurrent_agents_by_state:
    todo: 5
    in progress: 3
    # Other states fallback to global limit of 10
```

This allows fine-grained control over concurrency based on issue states,
useful for:
- Limiting resource-intensive states
- Prioritizing certain issue types
- Managing capacity for different workflow stages
