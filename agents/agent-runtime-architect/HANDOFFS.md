# Agent Runtime Architect - Handoff Contracts

## To: platform-architect

### Контекст
Передача runtime требований для orchestrator scheduling, workspace management, и observability integration.

### Выходы от agent-runtime-architect

#### Runtime Requirements
- Session lifecycle states и transitions
- Subprocess launch parameters (command, cwd, stdio)
- Timeout policies (read_timeout_ms, turn_timeout_ms, stall_timeout_ms)
- Concurrency implications (per-agent resource usage)

#### Event Interface Contract
- Event emission requirements к orchestrator
- Token accounting формат
- Rate-limit tracking данные
- Structured event schemas

#### Error Interface Contract
- Error categories для orchestrator handling
- Retry/backoff рекомендации
- Stall detection сигналы
- Recovery triggers

### Ожидания от platform-architect

#### Scheduling Integration
- Dispatch eligibility checks (concurrency slots)
- Active run reconciliation logic
- Retry queue management

#### Observability Integration
- Logging контракты (session_id, issue_id, issue_identifier)
- Metrics/totals aggregation
- Snapshot interface requirements

#### Validation
- Предварительный validation runtime requirements
- Feedback о реализуемости протокола

---

## To: integration-architect

### Контекст
Передача деталей протокола для tracker integration (особенно linear_graphql tool extension) и observability integration.

### Выходы от agent-runtime-architect

#### Protocol Details
- Full Agent Runner Protocol specification
- Handshake sequence и payload shapes
- Event streaming контракт

#### linear_graphql Extension
- Tool purpose и availability conditions
- Input shape requirements (query, variables)
- Execution semantics (single operation per call)
- Result semantics (success/error responses)
- Auth requirements (reuse configured tracker auth)

#### Observability Contract
- Event types и schemas
- Token accounting правила
- Rate-limit формат
- Logging requirements

### Ожидания от integration-architect

#### Tracker Adapter
- Linear integration compatibility
- Query construction для linear_graphql tool
- Auth management для tool calls

#### Observability Adapter
- Event consumption contract
- Logging implementation
- Metrics aggregation

#### Validation
- Протестировать compatibility с Linear API
- Валидировать observability pipeline
- Feedback о missing integration requirements

---

## To: implementation-engineer

### Контекст
Передача полных спецификаций протокола для implementation.

### Выходы от agent-runtime-architect

#### Complete Protocol Specification
- Agent Runner Protocol (Section 10 из SPEC.md)
- Handshake transcript с примерами
- Message formats и ordering
- Session lifecycle state machine

#### Event Schemas
- Полный список event types
- Payload структуры для каждого типа
- Token accounting спецификация
- Rate-limit tracking формат

#### Error Handling
- Error category mapping
- Timeout policies
- Stall detection algorithm
- Retry/backoff formulas
- Error recovery strategies

#### Examples
- Complete transcript examples (success, error, continuation)
- Tool call examples (linear_graphql)
- Edge case scenarios

#### Implementation Notes
- Buffer requirements (stdout/stderr)
- Process launch details (bash -lc invocation)
- Workspace validation invariants
- Compatibility considerations

### Ожидания от implementation-engineer

#### Implementation
- Реализовать protocol-compliant agent runner
- Implement session lifecycle management
- Implement event streaming
- Implement error handling

#### Testing
- Unit tests для protocol compliance
- Integration tests с mock agents
- Edge case coverage
- Performance validation

#### Feedback
- Report blocking implementation issues
- Request clarification на неясных спецификациях
- Suggest protocol improvements

---

## To: verification-agent

### Контекст
Передача критериев валидации для проверки корректности реализации протокола.

### Выходы от agent-runtime-architect

#### Validation Criteria
- Protocol compliance checklist
- Session lifecycle verification steps
- Event streaming validation rules
- Timeout policy verification
- Error handling correctness checks

#### Test Scenarios
- Normal flow tests (startup, turn, continuation)
- Error scenario tests (timeout, crash, malformed)
- Edge case tests (rate limit, stall, cancellation)
- Tool call tests (linear_graphql extension)

#### Expected Behaviors
- Session state transitions
- Event emission ordering
- Token accounting correctness
- Error categorization accuracy
- Retry/backoff correctness

### Ожидания от verification-agent

#### Validation
- Verify protocol compliance
- Test all event types
- Validate error handling
- Verify timeout mechanisms
- Test edge cases

#### Reporting
- Дetailed test results
- Bug reports с reproducibility steps
- Coverage metrics
- Recommendations для fixes

---

## Handoff Protocol

### Передача информации
1. Собрать все спецификации в одном месте (ссылки или копии)
2. Создать summary с key points
3. Предоставить контакт для вопросов
4. Schedule review meeting если необходимо

### Post-handoff
1. Быть доступен для clarification
2. Обрабатывать feedback своевременно
3. Обновлять спецификации по необходимости
4. Документировать решения и trade-offs

### Критерии успеха
- Получатель понимает все спецификации
- Нет блокирующих вопросов
- Integration points ясны
- Implementation can proceed без delays
