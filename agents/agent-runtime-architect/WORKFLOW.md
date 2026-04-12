# Agent Runtime Architect - Workflow Process

## Шаг 1: Анализ требований к агенту

### Действия
1. Изучить SPEC.md Section 10 - Agent Runner Protocol
2. Проанализировать WORKFLOW.md шаблон для понимания prompt requirements
3. Изучить существующие integration constraints (workspace, tracker, observability)
4. Собрать требования от platform-architect (runtime requirements)
5. Собрать требования от integration-architect (protocol compatibility)

### Выходы
- Понимание роли orchestrator в agent lifecycle
- Требования к session management
- Констрейнты от platform и integration layers

---

## Шаг 2: Проектирование структуры протокола

### Действия
1. Определить формат сообщений (JSON-RPC-like line-delimited)
2. Специфицировать startup handshake sequence:
   - `initialize` request/response
   - `initialized` notification
   - `thread/start` request/response
   - `turn/start` request/response
3. Определить session identifiers (thread_id, turn_id, session_id)
4. Специфицировать continuation turn mechanics (reuse thread_id)
5. Определить payload shapes для compatibility

### Выходы
- Protocol message sequence diagram
- Complete handshake transcript с примерами
- Session identifier specification
- Payload compatibility notes

---

## Шаг 3: Определение жизненного цикла сессии

### Действия
1. Определить состояния сессии:
   - PreparingWorkspace
   - BuildingPrompt
   - LaunchingAgentProcess
   - InitializingSession
   - StreamingTurn
   - Finishing
   - Succeeded/Failed/TimedOut/Stalled/CanceledByReconciliation
2. Специфицировать transition triggers
3. Определить idempotency и recovery rules
4. Проектировать continuation retry mechanics
5. Определить termination conditions

### Выходы
- Session lifecycle state machine
- State transition table
- Recovery strategy document
- Retry/backoff formulas

---

## Шаг 4: Спецификация контрактов событий

### Действия
1. Определить все event types:
   - session_started, startup_failed
   - turn_completed, turn_failed, turn_cancelled, turn_ended_with_error
   - turn_input_required
   - approval_auto_approved
   - unsupported_tool_call
   - notification, other_message, malformed
2. Специфицировать event payload schemas
3. Определить token accounting правила (input/output/total tokens)
4. Определить rate-limit tracking формат
5. Специфицировать event ordering guarantees

### Выходы
- Complete event type enumeration
- Event payload schemas
- Token accounting specification
- Rate-limit tracking format
- Event ordering semantics

---

## Шаг 5: Проектирование обработки ошибок

### Действия
1. Определить error categories:
   - codex_not_found
   - invalid_workspace_cwd
   - response_timeout
   - turn_timeout
   - port_exit
   - response_error
   - turn_failed, turn_cancelled
   - turn_input_required
2. Специфицировать timeout policies:
   - read_timeout_ms (startup/sync requests)
   - turn_timeout_ms (total turn stream)
   - stall_timeout_ms (event inactivity)
3. Определить stall detection mechanism
4. Специфицировать error recovery strategies
5. Определить retry logic (exponential backoff)

### Выходы
- Error category mapping
- Timeout policy specification
- Stall detection algorithm
- Error recovery flowchart
- Retry/backoff formulas

---

## Шаг 6: Документирование с примерами

### Действия
1. Создать complete transcript примеры:
   - Successful session startup и turn completion
   - Error scenarios (timeout, crash, malformed message)
   - Continuation turn flow
   - Tool call execution (включая linear_graphql extension)
2. Документировать integration points:
   - To orchestrator (event emission)
   - To workspace manager (cwd validation)
   - To observability (logging, metrics)
3. Создать validation checklist
4. Составить implementation notes

### Выходы
- Complete transcript examples
- Integration point documentation
- Implementation-ready specifications
- Validation criteria

---

## Итеративный процесс

### Feedback Loop
1. Получить feedback от implementation-engineer
2. Получить feedback от integration-architect
3. Получить feedback от platform-architect
4. Обновить спецификации на основе feedback
5. Пересогласовать измененные контракты

### Рефакторинг
- Упрощение протокола без потери функциональности
- Добавление недостающих edge cases
- Уточнение формулировок
- Обновление примеров

---

## Контроль качества

### Перед передачей
- [ ] Протокол полностью задокументирован
- [ ] Session lifecycle ясен и полон
- [ ] Event schemas определены
- [ ] Error handling полный
- [ ] Примеры предоставлены
- [ ] Integration points ясны

### После передачи
- Собрать feedback от получателей
- Обновить спецификации по необходимости
- Документировать implementation notes
