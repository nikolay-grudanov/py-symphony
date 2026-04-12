# Контракты передачи: Platform Architect

## Общий принцип

Агент platform-architect передает работу другим агентам через четкие, явные контракты. Каждый контракт определяет:

1. **Что передается**: конкретные артефакты и их содержание
2. **В каком формате**: форма представления артефактов
3. **Когда**: условия и критерии готовности передачи
4. **Что ожидается в ответ**: ожидаемые результаты от принимающего агента

---

## Контракт с implementation-engineer

### Что передается

#### Спецификации компонентов

**Workflow Loader**
- Описание ответственности: чтение и парсинг WORKFLOW.md
- Интерфейс: методы для загрузки и парсинга
- Входные данные: путь к файлу WORKFLOW.md
- Выходные данные: `{config, prompt_template}`
- Ошибки: `missing_workflow_file`, `workflow_parse_error`, `workflow_front_matter_not_a_map`

**Config Layer**
- Описание ответственности: экспозиция типизированных getters для конфигурации
- Интерфейс: методы для получения конфигурационных значений
- Входные данные: parsed YAML front matter
- Выходные данные: типизированные конфигурационные значения
- Логика: применение defaults, resolution of environment variables, validation

**Issue Tracker Client**
- Описание ответственности: взаимодействие с Issue Tracker API (Linear)
- Интерфейс: методы для фетчинга issues, состояний
- Входные данные: project slug, state filters
- Выходные данные: normalized issue records
- Контракт: нормализация полей issue в стандартную модель

**Orchestrator**
- Описание ответственности: управление жизненным циклом агент-сессий
- Интерфейс: методы для dispatch, retry, stop, release
- Состояние: in-memory runtime state
- Поведение: polling loop, reconciliation, concurrency control

**Workspace Manager**
- Описание ответственности: управление workspace lifecycle
- Интерфейс: методы для создания, подготовки, очистки workspace
- Входные данные: issue identifier
- Выходные данные: workspace path
- Безопасность: проверка, что workspace path находится внутри workspace root

**Agent Runner**
- Описание ответственности: запуск и управление coding agent subprocess
- Интерфейс: методы для создания workspace, построения prompt, запуска агента
- Протокол: JSON-RPC-like app-server mode over stdio
- Контракт: startup handshake, streaming turn processing, event emission

**Status Surface (optional)**
- Описание ответственности: представление human-readable runtime status
- Интерфейс: методы для получения snapshot текущего состояния
- Выходные данные: running sessions, retry queue, aggregates

**Logging**
- Описание ответственности: эмиссия structured runtime logs
- Интерфейс: методы для логирования с контекстом
- Формат: structured logs с обязательными полями

#### API контракты между компонентами

**Методы интерфейсов**
- Сигнатуры методов с типами параметров и возвращаемых значений
- Описание поведения каждого метода
- Обработка ошибок для каждого метода

**Форматы данных**
- Структуры данных для обмена между компонентами
- Форматы JSON/YAML для конфигураций
- Схемы данных для normalized issue records

**Асинхронные контракты**
- Контракты для асинхронных операций
- Callbacks и event handling
- Timeout behavior

#### Контракты интеграции с внешними системами

**Linear Integration**
- API endpoints: `https://api.linear.app/graphql`
- Auth: `Authorization` header с API key
- Operations: `fetch_candidate_issues()`, `fetch_issues_by_states()`, `fetch_issue_states_by_ids()`
- Pagination: required, default page size 50
- Network timeout: 30000 ms
- Error handling: categories для разных типов ошибок

**Codex App-Server Integration**
- Command: `codex app-server` (или custom из config)
- Protocol: line-delimited JSON over stdio
- Startup sequence: `initialize` -> `initialized` -> `thread/start` -> `turn/start`
- Turn processing: streaming до `turn/completed`/`turn/failed`/`turn/cancelled`
- Events: `session_started`, `turn_completed`, `turn_failed`, `turn_input_required`, etc.
- Timeouts: `read_timeout_ms` (default 5000), `turn_timeout_ms` (default 3600000)

#### Технологический стек

**Языки и фреймворки**
- Выбранные языки программирования для каждого компонента
- Фреймворки и библиотеки для реализации
- Обоснование выбора технологий

**Инфраструктура**
- Требования к развертыванию
- Сетевые конфигурации
- Стратегии безопасности инфраструктуры

### В каком формате

- **Спецификации компонентов**: Markdown файлы с четкой структурой (Responsibility, Interface, Input, Output, Behavior)
- **UML диаграммы**: Component diagrams, Sequence diagrams для критических сценариев
- **API контракты**: OpenAPI/Swagger спецификации или Markdown с примерами
- **Контракты интеграции**: Markdown с примерами запросов/ответов и GraphQL схемами
- **Технологический стек**: Markdown файл с перечнем технологий и обоснованием

### Когда передается

- Когда все спецификации компонентов завершены и рассмотрены
- Когда все API контракты определены и согласованы
- Когда все контракты интеграции определены и протестируемы
- Когда технологический стек выбран и обоснован

### Что ожидается в ответ

- Реализация компонентов в соответствии со спецификациями
- Тесты, которые проверяют соответствие спецификациям
- Отчет о реализации и выявленных проблемах
- Запросы на уточнение спецификаций при необходимости

---

## Контракт с workflow-architect

### Что передается

#### Требования к процессам Workflow Loader

**Процесс загрузки WORKFLOW.md**
- Path discovery: precedence правил (explicit application setting -> cwd default)
- File reading: обработка ошибок при невозможности чтения
- Parsing: YAML front matter + Markdown body separation
- Validation: проверка на map/object для YAML, не-empty для prompt

**Процесс парсинга WORKFLOW.md**
- YAML front matter parsing: обработка `---` delimiters
- Prompt body extraction: trim whitespace
- Error handling: `workflow_parse_error`, `workflow_front_matter_not_a_map`

#### Требования к WORKFLOW.md контракту

**Формат файла**
- Markdown с optional YAML front matter
- Front matter fields: `tracker`, `polling`, `workspace`, `hooks`, `agent`, `codex`
- Prompt template: Markdown body после front matter

**Dynamic Reload Semantics**
- Watch `WORKFLOW.md` for changes
- Re-read and re-apply config без restart
- Live rebind для polling interval, concurrency limits, agent settings
- Extensions (например `server.port`) могут требовать restart

**Front Matter Schema**
- `tracker.kind`: string (required, currently `linear`)
- `tracker.endpoint`: string (default `https://api.linear.app/graphql`)
- `tracker.api_key`: string or `$VAR` (canonical env `LINEAR_API_KEY`)
- `tracker.project_slug`: string (required for linear)
- `tracker.active_states`: list of strings (default `["Todo", "In Progress"]`)
- `tracker.terminal_states`: list of strings (default terminal states)
- `polling.interval_ms`: integer (default 30000)
- `workspace.root`: path (default `<system-temp>/symphony_workspaces`)
- `hooks.after_create`, `hooks.before_run`, `hooks.after_run`, `hooks.before_remove`: shell scripts
- `hooks.timeout_ms`: integer (default 60000)
- `agent.max_concurrent_agents`: integer (default 10)
- `agent.max_retry_backoff_ms`: integer (default 300000)
- `agent.max_concurrent_agents_by_state`: map (default empty)
- `codex.command`: string (default `codex app-server`)
- `codex.approval_policy`, `codex.thread_sandbox`, `codex.turn_sandbox_policy`: pass-through values
- `codex.turn_timeout_ms`: integer (default 3600000)
- `codex.read_timeout_ms`: integer (default 5000)
- `codex.stall_timeout_ms`: integer (default 300000)

#### Архитектурные ограничения на процессы

**Policy Layer Constraints**
- WORKFLOW.md должен быть repository-owned и version-controlled
- Team-specific rules должны быть defined в prompt body, не в code
- Front matter должен быть extensible for extensions

**Configuration Layer Constraints**
- Typed getters должны применять defaults и env resolution
- Validation должно выполняться перед dispatch
- Invalid reloads должны fail gracefully без crash

**Coordination Layer Constraints**
- Orchestrator должен быть single source of truth для state
- State mutations должны быть serialized через one authority
- Reconciliation должен выполняться на каждом tick

#### Контракты для взаимодействия процессов с компонентами

**Workflow Loader -> Config Layer**
- Input: parsed YAML front matter
- Output: typed getters with defaults/env resolution applied
- Contract: validation before dispatch, dynamic reload on file changes

**Config Layer -> Orchestrator**
- Input: typed config values
- Output: runtime settings (poll interval, concurrency limits, etc.)
- Contract: config must be validated before use, dynamic reapply on changes

**Workflow Loader -> Agent Runner**
- Input: prompt template, issue object, attempt number
- Output: rendered prompt for agent
- Contract: strict template engine, unknown variables must fail rendering

### В каком формате

- **Требования к процессам**: Markdown файлы с описанием процессов и их поведения
- **WORKFLOW.md контракты**: Markdown или YAML файлы со схемами front matter
- **Архитектурные ограничения**: Markdown файлы с явными ограничениями и их обоснованием
- **Контракты взаимодействия**: Markdown или Sequence diagrams с описанием потоков данных

### Когда передается

- Когда требования к процессам ясны и полны
- Когда WORKFLOW.md контракт полностью определен
- Когда архитектурные ограничения идентифицированы
- Когда контракты взаимодействия процессируемы

### Что ожидается в ответ

- Процессы, которые соответствуют требованиям
- WORKFLOW.md шаблоны и примеры
- Реализация процессов с учетом ограничений
- Отчет о реализации и выявленных проблемах

---

## Контракт с integration-architect

### Что передается

#### Контракты интеграции для Issue Tracker Client (Linear)

**Operations Required**
- `fetch_candidate_issues()`: возвращает issues в active states для configured project
- `fetch_issues_by_states(state_names)`: используется для startup terminal cleanup
- `fetch_issue_states_by_ids(issue_ids)`: используется для active-run reconciliation

**Query Semantics**
- `tracker.kind == "linear"`
- GraphQL endpoint: `https://api.linear.app/graphql`
- Auth: token в `Authorization` header
- `tracker.project_slug` maps to Linear project `slugId`
- Candidate query: фильтр по `project: { slugId: { eq: $projectSlug } }`
- State refresh query: использует GraphQL issue IDs
- Pagination: required, default page size 50
- Network timeout: 30000 ms

**Normalization Rules**
- `labels`: lowercase strings
- `blocked_by`: derived из inverse relations (type `blocks`)
- `priority`: integer only (non-integers become null)
- `created_at`, `updated_at`: parse ISO-8601 timestamps
- `state`: compare после `lowercase`

**Error Categories**
- `unsupported_tracker_kind`
- `missing_tracker_api_key`
- `missing_tracker_project_slug`
- `linear_api_request` (transport failures)
- `linear_api_status` (non-200 HTTP)
- `linear_graphql_errors`
- `linear_unknown_payload`
- `linear_missing_end_cursor` (pagination integrity)

**Orchestrator Behavior on Errors**
- Candidate fetch failure: log and skip dispatch
- State refresh failure: log and keep workers running
- Startup cleanup failure: log warning and continue

#### Контракты интеграции для Agent Runner (Codex app-server)

**Launch Contract**
- Command: `codex.command`
- Invocation: `bash -lc <codex.command>`
- Working directory: workspace path
- Stdout/stderr: separate streams
- Framing: line-delimited JSON on stdout (JSON-RPC-like)
- Max line size: 10 MB (recommended)

**Startup Handshake Sequence**
1. `initialize` request с `clientInfo` и `capabilities`
2. `initialized` notification
3. `thread/start` request с `approvalPolicy`, `sandbox`, `cwd`
4. `turn/start` request с `threadId`, `input`, `cwd`, `title`, `approvalPolicy`, `sandboxPolicy`

**Session Identifiers**
- `thread_id`: из `thread/start` result `result.thread.id`
- `turn_id`: из `turn/start` result `result.turn.id`
- `session_id`: `<thread_id>-<turn_id>`

**Streaming Turn Processing**
- Read messages до termination: `turn/completed` (success), `turn/failed`, `turn/cancelled`, timeout, subprocess exit
- Continuation: повторный `turn/start` на том же `threadId`
- Line handling: JSON parse на complete stdout lines, stderr игнорируется

**Emitted Events**
- `session_started`, `startup_failed`
- `turn_completed`, `turn_failed`, `turn_cancelled`, `turn_ended_with_error`
- `turn_input_required`, `approval_auto_approved`
- `unsupported_tool_call`, `notification`, `other_message`, `malformed`

**Approval and Tool Call Policy**
- Approval, sandbox, user-input behavior: implementation-defined
- `linear_graphql` extension: optional client-side tool for Linear GraphQL
- Unsupported tool calls: return failure and continue session

**Timeouts**
- `read_timeout_ms`: request/response timeout (default 5000)
- `turn_timeout_ms`: total turn stream timeout (default 3600000)
- `stall_timeout_ms`: orchestrator-based stall detection (default 300000)

#### Архитектурные ограничения на интеграции

**Orchestrator Boundary**
- Symphony является scheduler/runner и tracker reader
- Ticket writes (state transitions, comments, PR links) выполняются coding agent через tools
- Workflow success может заканчиваться в handoff state (например `Human Review`), не обязательно `Done`

**Safety Invariants**
- Invariant 1: Run coding agent только в per-issue workspace path
- Invariant 2: Workspace path должен быть внутри workspace root
- Invariant 3: Workspace key sanitized (только `[A-Za-z0-9._-]`)

#### Требования к безопасности интеграций

**Authentication**
- Linear: `Authorization` header с API key из config или env variable
- Codex: host environment authentication

**Authorization**
- Linear: project-based access control
- Codex: approval policy defined in workflow config

**Security**
- Validate workspace paths are inside workspace root
- Validate inputs to external APIs
- Sanitize user inputs in GraphQL queries
- Error messages must not expose sensitive data

### В каком формате

- **Контракты интеграции**: Markdown файлы с описанием операций, семантики, правил нормализации
- **API контракты**: OpenAPI/Swagger или Markdown с примерами запросов/ответов
- **GraphQL схемы**: GraphQL SDL или Markdown с примерами queries/mutations
- **Контракты протоколов**: Markdown с последовательностями сообщений и примерами

### Когда передается

- Когда все контракты интеграции полностью определены
- Когда протоколы взаимодействия специфицированы
- Когда архитектурные ограничения идентифицированы
- Когда требования к безопасности определены

### Что ожидается в ответ

- Реализация интеграций в соответствии с контрактами
- Тесты, которые проверяют соответствие контрактам
- Отчет о реализации и выявленных проблемах
- Запросы на уточнение контрактов при необходимости

---

## Контракт с verification-agent

### Что передается

#### Критерии валидации архитектуры

**Соответствие требованиям**
- Все функциональные требования удовлетворены
- Все нефункциональные требования (производительность, надежность, безопасность) удовлетворены
- Все ограничения (бюджет, время, команда) учтены

**Согласованность архитектуры**
- Все компоненты согласованы друг с другом
- Все слои архитектуры (Policy, Configuration, Coordination, Execution, Integration, Observability) четко разделены
- Нет противоречий между архитектурными решениями

**Реализуемость архитектуры**
- Архитектура реализуема в рамках выбранных технологий
- Архитектура реализуема в рамках доступных ресурсов
- Архитектура реализуема в рамках ограничений команды

**Соответствие SPEC.md**
- Все основные компоненты из SPEC.md присутствуют
- Все абстрактные уровни из SPEC.md соблюдены
- Все внешние зависимости из SPEC.md учтены

#### Контракты для проверки реализаций

**Проверка спецификаций компонентов**
- Реализация соответствует спецификации компонента
- Интерфейс компонента соответствует спецификации
- Поведение компонента соответствует спецификации

**Проверка API контрактов**
- Реализация API соответствует контракту
- Форматы данных соответствуют контракту
- Обработка ошибок соответствует контракту

**Проверка контрактов интеграции**
- Реализация интеграции соответствует контракту
- Протоколы взаимодействия соблюдены
- Обработка ошибок соответствует контракту

#### Метрики для оценки качества архитектуры

**Масштабируемость**
- Количество concurrent agents поддерживаемых архитектурой
- Частота polling, поддерживаемая архитектурой
- Размер workspace, поддерживаемый архитектурой

**Производительность**
- Latency dispatch operations
- Throughput agent sessions
- Latency integration operations

**Надежность**
- Uptime сервиса
- MTBF (Mean Time Between Failures)
- MTTR (Mean Time To Recovery)
- Rate of successful agent completions

**Безопасность**
- Наличие аутентификации и авторизации
- Защита от common vulnerabilities (injection, XSS, CSRF)
- Шифрование данных в transit и at rest
- Audit trails для критических операций

**Поддерживаемость**
- Число компонентов и их сложность
- Четкость разделения ответственности
- Качество документации

#### Критерии приемки для компонентов

**Workflow Loader**
- SUCCESS: Loads and parses valid WORKFLOW.md files
- SUCCESS: Returns `{config, prompt_template}` with correct structure
- SUCCESS: Handles errors with appropriate error categories
- FAIL: Cannot read WORKFLOW.md file
- FAIL: Cannot parse YAML front matter
- FAIL: Front matter is not a map

**Config Layer**
- SUCCESS: Provides typed getters for all config fields
- SUCCESS: Applies defaults correctly
- SUCCESS: Resolves environment variables correctly
- SUCCESS: Validates config before dispatch
- FAIL: Missing required fields
- FAIL: Invalid field types
- FAIL: Env variable resolution fails

**Issue Tracker Client**
- SUCCESS: Fetches candidate issues correctly
- SUCCESS: Normalizes issue records according to spec
- SUCCESS: Handles pagination correctly
- SUCCESS: Returns appropriate error categories
- FAIL: Cannot connect to tracker API
- FAIL: Authentication fails
- FAIL: Invalid query syntax

**Orchestrator**
- SUCCESS: Dispatches issues according to eligibility rules
- SUCCESS: Manages concurrency limits correctly
- SUCCESS: Reconciles running issues on each tick
- SUCCESS: Handles retries with backoff correctly
- FAIL: Concurrency limit exceeded
- FAIL: State mutation not serialized
- FAIL: Reconciliation logic incorrect

**Workspace Manager**
- SUCCESS: Creates workspaces correctly
- SUCCESS: Ensures workspace path is inside workspace root
- SUCCESS: Sanitizes workspace key correctly
- SUCCESS: Executes hooks with correct semantics
- FAIL: Workspace path outside workspace root
- FAIL: Workspace key not sanitized
- FAIL: Hook timeout behavior incorrect

**Agent Runner**
- SUCCESS: Launches agent subprocess correctly
- SUCCESS: Performs startup handshake correctly
- SUCCESS: Streams turn processing correctly
- SUCCESS: Emits events correctly
- FAIL: Cannot launch agent subprocess
- FAIL: Startup handshake fails
- FAIL: Turn processing timeout
- FAIL: Protocol violation

### В каком формате

- **Критерии валидации**: Markdown файлы с критериями и их описанием
- **Чек-листы**: Markdown файлы с чек-листами для проверки
- **Метрики**: Markdown файлы с определениями метрик и их единицами измерения
- **Критерии приемки**: Markdown файлы с SUCCESS/FAIL критериями для каждого компонента

### Когда передается

- Когда все критерии валидации определены
- Когда все контракты для проверки созданы
- Когда все метрики определены
- Когда все критерии приемки созданы

### Что ожидается в ответ

- Отчет о валидации архитектуры с результатами
- Отчет о проверке реализаций с результатами
- Результаты измерения метрик
- Результаты приемочного тестирования компонентов
- Запросы на уточнение критериев при необходимости
