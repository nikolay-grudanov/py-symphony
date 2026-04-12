# SSH Worker Hosts Support Implementation Summary

## Overview
This document summarizes the implementation of SSH worker hosts support for the Python Orchestrator, matching the functionality provided in the Elixir reference implementation.

## Changes Made

### 1. Config Layer (`runtime/symphony/config.py`)

#### Added Worker Configuration Fields
- `worker_ssh_hosts: list[str]` - List of SSH host addresses for remote execution
- `worker_max_concurrent_agents_per_host: int` - Maximum number of concurrent agents per host

#### Default Values
```python
"worker": {
    "ssh_hosts": [],
    "max_concurrent_agents_per_host": 3,
}
```

### 2. Orchestrator Layer (`runtime/symphony/orchestrator.py`)

#### Updated Data Classes
- **RunningEntry**: Added `worker_host: Optional[str]` field to track which host is running the issue

#### New Methods

1. **`_can_dispatch(self) -> bool`** (Enhanced)
   - Now checks both global agent limit and worker host slots
   - Returns `False` if any SSH host is configured but no slots available

2. **`_worker_slots_available(self, preferred_worker_host: Optional[str] = None) -> bool`**
   - Checks if any worker host has available slots
   - Supports preferred host selection

3. **`_select_worker_host(self, preferred_worker_host: Optional[str] = None) -> Optional[str]`**
   - Selects the best worker host for a new agent
   - Uses preferred host if available and has slots
   - Otherwise selects least loaded host
   - Returns `None` if no capacity available

4. **`_preferred_worker_host_available(self, preferred_worker_host: Optional[str], hosts: list[str]) -> bool`**
   - Checks if preferred worker host is in available hosts list

5. **`_least_loaded_worker_host(self, hosts: list[str]) -> str`**
   - Selects host with fewest running agents
   - Uses tuple comparison (count, index) for determinism

6. **`_running_worker_host_count(self, worker_host: str) -> int`**
   - Counts number of agents currently running on specific host

7. **`_worker_host_slots_available(self, worker_host: str) -> bool`**
   - Checks if specific host has available slots
   - Respects `worker_max_concurrent_agents_per_host` limit

#### Updated Methods

1. **`_dispatch_issue(self, issue: Issue) -> None`**
   - Now calls `_select_worker_host()` to assign a worker host
   - Stores selected host in RunningEntry
   - Logs selected worker host

2. **`get_state_snapshot(self) -> dict`**
   - Added `worker_host` to each running entry in snapshot
   - Added `worker_hosts` section with configuration details

### 3. Tests (`runtime/tests/test_worker_hosts.py`)

Created comprehensive test suite with 11 test cases:
- Slot availability checks (empty, below limit, at limit)
- Running agent count per host
- Least loaded host selection
- Worker host selection with various states
- Dispatch validation with worker hosts
- Preferred worker host selection
- Capacity limits handling

## Key Design Decisions

1. **Backward Compatibility**: If `worker_ssh_hosts` is empty, the orchestrator behaves exactly as before (no SSH hosts).

2. **Dual Limiting**: Both global (`agent_max_concurrent_agents`) and per-host (`worker_max_concurrent_agents_per_host`) limits are enforced.

3. **Deterministic Selection**: When multiple hosts have the same load, the host with the lowest index is selected (based on Elixir implementation).

4. **Logging**: Added logging for:
   - Selected worker host
   - No capacity available warnings

5. **Type Safety**: All new code includes type hints following PEP 8 and Python best practices.

## Usage Example

### WORKFLOW.md Configuration
```yaml
---
worker:
  ssh_hosts:
    - host1.example.com
    - host2.example.com:2222
    - [::1]:2222  # IPv6 with port
  max_concurrent_agents_per_host: 3
---
```

### Expected Behavior
- Agents are distributed across SSH hosts based on current load
- Each host respects its max concurrent agents limit
- Least loaded host is preferred for new agents
- Global agent limit is also enforced
- If no SSH hosts configured, uses local execution (original behavior)

## Alignment with Elixir Reference

This implementation closely follows the Elixir reference (`elixir/lib/symphony_elixir/orchestrator.ex` lines 973-1033):

- ✅ `_select_worker_host()` matches `select_worker_host/2`
- ✅ `_worker_slots_available()` matches `worker_slots_available?/2`
- ✅ `_least_loaded_worker_host()` matches `least_loaded_worker_host/2`
- ✅ `_running_worker_host_count()` matches `running_worker_host_count/2`
- ✅ `_worker_host_slots_available()` matches `worker_host_slots_available?/2`
- ✅ Slot tracking in RunningEntry matches Elixir state structure

## Testing Results

All 11 tests pass:
```
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-8.4.2, pluggy-1.6.0
collected 11 items

tests/test_worker_hosts.py::TestWorkerHostSelection::test_worker_host_slots_available_empty PASSED [  9%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_worker_host_slots_available_below_limit PASSED [ 18%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_worker_host_slots_available_at_limit PASSED [ 27%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_running_worker_host_count PASSED [ 36%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_least_loaded_worker_host PASSED [ 45%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_select_worker_host_empty_state PASSED [ 54%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_select_worker_host_least_loaded PASSED [ 63%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_select_worker_host_no_capacity PASSED [ 72%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_can_dispatch_with_worker_hosts PASSED [ 81%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_can_dispatch_without_worker_hosts PASSED [ 90%]
tests/test_worker_hosts.py::TestWorkerHostSelection::test_preferred_worker_host_available PASSED [100%]

======================= 11 passed, 35 warnings in 0.08s =====================
```

## Code Quality

- ✅ All code passes Python syntax validation
- ✅ No flake8 linting issues
- ✅ Comprehensive docstrings (Google style)
- ✅ Type hints throughout
- ✅ Follows existing code style and patterns
- ✅ Test coverage for all new functionality

## Future Considerations

While this implementation provides the worker host selection and slot management, the actual SSH execution would need to be implemented in the AgentRunner component. The orchestrator now:
1. Selects the appropriate worker host
2. Tracks which host is running which issue
3. Enforces per-host limits
4. Provides host information in state snapshots

The AgentRunner would use the `worker_host` field from RunningEntry to determine whether to run locally or via SSH.
