# Agent Runtime Architect - Allowed Skills

## Protocol Design

### Описание
Разработка и спецификация протоколов взаимодействия между компонентами системы, особенно между orchestrator и coding agent.

### Применение
- Определение формата сообщений (JSON-RPC-like)
- Спецификация handshake sequences
- Определение message ordering
- Дизайн контрактов для bidirectional communication

### Связь с задачами
- Section 10.2: Session Startup Handshake
- Section 10.3: Streaming Turn Processing
- Section 10.4: Emitted Runtime Events

### Примеры использования
- Проектирование startup handshake (initialize → initialized → thread/start → turn/start)
- Определение continuation turn mechanics (reuse thread_id)
- Спецификация event emission contract

---

## System Architecture

### Описание
Проектирование архитектуры систем с четким разделением слоев и ответственностей.

### Применение
- Определение abstraction levels (Policy, Config, Coordination, Execution, Integration, Observability)
- Дизайн component boundaries
- Определение interface contracts
- Проектирование extensibility points

### Связь с задачами
- Section 3.2: Abstraction Levels
- Section 7: Orchestration State Machine
- Section 10.7: Agent Runner Contract

### Примеры использования
- Разделение orchestrator и agent runner responsibilities
- Определение workspace management как execution layer
- Дизайн integration layer для Linear adapter

---

## API Contract Design

### Описание
Разработка точных и полных контрактов API, включая message formats, schemas, и behavior semantics.

### Применение
- Определение message schemas (required/optional fields, types, defaults)
- Спецификация request/response patterns
- Дизайн error response formats
- Определение pre/post conditions

### Связь с задачами
- Section 10.1: Launch Contract
- Section 10.2: Session Startup Handshake
- Section 10.4: Emitted Runtime Events

### Примеры использования
- Спецификация initialize request params (clientInfo, capabilities)
- Определение event payload schemas (session_started, turn_completed)
- Дизайн token accounting interface

---

## Event Streaming Design

### Описание
Проектирование систем потоковой передачи событий с фокусом на reliability, ordering, и semantics.

### Применение
- Определение event types и их семантики
- Спецификация event ordering guarantees
- Дизайн event payload structures
- Определение event emission contracts

### Связь с задачами
- Section 10.4: Emitted Runtime Events (Upstream to Orchestrator)
- Section 13.5: Session Metrics and Token Accounting

### Примеры использования
- Определение event enumeration (session_started, turn_completed, turn_failed, ...)
- Спецификация token accounting в event payloads
- Дизайн rate-limit tracking через events

---

## Дополнительные навыки

### Error Handling Strategy
- Определение error categories
- Проектирование recovery strategies
- Спецификация retry/backoff logic

### Timeout Management
- Дизайн timeout policies (read, turn, stall timeouts)
- Определение timeout enforcement mechanisms
- Проектирование graceful degradation

### State Machine Design
- Определение session lifecycle states
- Спецификация state transitions
- Дизайн idempotency rules

### Documentation Standards
- Создание complete specifications
- Написание illustrative examples
- Документирование edge cases

## Ограничения

### Вне области ответственности
- ❌ Implementation кода (задача implementation-engineer)
- ❌ Business logic (задача workflow-architect)
- ❌ UI/dashboard дизайн (задача platform-architect)
- ❌ Sandbox/approval policies (implementation-defined)

### В области ответственности
- ✅ Protocol specification
- ✅ Interface definition
- ✅ Event contract design
- ✅ Error handling strategy
- ✅ Session lifecycle modeling
