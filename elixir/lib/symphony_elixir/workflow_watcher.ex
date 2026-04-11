defmodule SymphonyElixir.WorkflowWatcher do
  @moduledoc """
  Watches `WORKFLOW.md` for filesystem changes and triggers workflow reloads.

  This GenServer uses the `file_system` library to watch the workflow file
  for modifications. When a change is detected, it triggers a reload via
  `SymphonyElixir.WorkflowStore.force_reload/0`.

  The watcher handles errors gracefully:
  - Failed reloads are logged but don't crash the watcher
  - Last known good configuration is preserved
  - Operator-visible errors are emitted via Logger
  """

  use GenServer
  require Logger

  alias SymphonyElixir.Workflow
  alias SymphonyElixir.WorkflowStore

  @type state :: %{
          watcher_pid: pid() | nil,
          workflow_path: Path.t()
        }

  @doc """
  Starts the workflow watcher.

  ## Options

  - `:workflow_path` - Path to the WORKFLOW.md file. Defaults to `Workflow.workflow_file_path/0`.
  """
  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    workflow_path = Keyword.get(opts, :workflow_path, Workflow.workflow_file_path())
    GenServer.start_link(__MODULE__, workflow_path, name: __MODULE__)
  end

  @doc """
  Returns the current workflow path being watched.
  """
  @spec workflow_path() :: Path.t()
  def workflow_path do
    GenServer.call(__MODULE__, :workflow_path)
  end

  @doc """
  Manually triggers a workflow reload.
  """
  @spec force_reload() :: :ok | {:error, term()}
  def force_reload do
    GenServer.call(__MODULE__, :force_reload)
  end

  @impl true
  @spec init(Path.t()) :: {:ok, state()} | {:stop, term()}
  def init(workflow_path) do
    Logger.info("Starting workflow watcher for #{workflow_path}")

    case start_watcher(workflow_path) do
      {:ok, watcher_pid} ->
        {:ok, %{watcher_pid: watcher_pid, workflow_path: workflow_path}}

      {:error, reason} ->
        Logger.error("Failed to start watcher for #{workflow_path}: #{inspect(reason)}")
        {:stop, reason}
    end
  end

  @impl true
  def handle_call(:workflow_path, _from, %{} = state) do
    {:reply, state.workflow_path, state}
  end

  def handle_call(:force_reload, _from, %{} = state) do
    case reload_workflow() do
      :ok ->
        {:reply, :ok, state}

      {:error, reason} ->
        Logger.error("Failed to manually reload workflow: #{inspect(reason)}")
        {:reply, {:error, reason}, state}
    end
  end

  @impl true
  def handle_info({:file_event, _watcher_pid, {path, events}}, %{} = state) do
    handle_file_event(path, events, state)
  end

  def handle_info({:file_event, _watcher_pid, :stop}, %{} = state) do
    Logger.warning("File watcher stopped unexpectedly")
    {:noreply, %{state | watcher_pid: nil}}
  end

  def handle_info({:DOWN, _ref, :process, pid, reason}, %{watcher_pid: pid} = state) do
    Logger.error("Watcher process died with reason: #{inspect(reason)}")
    {:noreply, %{state | watcher_pid: nil}}
  end

  def handle_info(_msg, state), do: {:noreply, state}

  # Private functions

  defp start_watcher(path) do
    # Get the directory containing the workflow file
    dir = Path.dirname(path)
    # Get the filename to filter events
    filename = Path.basename(path)

    case FileSystem.start_link(dirs: [dir], name: __MODULE__.Worker) do
      {:ok, pid} ->
        # Subscribe to file events
        FileSystem.subscribe(pid)

        # Monitor the watcher process
        Process.monitor(pid)

        Logger.info("Watching directory #{dir} for changes to #{filename}")
        {:ok, pid}

      {:error, reason} ->
        {:error, {:watcher_start_failed, reason}}
    end
  end

  defp handle_file_event(path, events, state) do
    watched_filename = Path.basename(state.workflow_path)

    if String.ends_with?(path, watched_filename) and should_reload?(events) do
      Logger.debug("File change detected for #{path} with events: #{inspect(events)}")

      case reload_workflow() do
        :ok ->
          Logger.info("Successfully reloaded workflow from #{path}")

        {:error, reason} ->
          Logger.error(
            "Failed to reload workflow from #{path}: #{inspect(reason)}; keeping last known good configuration"
          )
      end
    end

    {:noreply, state}
  end

  defp should_reload?(events) do
    # Reload on modified, created, or renamed events
    # Ignore :ignored events (e.g., from temporary files)
    Enum.any?(events, fn event ->
      event in [:modified, :created, :renamed, :closed]
    end)
  end

  defp reload_workflow do
    WorkflowStore.force_reload()
  end
end
