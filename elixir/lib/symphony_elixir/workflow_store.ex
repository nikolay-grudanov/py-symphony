defmodule SymphonyElixir.WorkflowStore do
  @moduledoc """
  Caches the last known good workflow and reloads it when triggered.

  This GenServer stores the current workflow configuration and provides
  a cached interface. It does not poll for changes; instead, it relies
  on `SymphonyElixir.WorkflowWatcher` to trigger reloads when the
  workflow file is modified.

  The store handles errors gracefully by keeping the last known good
  configuration when a reload fails.
  """

  use GenServer
  require Logger

  alias SymphonyElixir.Workflow

  defmodule State do
    @moduledoc false

    defstruct [:path, :stamp, :workflow]
  end

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @spec current() :: {:ok, Workflow.loaded_workflow()} | {:error, term()}
  def current do
    case Process.whereis(__MODULE__) do
      pid when is_pid(pid) ->
        GenServer.call(__MODULE__, :current)

      _ ->
        Workflow.load()
    end
  end

  @spec force_reload() :: :ok | {:error, term()}
  def force_reload do
    case Process.whereis(__MODULE__) do
      pid when is_pid(pid) ->
        GenServer.call(__MODULE__, :force_reload)

      _ ->
        case Workflow.load() do
          {:ok, _workflow} -> :ok
          {:error, reason} -> {:error, reason}
        end
    end
  end

  @impl true
  def init(_opts) do
    case load_state(Workflow.workflow_file_path()) do
      {:ok, state} ->
        {:ok, state}

      {:error, reason} ->
        {:stop, reason}
    end
  end

  @impl true
  def handle_call(:current, _from, %State{} = state) do
    {:reply, {:ok, state.workflow}, state}
  end

  def handle_call(:force_reload, _from, %State{} = state) do
    path = Workflow.workflow_file_path()

    case load_state(path) do
      {:ok, new_state} ->
        {:reply, :ok, new_state}

      {:error, reason} ->
        log_reload_error(path, reason)
        {:reply, {:error, reason}, state}
    end
  end

  defp load_state(path) do
    with {:ok, workflow} <- Workflow.load(path),
         {:ok, stamp} <- current_stamp(path) do
      {:ok, %State{path: path, stamp: stamp, workflow: workflow}}
    else
      {:error, reason} ->
        {:error, reason}
    end
  end

  defp current_stamp(path) when is_binary(path) do
    with {:ok, stat} <- File.stat(path, time: :posix),
         {:ok, content} <- File.read(path) do
      {:ok, {stat.mtime, stat.size, :erlang.phash2(content)}}
    else
      {:error, reason} -> {:error, reason}
    end
  end

  defp log_reload_error(path, reason) do
    Logger.error("Failed to reload workflow path=#{path} reason=#{inspect(reason)}; keeping last known good configuration")
  end
end
