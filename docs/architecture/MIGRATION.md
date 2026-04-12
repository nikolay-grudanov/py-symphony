# Миграция с Elixir на Python-first архитектуру

**Версия**: 1.0
**Статус**: Draft
**Последнее обновление**: 2026-04-12
**Автор**: Implementation Engineer

---

## Executive Summary

Symphony переходит от Elixir-основанной реализации к Python-first архитектуре. Elixir остаётся как reference implementation, Python становится primary production runtime.

**Ключевые факты:**
- Elixir реализация: production-ready, ~1700 LOC основных компонентов, 14 модулей тестов
- Python реализация: partial reference, основные компоненты частично реализованы
- Новые архитектурные документы: полная спецификация системы
- Стратегия миграции: пофазная, с параллельным запуском и проверкой паритета

---

## 1. Классификация Elixir артефактов

### 1.1 Таблица классификации

| Категория | Статус | Классификация | Обоснование |
|-----------|---------|---------------|------------|
| **Orchestrator logic** | Полный | REWRITE | Python частично реализован (1316 LOC), нужно завершить по SPEC.md |
| **Workspace management** | Полный | REWRITE | Python частично реализован, нужен SSH и hooks |
| **Agent runner / Codex protocol** | Полный | REWRITE | Полностью отсутствует в Python |
| **Tracker adapters (Linear)** | Полный | REWRITE | Python частично реализован, нужна полная функциональность |
| **Config management** | Полный | REWRITE | Python частично реализован, нужна schema validation |
| **Workflow loader** | Полный | REUSE | Парсинг WORKFLOW.md - простой, можно адаптировать паттерны |
| **Dynamic reload** | Полный | REWRITE | Полностью отсутствует в Python |
| **SSH worker support** | Полный | REWRITE | Python частично реализован, нужна полная интеграция |
| **Token accounting** | Полный | REWRITE | Python реализован, но нужно интегрировать с Agent Runner |
| **Status dashboard (Phoenix/LiveView)** | Полный | DEPRECATE | Python будет использовать HTTP API + optional UI |
| **HTTP server** | Полный | REWRITE | Python нужен JSON API для observability |
| **Path safety** | Полный | REUSE | Простая валидация, можно адаптировать логику |
| **Tests** | ~250KB | REWRITE | Все тесты нужно переписать для Python |

### 1.2 Детальная классификация по модулям

#### Orchestrator (`orchestrator.ex` - 1655 LOC)

**Классификация:** REWRITE

**Что уже есть в Python:**
- Basic state structure (RunningEntry, RetryEntry, OrchestratorState)
- Poll loop skeleton
- Core dispatch logic
- Per-state concurrency ✅
- SSH worker hosts ✅
- Token accounting ✅
- Snapshot API ✅
- Stall detection ✅

**Что нужно добавить:**
- Complete reconciliation logic (state refresh from tracker)
- Terminal state cleanup
- Poll interval management
- Config refresh
- Workflow watcher integration
- Full error handling

**Паттерны для REUSE:**
- State machine transitions (Unclaimed → Claimed → Running → etc.)
- Retry backoff formula: `min(10000 * 2^(attempt - 1), max_retry_backoff_ms)`
- Stall detection algorithm
- Slot availability checks

---

#### Workspace (`workspace.ex` - 483 LOC)

**Классификация:** REWRITE

**Что уже есть в Python:**
- Basic workspace creation
- Workspace key sanitization
- Path validation

**Что нужно добавить:**
- SSH remote workspace creation
- Hooks execution (after_create, before_run, after_run, before_remove)
- Hook timeout management
- Remote workspace marker handling
- Workspace lifecycle management

**Паттерны для REUSE:**
- Hook execution context (cwd = workspace directory)
- Hook error handling (fatal vs non-fatal)
- Remote workspace preparation script
- Workspace path validation (must be under workspace root)

---

#### Agent Runner (`agent_runner.ex` - 203 LOC)

**Классификация:** REWRITE (с нуля)

**Что уже есть в Python:**
- Ничего ❌

**Что нужно реализовать:**
- Codex app-server protocol (JSON-RPC over stdio)
- Session initialization handshake
- Turn management (multiple turns per session)
- Turn streaming (line-delimited JSON)
- Timeout handling (read_timeout, turn_timeout, stall_timeout)
- Event forwarding to orchestrator
- Worker host integration (local vs SSH)
- Codex process lifecycle

**Паттерны для REUSE:**
- Protocol message formats (initialize, thread/start, turn/start, etc.)
- Event types (session_started, turn_completed, turn_failed, etc.)
- Turn continuation logic (worker decides to continue)
- Prompt building (Jinja2 template rendering)

---

#### Tracker (Linear) (`linear/` directory)

**Классификация:** REWRITE

**Что уже есть в Python:**
- Linear client skeleton (`tracker.py`)
- Issue dataclass
- Exception types

**Что нужно добавить:**
- Complete GraphQL queries
- Pagination handling
- Issue normalization
- State mapping
- Rate limiting (if applicable)

**Паттерны для REUSE:**
- GraphQL query structure
- Pagination cursor handling
- Issue field mapping from Linear API
- State normalization (lowercase)
- Label normalization

---

#### Config (`config.ex`)

**Классификация:** REWRITE

**Что уже есть в Python:**
- Basic config loading
- Defaults
- Environment variable resolution
- Per-state concurrency ✅
- SSH worker hosts ✅

**Что нужно добавить:**
- Schema validation
- Workflow prompt loading
- Codex runtime settings
- Hook script configuration
- Validation errors

**Паттерны для REUSE:**
- Environment variable indirection (`$VAR_NAME`)
- Home directory expansion (`~`)
- Schema validation rules
- Default value fallback

---

#### Workflow Loader (`workflow.ex`, `workflow_store.ex`, `workflow_watcher.ex`)

**Классификация:** REUSE (loader), REWRITE (watcher)

**Что уже есть в Python:**
- Basic WORKFLOW.md loading (`workflow.py`)

**Что нужно добавить:**
- YAML front matter parsing
- Jinja2 template extraction
- Dynamic reload on file changes
- Inotify / watchdog integration

**Паттерны для REUSE:**
- YAML parsing (PyYAML)
- Markdown body extraction
- Config validation

---

#### SSH Execution (`ssh.ex`)

**Классификация:** REWRITE

**Что уже есть в Python:**
- SSH host configuration ✅
- SSH host selection logic ✅

**Что нужно добавить:**
- SSH command execution
- SSH port forwarding support
- Remote script execution
- SSH config file support (`$SYMPHONY_SSH_CONFIG`)
- Error handling

**Паттерны для REUSE:**
- Command escaping
- Host:port parsing
- SSH options construction
- Remote shell execution (`bash -lc`)

---

#### Status Dashboard (`status_dashboard.ex` - 1952 LOC)

**Классификация:** DEPRECATE

**Обоснование:**
- Phoenix/LiveView - Elixir-specific технология
- Python будет использовать HTTP API + optional separate UI
- Complex UI не является core функциональностью

**Что заменить на:**
- JSON HTTP API (`GET /api/v1/state`)
- Optional simple terminal UI
- Optional web dashboard (separate project)

---

#### HTTP Server (`http_server.ex`)

**Классификация:** REWRITE

**Что уже есть в Python:**
- Basic HTTP server skeleton (`server/api.py`)

**Что нужно добавить:**
- Complete REST API (`/api/v1/*`)
- CORS support
- Authentication (optional)
- Rate limiting (optional)
- OpenAPI documentation

**Паттерны для REUSE:**
- Endpoints structure
- Response formats
- Error handling

---

#### Tests (14 модулей, ~250KB)

**Классификация:** REWRITE

**Тестовые модули для переписывания:**

| Elixir модуль | Строк | Покрытие | Python эквивалент |
|---------------|-------|-----------|-------------------|
| `core_test.exs` | 60030 | High | Требуется |
| `orchestrator_status_test.exs` | 48364 | High | Частично (test_stall_detection.py) |
| `workspace_and_config_test.exs` | 45885 | High | Требуется |
| `app_server_test.exs` | 45411 | High | Требуется (Agent Runner) |
| `extensions_test.exs` | 24740 | Medium | Требуется |
| `live_e2e_test.exs` | 25911 | Low | Требуется |
| `status_dashboard_snapshot_test.exs` | 8395 | Medium | Требуется (или DEPRECATE) |
| `dynamic_tool_test.exs` | 9902 | Low | Требуется |
| `cli_test.exs` | 4499 | Low | Требуется |
| `ssh_test.exs` | 6219 | High | Частично (test_worker_hosts.py) |
| `workflow_watcher_test.exs` | 4202 | Medium | Требуется |

**Что уже есть в Python:**
- `test_get_state_snapshot.py` (11K)
- `test_per_state_concurrency.py` (18K)
- `test_stall_detection.py` (14K)
- `test_token_accounting.py` (19K)
- `test_worker_hosts.py` (10K)

**Итого:** ~72K LOC в Python тестах против ~250K в Elixir (28% покрытие)

---

## 2. Пробелы реализации (Implementation Gaps)

### 2.1 Функциональность, отсутствующая в Python

#### Критические пробелы (P0)

1. **Agent Runner / Codex Protocol** - полностью отсутствует
   - ❌ Нет Codex app-server protocol реализации
   - ❌ Нет session initialization
   - ❌ Нет turn management
   - ❌ Нет event streaming

2. **SSH Execution** - частично реализовано
   - ✅ Конфигурация SSH hosts
   - ✅ Выбор worker host
   - ❌ Нет SSH command execution
   - ❌ Нет remote workspace operations

3. **HTTP Server** - частично реализовано
   - ✅ Базовый skeleton
   - ❌ Нет полных REST endpoints
   - ❌ Нет proper error handling

4. **Workflow Watcher** - полностью отсутствует
   - ❌ Нет dynamic reload на изменении WORKFLOW.md
   - ❌ Нет file watching

5. **Complete Tests** - существенно меньше
   - ✅ 5 тестовых файлов (~72K LOC)
   - ❌ Нужно 11+ дополнительных модулей

#### Важные пробелы (P1)

6. **Hooks Execution** - отсутствует в workspace
   - ❌ after_create hook
   - ❌ before_run hook
   - ❌ after_run hook
   - ❌ before_remove hook

7. **Complete Orchestrator** - частично реализовано
   - ✅ Core dispatch logic
   - ✅ Per-state concurrency
   - ✅ Token accounting
   - ❌ Полный reconciliation
   - ❌ Terminal state cleanup
   - ❌ Poll interval management

8. **Complete Tracker** - частично реализовано
   - ✅ Basic Linear client
   - ❌ Полная GraphQL реализация
   - ❌ Pagination handling
   - ❌ Error handling

9. **Config Validation** - частично реализовано
   - ✅ Basic loading
   - ❌ Schema validation
   - ❌ Workflow prompt loading

#### Желательные пробелы (P2)

10. **Status Dashboard UI** - deprecated в favour of HTTP API
    - ❌ Terminal UI (optional)
    - ❌ Web dashboard (optional, separate project)

11. **CLI** - базовая реализация
    - ✅ Basic CLI exists
    - ❌ Full command set

### 2.2 Функциональность из Elixir, отсутствующая в архитектурных документах

Следующие функции есть в Elixir, но не явно описаны в новых архитектурных документах:

1. **Workflow Watcher Integration** - dynamic reload
   - Elixir: `workflow_watcher.ex` - inotify watcher
   - Architecture docs: не явно описан механизм
   - **Решение:** Добавить в COMPONENTS.md как часть Workflow Layer

2. **Poll Interval Dynamic Adjustment**
   - Elixir: `refresh_runtime_config/1` - обновление конфигурации каждый tick
   - Architecture docs: не описан механизм
   - **Решение:** Добавить в Orchestrator секцию COMPONENTS.md

3. **Terminal State Cleanup**
   - Elixir: автоматическая очистка workspace для terminal issues
   - Architecture docs: не явно описана
   - **Решение:** Добавить в Workspace Manager секцию COMPONENTS.md

4. **SSH Config File Support**
   - Elixir: `$SYMPHONY_SSH_CONFIG` environment variable
   - Architecture docs: не описана
   - **Решение:** Добавить в INTEGRATIONS.md SSH секцию

5. **Observability PubSub**
   - Elixir: `ObservabilityPubSub` для real-time updates
   - Architecture docs: описан HTTP API, но не pub/sub
   - **Решение:** HTTP API достаточен для MVP

### 2.3 Адаптерные интерфейсы для реализации

Согласно ADAPTERS.md, следующие адаптеры нужно реализовать:

#### Issue Tracker Adapters

| Адаптер | Статус | Приоритет |
|---------|--------|----------|
| Linear | Частично реализован | P0 |
| GitHub Issues | Не реализован | P2 |
| Jira | Не реализован | P2 |
| Trello | Не реализован | P2 |

#### Agent Adapters

| Адаптер | Статус | Приоритет |
|---------|--------|----------|
| Codex (App-Server) | Не реализован | P0 |
| OpenAI Agents | Не реализован | P2 |
| Anthropic Claude | Не реализован | P2 |

#### Storage Adapters (Future)

| Адаптер | Статус | Приоритет |
|---------|--------|----------|
| Postgres | Не реализован | Future |
| SQLite | Не реализован | Future |
| Redis | Не реализован | Future |

---

## 3. Фазы миграции

### 3.1 Стратегия миграции

**Подход:** Gradual migration с параллельным запуском

**Обоснование:**
- Минимизация риска downtime
- Возможность параллельного тестирования
- Проверка feature parity перед переключением
- Возможность быстрого rollback

**Coexistence Strategy:**
- Фаза 1-2: Elixir production, Python dev/staging
- Фаза 3: Parallel run (both systems, один читает tracker)
- Фаза 4: Python production, Elixir standby (rollback ready)
- Фаза 5: Python production, Elixir deprecated

### 3.2 Фаза 0: Архитектура завершена ✅ (DONE)

**Статус:** ЗАВЕРШЕНО

**Что сделано:**
- ✅ System Architecture Docs (CONTEXT.md, DOMAIN-MODEL.md, COMPONENTS.md)
- ✅ Integration Contracts (INTEGRATIONS.md)
- ✅ Configuration Model (CONFIGURATION-MODEL.md)
- ✅ Artifact Model (ARTIFACT-MODEL.md)
- ✅ Observability Design (OBSERVABILITY.md)
- ✅ Security Model (SECURITY.md)
- ✅ Deployment Guide (DEPLOYMENT.md)

**Успех:** Архитектурная база готова для реализации

---

### 3.3 Фаза 1: Python Engine Core (2-3 недели)

**Цель:** Implement core orchestrator components with basic functionality

**Критерии успеха:**
- ✅ Orchestrator poll loop работает с Linear tracker
- ✅ Basic dispatch работает
- ✅ Workspace creation (local) работает
- ✅ Minimal Agent Runner (local Codex) работает
- ✅ Unit tests для core компонентов >80% coverage

**Задачи:**

#### 1.1 Orchestrator Core (1 неделя)

- [ ] **P0** Complete reconciliation logic
  - [ ] Implement `reconcile_running_issues()`
  - [ ] Implement terminal state detection
  - [ ] Implement state refresh from tracker
  - [ ] Implement workspace cleanup for terminal issues

- [ ] **P0** Complete poll interval management
  - [ ] Implement `refresh_runtime_config()`
  - [ ] Add config validation on each tick
  - [ ] Add error handling for invalid config

- [ ] **P0** Enhance error handling
  - [ ] Add comprehensive error logging
  - [ ] Add graceful degradation
  - [ ] Add error recovery logic

- [ ] **P1** Add orchestrator tests
  - [ ] Test dispatch logic
  - [ ] Test retry logic
  - [ ] Test reconciliation
  - [ ] Test error scenarios
  - [ ] Target: >80% coverage

**Зависимости:** Config (частично), Tracker (частично)

**Выходы:**
- `orchestrator.py` - полная реализация core logic
- `test_orchestrator.py` - comprehensive tests

---

#### 1.2 Workspace Core (3-4 дня)

- [ ] **P0** Implement hooks execution
  - [ ] `run_after_create_hook()`
  - [ ] `run_before_run_hook()`
  - [ ] `run_after_run_hook()`
  - [ ] `run_before_remove_hook()`

- [ ] **P0** Add hook timeout handling
  - [ ] Implement timeout enforcement
  - [ ] Add hook error handling (fatal vs non-fatal)
  - [ ] Add hook logging

- [ ] **P1** Enhance workspace tests
  - [ ] Test workspace creation
  - [ ] Test hooks execution
  - [ ] Test hook timeouts
  - [ ] Test hook failures
  - [ ] Target: >80% coverage

**Зависимости:** Config (полностью)

**Выходы:**
- `workspace.py` - полная реализация с hooks
- `test_workspace.py` - comprehensive tests

---

#### 1.3 Agent Runner MVP (1 неделя)

- [ ] **P0** Implement Codex app-server protocol
  - [ ] JSON-RPC message parsing
  - [ ] Session initialization handshake
  - [ ] Turn start/complete/failed handling
  - [ ] Event streaming

- [ ] **P0** Implement turn management
  - [ ] Multiple turns per session
  - [ ] Turn continuation logic
  - [ ] Turn timeout handling

- [ ] **P0** Add local Codex execution
  - [ ] Subprocess spawning
  - [ ] Stdio communication
  - [ ] Process lifecycle

- [ ] **P1** Add agent runner tests
  - [ ] Test protocol messages
  - [ ] Test session lifecycle
  - [ ] Test turn management
  - [ ] Test error scenarios
  - [ ] Target: >80% coverage

**Зависимости:** Orchestrator (полностью), Workspace (полностью)

**Выходы:**
- `agent.py` - полная реализация Agent Runner
- `test_agent.py` - comprehensive tests

---

#### 1.4 HTTP Server Basic (2-3 дня)

- [ ] **P1** Implement core REST API
  - [ ] `GET /api/v1/state` - state snapshot
  - [ ] `GET /api/v1/health` - health check
  - [ ] Error handling middleware

- [ ] **P1** Add CORS support
  - [ ] Configure CORS headers
  - [ ] Add optional authentication

- [ ] **P2** Add HTTP server tests
  - [ ] Test endpoints
  - [ ] Test error handling
  - [ ] Target: >70% coverage

**Зависимости:** Orchestrator (полностью)

**Выходы:**
- `server/api.py` - REST API endpoints
- `test_api.py` - comprehensive tests

---

**Фаза 1 Deliverables:**
- ✅ Orchestrator core (poll, dispatch, reconcile)
- ✅ Workspace core (creation, hooks)
- ✅ Agent Runner MVP (Codex protocol)
- ✅ HTTP server basic (state API)
- ✅ Unit tests >80% coverage

**Риск:** Agent Runner complexity может потребовать больше времени

---

### 3.4 Фаза 2: Первые интеграции (2-3 недели)

**Цель:** Add SSH support and complete Linear tracker integration

**Критерии успеха:**
- ✅ SSH remote workspaces работают
- ✅ Linear tracker полностью функционален
- ✅ Basic workflow watching работает
- ✅ Integration tests проходят

**Задачи:**

#### 2.1 SSH Execution Complete (1 неделя)

- [ ] **P0** Implement SSH command execution
  - [ ] SSH subprocess spawning
  - [ ] Remote command execution
  - [ ] SSH port support
  - [ ] SSH config file support (`$SYMPHONY_SSH_CONFIG`)

- [ ] **P0** Implement SSH remote workspace operations
  - [ ] Remote workspace creation
  - [ ] Remote workspace hooks execution
  - [ ] Remote workspace cleanup

- [ ] **P1** Add SSH tests
  - [ ] Test SSH command execution
  - [ ] Test remote workspace operations
  - [ ] Test SSH error handling
  - [ ] Target: >75% coverage

**Зависимости:** Workspace (полностью), Orchestrator (полностью)

**Выходы:**
- `ssh.py` - полная реализация SSH execution
- `test_ssh.py` - comprehensive tests

---

#### 2.2 Linear Tracker Complete (1 неделя)

- [ ] **P0** Complete GraphQL implementation
  - [ ] Candidate issues query
  - [ ] Issues by states query
  - [ ] Issue states by IDs query
  - [ ] Pagination handling

- [ ] **P0** Enhance issue normalization
  - [ ] Complete field mapping
  - [ ] State mapping
  - [ ] Label normalization
  - [ ] Blocker resolution

- [ ] **P1** Add Linear tests
  - [ ] Test GraphQL queries
  - [ ] Test pagination
  - [ ] Test error handling
  - [ ] Test normalization
  - [ ] Target: >80% coverage

**Зависимости:** Config (полностью)

**Выходы:**
- `tracker.py` - полная реализация Linear tracker
- `test_tracker.py` - comprehensive tests

---

#### 2.3 Workflow Watcher Basic (2-3 дня)

- [ ] **P1** Implement file watching
  - [ ] Watch WORKFLOW.md for changes
  - [ ] Trigger reload on change
  - [ ] Error handling for invalid config

- [ ] **P1** Add workflow watcher tests
  - [ ] Test file watching
  - [ ] Test config reload
  - [ ] Target: >70% coverage

**Зависимости:** Config (полностью), Orchestrator (полностью)

**Выходы:**
- `workflow_watcher.py` - file watching implementation
- `test_workflow_watcher.py` - comprehensive tests

---

#### 2.4 Integration Tests (3-4 дня)

- [ ] **P0** E2E test suite
  - [ ] Test full dispatch cycle
  - [ ] Test SSH remote execution
  - [ ] Test Linear integration
  - [ ] Test error recovery

- [ ] **P1** Performance tests
  - [ ] Measure poll loop performance
  - [ ] Measure dispatch latency
  - [ ] Measure SSH command overhead
  - [ ] Establish baseline metrics

**Зависимости:** Все компоненты фаз 1-2

**Выходы:**
- `test_e2e.py` - E2E test suite
- `test_performance.py` - performance benchmarks

---

**Фаза 2 Deliverables:**
- ✅ SSH execution (local + remote)
- ✅ Linear tracker (complete)
- ✅ Workflow watching (basic)
- ✅ Integration tests
- ✅ Performance baseline

**Риск:** SSH integration сложная, возможны проблемы с network/permissions

---

### 3.5 Фаза 3: Advanced Features (2-3 недели)

**Цель:** Add advanced features for production readiness

**Критерии успеха:**
- ✅ Dynamic reload работает
- ✅ Approval gates поддерживаются
- ✅ Observability complete
- ✅ Production-ready

**Задачи:**

#### 3.1 Dynamic Workflow Reload (1 неделя)

- [ ] **P1** Complete workflow watcher
  - [ ] Debounce file changes
  - [ ] Validate new config before reload
  - [ ] Graceful reload without downtime

- [ ] **P1** Orchestrator integration
  - [ ] Subscribe to workflow changes
  - [ ] Re-validate running issues with new config
  - [ ] Update runtime config on reload

- [ ] **P2** Add dynamic reload tests
  - [ ] Test config reload
  - [ ] Test graceful transition
  - [ ] Target: >70% coverage

**Зависимости:** Orchestrator (полностью), Workflow Watcher (basic)

**Выходы:**
- `workflow_watcher.py` - полная реализация
- `test_workflow_watcher.py` - comprehensive tests

---

#### 3.2 Approval Gates (1 неделя)

- [ ] **P2** Implement approval policy
  - [ ] Approval policy configuration
  - [ ] Approval timeout handling
  - [ ] Approval state tracking

- [ ] **P2** Orchestrator integration
  - [ ] Check approval before dispatch
  - [ ] Handle approval responses
  - [ ] Retry on approval timeout

- [ ] **P2** Add approval tests
  - [ ] Test approval flow
  - [ ] Test timeout handling
  - [ ] Target: >70% coverage

**Зависимости:** Orchestrator (полностью), Config (полностью)

**Выходы:**
- `approval.py` - approval policy implementation
- `test_approval.py` - comprehensive tests

---

#### 3.3 Observability Complete (3-4 дня)

- [ ] **P1** Enhanced logging
  - [ ] Structured logging with context
  - [ ] Log level configuration
  - [ ] Log rotation

- [ ] **P1** Metrics collection
  - [ ] Token usage metrics
  - [ ] Dispatch metrics
  - [ ] Error metrics

- [ ] **P2** Optional status UI
  - [ ] Terminal status UI (optional)
  - [ ] Web dashboard skeleton (optional)

**Зависимости:** Все компоненты

**Выходы:**
- `observability/` - logging and metrics
- `status_ui.py` - optional terminal UI

---

#### 3.4 Production Readiness (3-4 дня)

- [ ] **P1** Documentation
  - [ ] Deployment guide
  - [ ] Configuration reference
  - [ ] Troubleshooting guide

- [ ] **P1** Operational readiness
  - [ ] Health checks
  - [ ] Graceful shutdown
  - [ ] Error recovery procedures

- [ ] **P1** Security hardening
  - [ ] Input validation
  - [ ] Secret management
  - [ ] Security audit

**Зависимости:** Все компоненты

**Выходы:**
- `docs/deployment.md` - deployment guide
- `docs/configuration.md` - configuration reference
- `docs/troubleshooting.md` - troubleshooting guide

---

**Фаза 3 Deliverables:**
- ✅ Dynamic workflow reload
- ✅ Approval gates
- ✅ Complete observability
- ✅ Production documentation

**Риск:** Advanced features могут быть deprioritized для более быстрого релиза

---

### 3.6 Фаза 4: Parallel Run & Switchover (1-2 недели)

**Цель:** Run Python and Elixir in parallel, verify parity, switch to Python

**Критерии успеха:**
- ✅ Feature parity verified
- ✅ Performance comparable
- ✅ No critical bugs found
- ✅ Python production-ready

**Задачи:**

#### 4.1 Parallel Setup (2-3 дня)

- [ ] **P0** Configure parallel run
  - [ ] Elixir production on current infrastructure
  - [ ] Python staging on new infrastructure
  - [ ] Both reading same Linear project (read-only mode)

- [ ] **P0** Feature parity checklist
  - [ ] Create comprehensive checklist
  - [ ] Verify each feature works
  - [ ] Document any differences

**Выходы:**
- Feature parity checklist
- Parallel run configuration

---

#### 4.2 Verification (1 неделя)

- [ ] **P0** Feature verification
  - [ ] Test all orchestrator features
  - [ ] Test SSH remote execution
  - [ ] Test Linear integration
  - [ ] Test error scenarios

- [ ] **P1** Performance comparison
  - [ ] Measure Python vs Elixir performance
  - [ ] Identify bottlenecks
  - [ ] Optimize if needed

- [ ] **P1** Load testing
  - [ ] Test with realistic load
  - [ ] Verify stability
  - [ ] Identify limits

**Выходы:**
- Feature parity report
- Performance comparison report
- Load test results

---

#### 4.3 Switchover (2-3 дня)

- [ ] **P0** Gradual traffic shift
  - [ ] 10% to Python
  - [ ] Monitor for issues
  - [ ] Increase to 50%
  - [ ] Monitor for issues
  - [ ] Increase to 100%

- [ ] **P0** Rollback plan ready
  - [ ] Elixir kept in standby
  - [ ] Quick rollback procedure documented
  - [ ] Rollback tested

- [ ] **P1** Elixir deprecation
  - [ ] Mark Elixir as deprecated
  - [ ] Update documentation
  - [ ] Plan Elixir removal

**Выходы:**
- Switchover plan executed
- Rollback procedure documented
- Elixir deprecation notice

---

**Фаза 4 Deliverables:**
- ✅ Python production deployment
- ✅ Feature parity verified
- ✅ Elixir standby ready
- ✅ Rollback plan ready

**Риск:** Switchover complexity, rollback execution

---

### 3.7 Фаза 5: Elixir Deprecation & Cleanup (1 неделя)

**Цель:** Deprecate Elixir implementation, clean up code

**Критерии успеха:**
- ✅ Python stable in production
- ✅ No critical issues reported
- ✅ Elixir marked as deprecated

**Задачи:**

- [ ] **P2** Monitor Python production
  - [ ] Monitor for 1-2 weeks
  - [ ] Fix any issues
  - [ ] Gather feedback

- [ ] **P2** Deprecate Elixir
  - [ ] Add deprecation notice to Elixir code
  - [ ] Update documentation
  - [ ] Archive Elixir branch

- [ ] **P2** Clean up
  - [ ] Remove Elixir-specific CI/CD
  - [ ] Archive Elixir infrastructure
  - [ ] Update operational procedures

**Выходы:**
- Elixir deprecation notice
- Updated documentation
- Cleanup completed

---

**Фаза 5 Deliverables:**
- ✅ Python stable production
- ✅ Elixir deprecated
- ✅ Cleanup complete

**Риск:** Late bugs discovered in Python

---

## 4. Приоритизированный бэклог (Backlog)

### 4.1 P0: Must-have для MVP

| ID | Задача | Описание | Зависимости | Оценка |
|----|--------|----------|-------------|--------|
| **P0-1** | Orchestrator: Complete reconciliation | Реализовать полную логику reconciliation (state refresh, terminal cleanup) | Config, Tracker | 3 дня |
| **P0-2** | Orchestrator: Poll interval management | Добавить управление poll interval и refresh runtime config | Config | 2 дня |
| **P0-3** | Orchestrator: Error handling | Comprehensive error handling во всех путях выполнения | Все | 2 дня |
| **P0-4** | Workspace: Hooks execution | Реализовать all 4 hooks (after_create, before_run, after_run, before_remove) | Config | 2 дня |
| **P0-5** | Workspace: Hook timeouts | Добавить timeout enforcement для hooks | P0-4 | 1 день |
| **P0-6** | Agent Runner: Codex protocol | Полная реализация JSON-RPC protocol для Codex app-server | Orchestrator | 5 дней |
| **P0-7** | Agent Runner: Turn management | Реализовать multiple turns, continuation, timeouts | P0-6 | 2 дня |
| **P0-8** | Agent Runner: Local execution | Локальный Codex subprocess spawning | P0-6 | 1 день |
| **P0-9** | SSH: Command execution | SSH command execution subprocess spawning | Workspace | 3 дня |
| **P0-10** | SSH: Remote workspace | Remote workspace operations (creation, hooks, cleanup) | P0-9 | 2 дня |
| **P0-11** | Linear: Complete GraphQL | Полная GraphQL реализация с pagination | Config | 3 дня |
| **P0-12** | Linear: Issue normalization | Полная нормализация issues | P0-11 | 2 дня |
| **P0-13** | HTTP Server: State API | `GET /api/v1/state` endpoint | Orchestrator | 1 день |
| **P0-14** | Tests: Orchestrator | Comprehensive orchestrator tests (>80% coverage) | P0-1, P0-2, P0-3 | 3 дня |
| **P0-15** | Tests: Workspace | Comprehensive workspace tests (>80% coverage) | P0-4, P0-5 | 2 дня |
| **P0-16** | Tests: Agent Runner | Comprehensive agent runner tests (>80% coverage) | P0-6, P0-7, P0-8 | 3 дня |
| **P0-17** | Tests: SSH | Comprehensive SSH tests (>75% coverage) | P0-9, P0-10 | 2 дня |
| **P0-18** | Tests: Linear | Comprehensive Linear tests (>80% coverage) | P0-11, P0-12 | 2 дня |
| **P0-19** | Tests: Integration | E2E integration tests | Все P0 | 2 дня |

**Итого P0:** 19 задач, ~45 дней работы

---

### 4.2 P1: Важно для production

| ID | Задача | Описание | Зависимости | Оценка |
|----|--------|----------|-------------|--------|
| **P1-1** | Orchestrator: Config validation | Валидация конфигурации перед dispatch | Config | 1 день |
| **P1-2** | Orchestrator: State snapshot optimization | Оптимизация `get_state_snapshot()` | Orchestrator | 1 день |
| **P1-3** | Config: Schema validation | Schema validation для всех config полей | Config | 2 дня |
| **P1-4** | Config: Workflow prompt | Загрузка workflow prompt из WORKFLOW.md | Config | 1 день |
| **P1-5** | HTTP Server: Health endpoint | `GET /api/v1/health` endpoint | HTTP Server | 1 день |
| **P1-6** | HTTP Server: CORS | CORS support для HTTP API | P1-5 | 1 день |
| **P1-7** | Workflow Watcher: File watching | Базовая file watching для WORKFLOW.md | Config, Orchestrator | 2 дня |
| **P1-8** | Workflow Watcher: Reload on change | Dynamic config reload on file change | P1-7 | 2 дня |
| **P1-9** | Dynamic Reload: Debounce | Debounce file changes для быстрой последовательности | P1-8 | 1 день |
| **P1-10** | Dynamic Reload: Graceful transition | Graceful transition без downtime при reload | P1-9 | 2 дня |
| **P1-11** | Observability: Structured logging | Structured logging с context fields | Все | 2 дня |
| **P1-12** | Observability: Log levels | Configurable log levels | P1-11 | 1 день |
| **P1-13** | Observability: Log rotation | Log rotation configuration | P1-11 | 1 день |
| **P1-14** | Metrics: Token usage | Token usage metrics collection | Orchestrator | 1 день |
| **P1-15** | Metrics: Dispatch metrics | Dispatch metrics (success/failure/retry) | Orchestrator | 1 день |
| **P1-16** | Metrics: Error metrics | Error metrics aggregation | Все | 1 день |
| **P1-17** | Tests: HTTP Server | HTTP server tests (>70% coverage) | P1-5, P1-6 | 1 день |
| **P1-18** | Tests: Workflow Watcher | Workflow watcher tests (>70% coverage) | P1-7, P1-8, P1-9, P1-10 | 2 дня |
| **P1-19** | Tests: Performance | Performance benchmarks | Все | 2 дня |
| **P1-20** | Documentation: Deployment | Deployment guide | Все | 2 дня |
| **P1-21** | Documentation: Configuration | Configuration reference | Config | 2 дня |
| **P1-22** | Documentation: Troubleshooting | Troubleshooting guide | Все | 2 дня |
| **P1-23** | Ops: Health checks | Health check endpoints | HTTP Server | 1 день |
| **P1-24** | Ops: Graceful shutdown | Graceful shutdown handling | Orchestrator | 1 день |
| **P1-25** | Security: Input validation | Input validation для всех входов | Все | 2 дня |
| **P1-26** | Security: Secret management | Secret management integration | Config | 1 день |
| **P1-27** | Parallel Run: Setup | Configure parallel Elixir + Python run | Все P0, P1 | 2 дня |
| **P1-28** | Parallel Run: Parity verification | Feature parity checklist verification | P1-27 | 2 дня |
| **P1-29** | Switchover: Gradual traffic | Gradual traffic shift to Python | P1-27, P1-28 | 2 дня |
| **P1-30** | Switchover: Rollback plan | Rollback plan documentation и testing | P1-29 | 1 день |

**Итого P1:** 30 задач, ~42 дней работы

---

### 4.3 P2: Nice-to-have

| ID | Задача | Описание | Зависимости | Оценка |
|----|--------|----------|-------------|--------|
| **P2-1** | Approval Gates: Policy | Approval policy configuration | Config | 2 дня |
| **P2-2** | Approval Gates: Timeout | Approval timeout handling | P2-1 | 1 день |
| **P2-3** | Approval Gates: Integration | Orchestrator integration для approvals | P2-1, P2-2 | 2 дня |
| **P2-4** | Status UI: Terminal | Terminal status UI (optional) | Orchestrator | 3 дня |
| **P2-5** | Status UI: Web dashboard | Web dashboard skeleton (optional) | P2-4 | 5 дней |
| **P2-6** | Tracker: GitHub Issues | GitHub Issues adapter | Tracker interface | 3 дня |
| **P2-7** | Tracker: Jira | Jira adapter | Tracker interface | 5 дней |
| **P2-8** | Tracker: Trello | Trello adapter | Tracker interface | 3 дня |
| **P2-9** | Agent: OpenAI Agents | OpenAI Agents adapter | Agent interface | 3 дня |
| **P2-10** | Agent: Anthropic Claude | Anthropic Claude adapter | Agent interface | 3 дня |
| **P2-11** | Storage: Postgres | Postgres storage backend | Storage interface | 5 дней |
| **P2-12** | Storage: SQLite | SQLite storage backend | Storage interface | 2 дня |
| **P2-13** | Storage: Redis | Redis storage backend | Storage interface | 2 дня |
| **P2-14** | Tests: Approval | Approval gates tests (>70% coverage) | P2-1, P2-2, P2-3 | 2 дня |
| **P2-15** | Tests: Status UI | Status UI tests (>60% coverage) | P2-4, P2-5 | 2 дня |
| **P2-16** | Tests: Tracker adapters | Tracker adapter tests (>60% coverage) | P2-6, P2-7, P2-8 | 4 дня |
| **P2-17** | Tests: Agent adapters | Agent adapter tests (>60% coverage) | P2-9, P2-10 | 3 дня |
| **P2-18** | Elixir: Deprecation notice | Add deprecation notice to Elixir | Python stable | 1 день |
| **P2-19** | Elixir: Archive | Archive Elixir branch | P2-18 | 1 день |
| **P2-20** | Elixir: Cleanup | Remove Elixir CI/CD и infrastructure | P2-19 | 2 дня |

**Итого P2:** 20 задач, ~55 дней работы

---

## 5. Оценка сроков и ресурсов

### 5.1 Временная шкала

| Фаза | Длительность | Зависимости | P0 задач | P1 задач | P2 задач |
|------|-------------|--------------|----------|----------|----------|
| Фаза 0 (DONE) | - | - | - | - | - |
| Фаза 1 | 2-3 недели | Фаза 0 | 11 | 2 | 0 |
| Фаза 2 | 2-3 недели | Фаза 1 | 8 | 7 | 0 |
| Фаза 3 | 2-3 недели | Фаза 2 | 0 | 21 | 2 |
| Фаза 4 | 1-2 недели | Фаза 3 | 0 | 3 | 0 |
| Фаза 5 | 1 неделя | Фаза 4 | 0 | 0 | 3 |
| **Итого** | **8-13 недель** | - | **19** | **30** | **20** |

### 5.2 Минимальный MVP

**MVP Timeline (агрессивный):**
- Фаза 1 (сжато): 2 недели
- Фаза 2 (сжато): 2 недели
- **Итого:** 4 недели (1 месяц) для basic production-ready Python implementation

**MVP Deliverables:**
- ✅ Orchestrator core (dispatch, reconcile)
- ✅ Workspace core (creation, hooks)
- ✅ Agent Runner MVP (Codex protocol)
- ✅ SSH execution (local + remote)
- ✅ Linear tracker (complete)
- ✅ HTTP server (state API)
- ✅ Basic tests (>70% coverage)

**MVP NOT включающий:**
- ❌ Dynamic workflow reload
- ❌ Approval gates
- ❌ Advanced observability
- ❌ Status UI
- ❌ Additional trackers/agents

### 5.3 Полная миграция

**Full Migration Timeline:**
- Фаза 1-3 (implementation): 6-9 недель
- Фаза 4 (parallel run): 1-2 недели
- Фаза 5 (cleanup): 1 неделя
- **Итого:** 8-12 недель (2-3 месяца)

**Full Migration Deliverables:**
- ✅ Все P0 задачи (MVP)
- ✅ Все P1 задачи (production-ready)
- ✅ Выборочно P2 задачи (по приоритету)
- ✅ Python production deployment
- ✅ Elixir deprecation

### 5.4 Требуемые ресурсы

**Team composition (рекомендуется):**
- 1 Senior Python Engineer (Implementation Engineer) - 100%
- 1 Backend Engineer (Python/Infrastructure) - 50%
- 1 QA/Test Engineer - 30%

**Если ограниченные ресурсы (1 человек):**
- Минимум 3-4 месяца для полной миграции
- MVP возможен за 6-8 недель при полной загрузке

---

## 6. Риски и стратегия смягчения

### 6.1 Технические риски

| Риск | Вероятность | Влияние | Стратегия смягчения |
|------|-------------|----------|---------------------|
| **Agent Runner сложность** | Высокая | Высокое | Начать с прототипа, early validation с Elixir reference |
| **SSH integration** | Средняя | Высокое | Extensive testing, mock SSH для unit тестов |
| **Производительность Python** | Средняя | Среднее | Early performance benchmarks, оптимизация hot paths |
| **Баги в production** | Средняя | Высокое | Parallel run, feature parity verification, quick rollback |
| **Отсутствие feature parity** | Средняя | Высокое | Comprehensive feature checklist, automated parity tests |
| **Network latency (SSH)** | Низкая | Среднее | Connection pooling, retries, timeout handling |

### 6.2 Операционные риски

| Риск | Вероятность | Влияние | Стратегия смягчения |
|------|-------------|----------|---------------------|
| **Downtime при switchover** | Низкая | Высокое | Gradual traffic shift, rollback plan готов |
| **Ошибка в rollback** | Низкая | Критическое | Test rollback procedure, keep Elixir standby |
| **Отсутствие documentation** | Средняя | Среднее | Write docs parallel с кодом, review documentation |
| **Knowledge loss (Elixir)** | Средняя | Среднее | Archive Elixir code, keep reference for 6 месяцев |

### 6.3 Риски расписания

| Риск | Вероятность | Влияние | Стратегия смягчения |
|------|-------------|----------|---------------------|
| **Оценка времени занижена** | Высокая | Высокое | 20% buffer в планировании, weekly reviews |
| **Блокирующие задачи** | Средняя | Высокое | Identify dependencies early, parallel work streams |
| **Unforeseen complexity** | Средняя | Среднее | Spike investigation для неизвестных областей |
| **Отмена или изменение требований** | Низкая | Высокое | Weekly sync с архитекторами, адаптивный бэклог |

### 6.4 Rollback Plan

**Trigger условия для rollback:**
- Critical bugs в Python production
- Performance degradation >50% vs Elixir
- Data corruption или loss
- Security vulnerabilities
- Operator feedback indicating significant issues

**Rollback procedure:**
1. Немедленный stop Python service
2. Start Elixir standby service
3. Verify Elixir работает корректно
4. Redirect traffic обратно к Elixir
5. Investigate и fix issues в Python
6. Retry switchover после fix verification

**Rollback timeframe:** 5-10 минут (если Elixir standby готов)

---

## 7. Success Criteria

### 7.1 Фаза 1 Success Criteria

- [ ] Orchestrator успешно выполняет poll loop
- [ ] Dispatch работает для корректных issues
- [ ] Workspace creation (local) работает
- [ ] Hooks выполняются корректно
- [ ] Agent Runner MVP может запустить Codex и выполнить turn
- [ ] HTTP server возвращает state snapshot
- [ ] Unit tests coverage >80% для core компонентов
- [ ] Все тесты проходят стабильно

### 7.2 Фаза 2 Success Criteria

- [ ] SSH remote workspaces создаются и используются
- [ ] Linear tracker выполняет все required queries
- [ ] Pagination работает корректно
- [ ] Workflow watcher детектирует изменения WORKFLOW.md
- [ ] Integration tests проходят (E2E scenarios)
- [ ] Performance baseline установлен
- [ ] Unit tests coverage >75% для SSH и Linear

### 7.3 Фаза 3 Success Criteria

- [ ] Dynamic workflow reload работает без downtime
- [ ] Config changes применяются корректно
- [ ] Approval gates работают (если реализованы)
- [ ] Observability complete (structured logging, metrics)
- [ ] Production documentation complete
- [ ] Security review пройден

### 7.4 Фаза 4 Success Criteria

- [ ] Feature parity checklist на 100%
- [ ] Performance comparable с Elixir (<20% difference)
- [ ] Load tests показывают стабильность
- [ ] Python работает корректно с 10%, 50%, 100% traffic
- [ ] Rollback plan протестирован и задокументирован
- [ ] Elixir standby ready

### 7.5 Фаза 5 Success Criteria

- [ ] Python стабилен в production 1-2 недели
- [ ] No critical issues reported
- [ ] Elixir помечен как deprecated
- [ ] Documentation обновлена
- [ ] Elixir CI/CD и infrastructure archived

---

## 8. Связь с другими документами

- **[SDD.md](SDD.md)** - System Design Document, архитектурные решения
- **[CONTEXT.md](CONTEXT.md)** - System context и границы
- **[DOMAIN-MODEL.md](DOMAIN-MODEL.md)** - Domain entities и их отношения
- **[COMPONENTS.md](COMPONENTS.md)** - Component breakdown и ответственности
- **[INTEGRATIONS.md](INTEGRATIONS.md)** - Интеграции с внешними системами
- **[SPEC.md](../../SPEC.md)** - Полная техническая спецификация

---

## 9. TODO

### 9.1 Pre-Migration Tasks

- [ ] Review и approve migration plan с командой
- [ ] Setup infrastructure для Python staging
- [ ] Configure monitoring и alerting для Python
- [ ] Establish communication channel для migration updates

### 9.2 Migration Execution

- [ ] Start Phase 1 implementation
- [ ] Weekly progress reviews
- [ ] Mid-phase validation checkpoints
- [ ] Update backlog based на findings

### 9.3 Post-Migration Tasks

- [ ] Post-mortem анализа migration
- [ ] Document lessons learned
- [ ] Plan future enhancements
- [ ] Celebrate successful migration! 🎉

---

## 10. Приложения

### 10.1 Feature Parity Checklist

См. отдельный документ `docs/architecture/FEATURE_PARITY.md` (который будет создан)

### 10.2 Performance Benchmarks

См. отдельный документ `docs/architecture/PERFORMANCE_BENCHMARKS.md` (который будет создан)

### 10.3 Test Coverage Report

Будет автоматически генерироваться и обновляться по мере написания тестов

---

**Документ версии:** 1.0
**Статус:** Draft
**Дата создания:** 2026-04-12
**Автор:** Implementation Engineer
**Reviewers:** (TBD)

---

## Summary

Этот документ предоставляет полный план миграции с Elixir на Python-first архитектуру для Symphony. План включает:

1. **Классификацию Elixir артефактов** - что нужно REUSE, REWRITE или DEPRECATE
2. **Анализ пробелов реализации** - что отсутствует в Python или новых архитектурных документах
3. **5 фаз миграции** - от core implementation до Elixir deprecation
4. **Приоритизированный бэклог** - 69 задач (19 P0, 30 P1, 20 P2)
5. **Оценку сроков** - 8-13 недель для полной миграции (4 недели для MVP)
6. **Риски и стратегию смягчения** - технические, операционные и расписания
7. **Success criteria** - measurable цели для каждой фазы
8. **Rollback plan** - быстрый возврат к Elixir при проблемах

Следующий шаг: Review plan с командой и начать реализацию Phase 1.
