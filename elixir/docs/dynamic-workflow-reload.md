# Dynamic Workflow Reload Implementation

## Overview

This implementation adds dynamic configuration reloading for `WORKFLOW.md` without requiring a service restart, as specified in SPEC.md Section 6.2.

## Architecture

### Components

1. **SymphonyElixir.WorkflowWatcher** (New)
   - GenServer that watches the filesystem for changes to `WORKFLOW.md`
   - Uses the `file_system` library for efficient file watching
   - Triggers workflow reloads when changes are detected
   - Handles errors gracefully (logs errors, keeps last known good config)
   - Monitors the watcher process for unexpected failures

2. **SymphonyElixir.WorkflowStore** (Modified)
   - Previously used polling (every 1 second) to detect changes
   - Now relies on `WorkflowWatcher` to trigger reloads
   - Simplified logic: removed polling, stamp checking on `current()` calls
   - Still provides caching and graceful error handling
   - Maintains last known good configuration on reload failures

### Data Flow

```
WORKFLOW.md file changed
         ↓
FileSystem detects change
         ↓
WorkflowWatcher receives :file_event
         ↓
WorkflowWatcher calls WorkflowStore.force_reload()
         ↓
WorkflowStore loads new workflow
         ↓
If successful: updates cached workflow
If failed: logs error, keeps last known good config
         ↓
Config.settings() returns updated config on next call
```

## Key Features

### Dynamic Reload Semantics (SPEC.md Section 6.2)

✅ Watches `WORKFLOW.md` for changes
✅ Re-reads and re-applies workflow config without restart
✅ Adjusts live behavior to new config:
   - `polling.interval_ms`
   - `agent.max_concurrent_agents`
   - `tracker.active_states` and `tracker.terminal_states`
   - `codex` settings
✅ Reloaded config applies to:
   - Future dispatch decisions
   - Retry scheduling
   - Reconciliation decisions
   - Hook executions
   - Agent launches
✅ In-flight agent sessions are NOT automatically restarted (per spec)
✅ Defensive re-validation during runtime operations
✅ Invalid reloads don't crash the service (graceful error handling)

### Error Handling

- **File watcher startup failure**: WorkflowWatcher fails to start, logs error
- **Watcher process crash**: Monitored, logged, service continues with last known config
- **Invalid workflow file on reload**: Logged, last known good config preserved
- **Workflow file missing on reload**: Logged, last known good config preserved

### Logging

All important operations are logged:
- Watcher startup: `"Starting workflow watcher for #{path}"`
- Watching directory: `"Watching directory #{dir} for changes to #{filename}"`
- File change detected: `"File change detected for #{path} with events: #{inspect(events)}"`
- Successful reload: `"Successfully reloaded workflow from #{path}"`
- Failed reload: `"Failed to reload workflow from #{path}: #{inspect(reason)}; keeping last known good configuration"`
- Watcher stopped unexpectedly: `"File watcher stopped unexpectedly"`
- Watcher process died: `"Watcher process died with reason: #{inspect(reason)}"`

## Configuration

No additional configuration is required. The watcher automatically watches the `WORKFLOW.md` file specified in the application configuration.

## Testing

Tests are located in `test/symphony_elixir/workflow_watcher_test.exs`:

1. **Start watcher and monitor workflow file**
   - Verifies watcher starts with correct path
   - Confirms initial workflow is loaded

2. **Detect workflow file changes and trigger reload**
   - Modifies workflow file
   - Waits for file system watcher to detect change
   - Verifies new config is loaded

3. **Handle invalid workflow reload gracefully**
   - Writes invalid YAML to workflow file
   - Confirms watcher doesn't crash
   - Verifies last known good config is preserved

4. **Force reload triggers manual reload**
   - Tests manual reload via `WorkflowWatcher.force_reload()`
   - Verifies new config is loaded

5. **Handle missing workflow file on start**
   - Verifies watcher fails to start with non-existent file

6. **Log workflow reload errors but continue running**
   - Verifies errors are logged
   - Confirms watcher continues running after errors

## Migration from Polling

The previous polling-based approach (every 1 second) has been replaced with event-based file watching:

**Before:**
- `WorkflowStore` polled file system every 1 second
- Checked file modification time and hash
- Reloaded if changes detected

**After:**
- `WorkflowWatcher` uses `file_system` library
- Receives events when file changes
- Triggers reload only when necessary

Benefits:
- Reduced CPU usage (no polling)
- Faster response to changes (immediate notification)
- More efficient resource utilization
- Matches SPEC.md requirements for filesystem watching

## Dependencies

Added to `mix.exs`:
```elixir
{:file_system, "~> 1.0"}
```

The `file_system` library provides:
- Cross-platform file system watching
- Efficient event-based notifications
- Support for multiple backends (inotify, kqueue, FSEvents, ReadDirectoryChangesW)

## Integration Points

### Application Supervisor Tree

```elixir
children = [
  {Phoenix.PubSub, name: SymphonyElixir.PubSub},
  {Task.Supervisor, name: SymphonyElixir.TaskSupervisor},
  SymphonyElixir.WorkflowStore,        # Start store first
  SymphonyElixir.WorkflowWatcher,      # Then start watcher
  SymphonyElixir.Orchestrator,
  SymphonyElixir.HttpServer,
  SymphonyElixir.StatusDashboard
]
```

### Orchestrator Integration

The Orchestrator continues to use `Config.settings()` and `Config.settings!()` as before. When a workflow change is detected:

1. WorkflowWatcher triggers reload
2. WorkflowStore updates cached workflow
3. Next call to `Config.settings()` returns updated configuration
4. Orchestrator uses new config for subsequent operations

### CLI Integration

No changes required to CLI. The workflow path is still set via `CLI.run/1`, and the watcher automatically monitors that file.

## Future Enhancements

Potential improvements for future iterations:

1. **Hot-reload HTTP server port**: Currently requires restart (per spec, this is acceptable)
2. **Metrics**: Add Prometheus/metrics for reload success/failure rates
3. **Validation hooks**: Allow custom validation before applying new config
4. **Config diff logging**: Log what changed between old and new config
5. **Rollback support**: Ability to manually rollback to previous config

## Troubleshooting

### Watcher not detecting changes

Check logs for:
- `"Starting workflow watcher for #{path}"` - watcher started
- `"Watching directory #{dir} for changes to #{filename}"` - subscription active
- `"File change detected..."` - events being received

### Reload failing but watcher still running

Check logs for:
- `"Failed to reload workflow from #{path}: #{inspect(reason)}"`
- Verify workflow file syntax is valid
- Check file permissions

### Performance issues

The watcher should be very low overhead. If experiencing issues:
- Check file system event queue (some OSes have limits)
- Verify `file_system` backend is working correctly
- Monitor GenServer mailbox size

## References

- SPEC.md Section 6.2: Dynamic Reload Semantics
- `file_system` library: https://hex.pm/packages/file_system
- SymphonyElixir Documentation: `docs/`
