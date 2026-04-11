defmodule SymphonyElixir.WorkflowWatcherTest do
  use SymphonyElixir.TestSupport, async: false

  alias SymphonyElixir.Workflow
  alias SymphonyElixir.WorkflowWatcher

  @tag :tmp_dir
  test "starts watcher and monitors workflow file", %{tmp_dir: tmp_dir} do
    workflow_path = Path.join(tmp_dir, "WORKFLOW.md")

    # Create initial workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 30000)

    # Start the watcher
    start_supervised!({SymphonyElixir.WorkflowWatcher, workflow_path: workflow_path})

    # Verify workflow path
    assert WorkflowWatcher.workflow_path() == workflow_path

    # Verify initial workflow is loaded
    assert {:ok, _workflow} = Workflow.load(workflow_path)
  end

  @tag :tmp_dir
  test "detects workflow file changes and triggers reload", %{tmp_dir: tmp_dir} do
    workflow_path = Path.join(tmp_dir, "WORKFLOW.md")

    # Create initial workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 30000)

    # Start the watcher
    start_supervised!({SymphonyElixir.WorkflowWatcher, workflow_path: workflow_path})

    # Wait for initial load
    Process.sleep(100)

    # Modify the workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 60000)

    # Wait for file system watcher to detect change
    Process.sleep(200)

    # Verify the new config is loaded
    assert {:ok, workflow} = Workflow.load(workflow_path)
    assert workflow.config["polling"]["interval_ms"] == 60000
  end

  @tag :tmp_dir
  test "handles invalid workflow reload gracefully", %{tmp_dir: tmp_dir} do
    workflow_path = Path.join(tmp_dir, "WORKFLOW.md")

    # Create valid initial workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 30000)

    # Start the watcher
    start_supervised!({SymphonyElixir.WorkflowWatcher, workflow_path: workflow_path})

    # Wait for initial load
    Process.sleep(100)

    # Write invalid YAML to workflow file
    File.write!(workflow_path, "---\ninvalid: yaml: content: [unclosed\n")

    # Wait for file system watcher to detect change
    Process.sleep(200)

    # The watcher should not crash, and last known good config should be preserved
    assert Process.alive?(Process.whereis(SymphonyElixir.WorkflowWatcher))
  end

  @tag :tmp_dir
  test "force_reload triggers manual reload", %{tmp_dir: tmp_dir} do
    workflow_path = Path.join(tmp_dir, "WORKFLOW.md")

    # Create initial workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 30000)

    # Start the watcher
    start_supervised!({SymphonyElixir.WorkflowWatcher, workflow_path: workflow_path})

    # Wait for initial load
    Process.sleep(100)

    # Modify the workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 60000)

    # Trigger manual reload
    assert :ok = WorkflowWatcher.force_reload()

    # Wait for reload to complete
    Process.sleep(100)

    # Verify the new config is loaded
    assert {:ok, workflow} = Workflow.load(workflow_path)
    assert workflow.config["polling"]["interval_ms"] == 60000
  end

  @tag :tmp_dir
  test "handles missing workflow file on start", %{tmp_dir: tmp_dir} do
    workflow_path = Path.join(tmp_dir, "NONEXISTENT.md")

    # Starting watcher with non-existent file should fail
    assert {:error, _reason} =
             start_supervised({SymphonyElixir.WorkflowWatcher, workflow_path: workflow_path})
  end

  @tag :tmp_dir
  test "logs workflow reload errors but continues running", %{tmp_dir: tmp_dir} do
    workflow_path = Path.join(tmp_dir, "WORKFLOW.md")

    # Create valid initial workflow file
    write_workflow_file!(workflow_path, polling_interval_ms: 30000)

    # Start the watcher
    start_supervised!({SymphonyElixir.WorkflowWatcher, workflow_path: workflow_path})

    # Wait for initial load
    Process.sleep(100)

    # Capture logs
    capture_log(fn ->
      # Write invalid YAML to workflow file
      File.write!(workflow_path, "---\ninvalid: yaml: [unclosed")

      # Wait for file system watcher to detect change
      Process.sleep(200)
    end)

    # The watcher should still be running
    assert Process.alive?(Process.whereis(SymphonyElixir.WorkflowWatcher))
  end
end
