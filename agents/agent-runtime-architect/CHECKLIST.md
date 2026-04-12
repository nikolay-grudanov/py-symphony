# Agent Runtime Architect - Completion Criteria

## Protocol Fully Specified

### Критерий
Полная спецификация Agent Runner Protocol с четкими определениями всех аспектов.

### Проверка
- [ ] Определен формат сообщений (JSON-RPC-like line-delimited)
- [ ] Специфицирован startup handshake sequence (initialize → initialized → thread/start → turn/start)
- [ ] Определены session identifiers (thread_id, turn_id, session_id)
- [ ] Специфицированы continuation turn mechanics
- [ ] Определены payload compatibility notes
- [ ] Предоставлены complete transcript examples

---

## Session Lifecycle Documented

### Критерий
Полная документация жизненного цикла сессии с состояниями, переходами и recovery strategies.

### Проверка
- [ ] Определены все состояния сессии (PreparingWorkspace → Finishing → Succeeded/Failed/TimedOut/Stalled/CanceledByReconciliation)
- [ ] Специфицированы state transitions
- [ ] Определены transition triggers (Poll Tick, Worker Exit, Codex Update Event, Retry Timer Fired, Reconciliation, Stall Timeout)
- [ ] Документированы idempotency rules
- [ ] Определены recovery strategies
- [ ] Специфицированы continuation retry mechanics
- [ ] Предоставлена state machine diagram или table

---

## Event Schemas Defined

### Критерий
Полные определения всех event types с payload schemas и semantics.

### Проверка
- [ ] Определены все event types (session_started, startup_failed, turn_completed, turn_failed, turn_cancelled, turn_ended_with_error, turn_input_required, approval_auto_approved, unsupported_tool_call, notification, other_message, malformed)
- [ ] Специфицированы payload schemas для каждого event type
- [ ] Определены required и optional поля
- [ ] Специфицированы event ordering guarantees
- [ ] Документированы token accounting правила (input/output/total tokens)
- [ ] Определен rate-limit tracking формат
- [ ] Предоставлены примеры event payloads

---

## Error Handling Complete

### Критерий
Полная спецификация обработки ошибок с категориями, timeout policies и recovery strategies.

### Проверка
- [ ] Определены error categories (codex_not_found, invalid_workspace_cwd, response_timeout, turn_timeout, port_exit, response_error, turn_failed, turn_cancelled, turn_input_required)
- [ ] Специфицированы timeout policies:
  - [ ] read_timeout_ms (startup/sync requests)
  - [ ] turn_timeout_ms (total turn stream)
  - [ ] stall_timeout_ms (event inactivity)
- [ ] Определен stall detection mechanism (elapsed_ms calculation)
- [ ] Специфицированы error recovery strategies для каждой категории
- [ ] Определены retry/backoff формулы:
  - [ ] Continuation retry: 1000ms fixed delay
  - [ ] Failure retry: min(10000 * 2^(attempt-1), max_retry_backoff_ms)
- [ ] Документированы error handling flowcharts

---

## Examples Provided

### Критерий
Полные и понятные примеры для всех основных сценариев и edge cases.

### Проверка
- [ ] Полный transcript успешного session startup и turn completion
- [ ] Пример continuation turn flow
- [ ] Пример tool call execution (включая linear_graphql extension)
- [ ] Пример error scenarios:
  - [ ] Timeout scenarios (read_timeout, turn_timeout, stall_timeout)
  - [ ] Subprocess crash/abnormal exit
  - [ ] Malformed JSON messages
  - [ ] Unsupported tool calls
  - [ ] User input required scenarios
  - [ ] Rate limit exceeded
- [ ] Примеры payload shapes для compatibility notes
- [ ] Примеры event emission для всех event types

---

## Integration Points Clear

### Критерий
Четкие определения всех точек интеграции с другими компонентами системы.

### Проверка
- [ ] Определен interface к orchestrator (event emission, callback registration)
- [ ] Определен interface к workspace manager (cwd validation, workspace preparation)
- [ ] Определен interface к observability layer (logging, metrics, snapshots)
- [ ] Специфицирован linear_graphql tool extension contract
- [ ] Определены integration requirements:
  - [ ] Tracker adapter (Linear integration)
  - [ ] Config layer (workflow config resolution)
  - [ ] Logging infrastructure (structured logging)
- [ ] Документированы handoff контракты для всех потребителей:
  - [ ] platform-architect (runtime requirements)
  - [ ] integration-architect (protocol details)
  - [ ] implementation-engineer (protocol specs)
  - [ ] verification-agent (validation criteria)

---

## Дополнительные критерии

### Documentation Quality
- [ ] Все спецификации на русском с English техническими терминами
- [ ] Структурированный формат (markdown с заголовками)
- [ ] Cross-references между связанными разделами
- [ ] Понятные и краткие определения
- [ ] Отсутствие двусмысленностей

### Completeness
- [ ] Все аспекты протокола задокументированы
- [ ] Нет пропущенных edge cases
- [ ] Все состояния и переходы определены
- [ ] Все event types документированы
- [ ] Все error categories охвачены

### Implementability
- [ ] Спецификации достаточны для implementation
- [ ] Нет противоречий между разделами
- [ ] Примеры соответствуют спецификациям
- [ ] Integration points реализуемы

---

## Итоговый Checklist

Перед передачей результатов:

- [ ] **Protocol**: Полностью специфицирован
- [ ] **Session Lifecycle**: Полностью документирован
- [ ] **Event Schemas**: Полностью определены
- [ ] **Error Handling**: Полностью спроектирован
- [ ] **Examples**: Полностью предоставлены
- [ ] **Integration Points**: Полностью ясны
- [ ] **Documentation**: Высокого качества
- [ ] **Completeness**: Без пропусков
- [ ] **Implementability**: Готов к реализации
- [ ] **Handoffs**: Готовы для передачи всем получателям

При выполнении всех критериев работа считается завершенной и готовой к передаче.
