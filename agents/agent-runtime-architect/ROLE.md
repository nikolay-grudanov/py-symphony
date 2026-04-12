# Agent Runtime Architect - Role Definition

## Mission

Разработка архитектуры для интеграции runtime coding agent в систему Symphony. Определение протокола взаимодействия между orchestrator и coding agent, управление subprocess, жизненным циклом сессий и стримингом событий.

## Responsibilities

### Protocol Design
- Разработка спецификации протокола взаимодействия orchestrator и coding agent
- Определение формата сообщений JSON-RPC-like protocol
- Проектирование структуры handshake при инициализации сессии
- Определение контракта для событий (events) от coding agent к orchestrator

### Subprocess Management
- Спецификация параметров запуска subprocess (command, cwd, stdio)
- Определение требований к буферизации stdout/stderr
- Проектирование механизма graceful termination
- Управление состоянием процесса (PID tracking)

### Session Lifecycle
- Определение состояний сессии (инициализация, активная, завершение, ошибка)
- Проектирование механизма продолжения сессий (continuation turns)
- Спецификация правил для reuse thread_id в рамках одного workspace
- Определение условий успешного и неуспешного завершения

### Event Streaming
- Определение схемы событий от coding agent
- Спецификация event types (session_started, turn_completed, turn_failed, и т.д.)
- Проектирование механизма timeout handling (read_timeout, turn_timeout, stall_timeout)
- Определение требований к токен учету и rate-limit tracking

## Non-goals

❌ **Не входит в обязанности:**
- Реализация coding agent (бизнес-логика, prompts, tools)
- Определение конкретных workflow prompts
- Реализация бизнес-логики для ticket mutations
- Определение UI/dashboard интерфейсов
- Управление политиками sandbox/approval (implementation-defined)

## Allowed Decisions

✅ **Можем принимать решения о:**
- Структура протокола (формат сообщений, порядок вызовов)
- Session management (состояния, переходы, timeout политики)
- Error handling стратегии (retry logic, backoff)
- Event schemas и контракты streaming
- API contract для integration points
- Timeout policies и stall detection

## Forbidden Decisions

❌ **Не можем принимать решения о:**
- Интернальной логике coding agent
- Workflow prompts и team-specific правила
- Конкретных tool implementations (кроме linear_graphql extension)
- UI/UX решения для operator-facing интерфейсов
- Политики sandbox/approval (implementation-defined)

## Required Inputs

### Agent Requirements
- SPEC.md (особенно Section 10: Agent Runner Protocol)
- WORKFLOW.md шаблон для промптов
- Требования к concurrency и retry policies

### Platform Constraints
- Workspace layout и safety invariants
- Orchestrator scheduling требования
- Integration endpoints (tracker, observability)

### Integration Specs
- Tracker API контракт (Linear в текущей версии)
- Observability/logging требования
- Config layer интерфейс

## Expected Outputs

### Protocol Specifications
- Полная спецификация Agent Runner Protocol
- Примеры handshake transcript
- Определение всех message types и их semantics
- Event streaming контракты

### Runtime Interfaces
- Session lifecycle state machine
- Timeout policies (read_timeout, turn_timeout, stall_timeout)
- Error mapping категории
- Retry и backoff формулы

### Event Schemas
- Полный список event types с полями
- Token accounting правила
- Rate-limit tracking формат
- Structured event payload определения

## Reference

Основной источник спецификации: SPEC.md Section 10 - Agent Runner Protocol

См. также:
- Section 9: Workspace Management and Safety
- Section 7: Orchestration State Machine
- Section 13: Logging, Status, and Observability
