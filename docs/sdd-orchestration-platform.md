# Software Design Document: Orchestration Platform

**Версия:** 1.0.0  
**Дата:** 2026-04-11  
**Статус:** Draft  
**Автор:** Build Team  

---

## Содержание

1. [System Purpose](#1-system-purpose--назначение-системы)
2. [Goals](#2-goals--цели-системы)
3. [Non-Goals](#3-non-goals--что-не-входит-в-scope)
4. [Actors and Roles](#4-actors-and-roles--участники-и-их-роли)
5. [System Context](#5-system-context--контекст-системы)
6. [Key Workflows](#6-key-workflows--ключевые-workflows)
7. [Component Architecture](#7-component-architecture--архитектура-компонентов)
8. [Domain Model](#8-domain-model--доменная-модель)
9. [State Model](#9-state-model--модель-состояний)
10. [Integration Boundaries](#10-integration-boundaries--границы-интеграции)
11. [Jira Interaction Model](#11-jira-interaction-model--модель-взаимодействия-с-jira)
12. [Git / CI Interaction Model](#12-git--ci-interaction-model--модель-взаимодействия-с-gitci)
13. [Agent Runtime Model](#13-agent-runtime-model--модель-runtime-агентов)
14. [Skill Loading Model](#14-skill-loading-model--модель-загрузки-skills)
15. [Artifact Model](#15-artifact-model--модель-артефактов)
16. [Handoff Model](#16-handoff-model--модель-handoff)
17. [Retry / Failure Handling](#17-retry--failure-handling--обработка-ошибок-и-retries)
18. [Approval Gates](#18-approval-gates--шлюзы-одобрения)
19. [Observability and Audit](#19-observability-and-audit--observability-и-аудит)
20. [Security Model](#20-security-model--модель-безопасности)
21. [Configuration Model](#21-configuration-model--модель-конфигурации)
22. [Deployment Model](#22-deployment-model--модель-деплоя)
23. [Extensibility Model](#23-extensibility-model--модель-расширяемости)
24. [Risks and Tradeoffs](#24-risks-and-tradeoffs--риски-и-компромиссы)

---

## 1. System Purpose — Назначение системы

### 1.1 Общее описание

Orchestration Platform — это **централизованная система координации агентов** в рамках SDLC (Software Development Life Cycle), которая обеспечивает:

- **Управление workflow** между стадиями разработки (BA → SA → Dev → QA)
- **Контроль состояний** задач и артефактов на каждой стадии
- **Handoff процессы** между агентами с гарантией доставки и обработки
- **Интеграцию** с внешними системами (Jira, Git, CI/CD, MCP tools)
- **Наблюдаемость** и аудит всех операций

### 1.2 Проблема, которую решает система

Текущие проблемы вручную координируемого SDLC:

| Проблема | Влияние | Решение от Orchestration Platform |
|----------|---------|-----------------------------------|
| Потеря контекста при handoff между агентами | Ошибки, задержки | Гарантированная доставка с подтверждением |
| Отсутствие единого source of truth | Конфликты данных | Jira как business state, orchestration engine для runtime state |
| Ручной контроль статусов | Непро��рачность процессов | Автоматическое отслеживание состояний и переходов |
| Нет централизованного мониторинга | Медленное обнаружение проблем | Единая observability платформа |

### 1.3 Сравнение с аналогами

| Характеристика | Традиционный подход | Orchestration Platform |
|----------------|---------------------|----------------------|
| Handoff | Ручной / чат | Автоматизированный с подтверждением |
| State tracking | Распределён в разных системах | Единая модель состояний |
| Retry логика | Вручную | Политики retry с backoff |
| Audit |fragmented logs | Централизованный аудит |
| Extensibility | Ограниченная | Модульная архитектура |

---

## 2. Goals — Цели системы

### 2.1 Ключевые цели

| # | Цель | Метрика измерения | Целевое значение |
|---|------|-------------------|-------------------|
| 1 | **Automation rate** — автоматизация переходов между стадиями | % автоматических handoff от общего числа | ≥ 95% |
| 2 | **Handoff reliability** — надёжность передачи контекста | Успешных handoff без потери данных | ≥ 99.9% |
| 3 | **Visibility** — прозрачность процессов | Время обнаружения проблемы | ≤ 5 минут |
| 4 | **Recovery time** — время восстановления при ошибках | MTTR (Mean Time To Recovery) | ≤ 15 минут |
| 5 | **Extensibility** — расширяемость платформы | Время добавления нового агента/стадии | ≤ 1 день |

### 2.2 Цели по качеству

- **Reliability**: 99.9% uptime orchestration engine
- **Latency**: Время отклика на handoff запрос ≤ 2 секунды
- **Scalability**: Поддержка ≥ 100 параллельных workflow
- **Auditability**: Полный аудит всех операций с retention 1 год

### 2.3 Business Goals

- Сокращение time-to-market за счёт автоматизации рутинных операций
- Повышение качества code review за счёт стандартизированных approval gates
- Улучшение traceability от business requirement до deployed artifact

---

## 3. Non-Goals — Что не входит в Scope

### 3.1 Явные ограничения

| Non-Goal | Причина |
|----------|---------|
| **Управление кодом агентов** | Агенты — внешние сущности, платформа только координирует их работу |
| **Выполнение задач агентов** | Агенты самостоятельно выполняют свою работу, платформа не вмешивается в их логику |
| **Аутентификация пользователей** | Делегируется внешним системам (Jira, GitHub) |
| **Хранение артефактов** | Платформа не хранит артефакты, только ссылается на них |
| **Планирование ресурсов агентов** | Каждый агент управляет своими ресурсами независимо |
| **Прямое выполнение CI/CD** | Делегируется внешним CI системам |

### 3.2 Out of Scope для v1.0

- Multitenancy (несколько организаций)
- Advanced analytics и predictive models
- Visual workflow editor
- Mobile UI
- Real-time collaboration

---

## 4. Actors and Roles — Участники и их роли

### 4.1 Акторы системы

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ACTORS DIAGRAM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐         ┌─────────────┐         ┌───────────────────┐       │
│   │  User   │────────▶│  Orchestration │◀──────│  Agent (Build)   │       │
│   │         │         │    Platform    │        │                  │       │
│   └─────────┘         └───────┬───────┘         └───────────────────┘       │
│                                │                                               │
│                                │                                               │
│   ┌─────────┐         ┌───────▼───────┐         ┌───────────────────┐       │
│   │  Jira   │◀───────▶│              │◀───────▶│  External Tools  │       │
│   │ System │         │              │         │  (MCP, CI, etc.)   │       │
│   └────────┘         └─────────────┘         └───────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Типы акторов

#### 4.2.1 Человеческие акторы

| Actor | Роль | Полномочия |
|-------|------|----------|
| **Platform Admin** | Настройка и управление платформой | Полный доступ к конфигурации |
| **Project Manager** | Управление workflow на уровне проекта | Запуск/остановка workflow, просмотр статусов |
| **Developer** | Исполнение задач на стадии Dev | Работа с задачами в своей очереди |
| **QA Engineer** | Исполнение задач на стадии QA | Работа с задачами в очереди QA |
| **Reviewer** | Оценирование и утверждение артефактов | Approval / rejection decisions |

#### 4.2.2 Агентные акторы (Build Agents)

| Agent | Role Description | Стадия SDLC |
|-------|------------------|-------------|
| **Build Orchestrator** | Координация разработки, управление overall workflow | Cross-cutting |
| **Platform Architect** | Архитектура платформы, проектирование компонентов | Planning |
| **Workflow Architect** | Проектирование workflows и state machines | Planning |
| **Agent Runtime Architect** | Runtime агентов, execution model | Implementation |
| **Integration Architect** | Интеграции (Jira, Git, CI, MCP) | Implementation |
| **Implementation Engineer** | Реализация компонентов | Implementation |
| **Verification Agent** | Проверка корректности реализации | Verification |
| **Test Engineer** | Тестирование компонентов | Testing |

#### 4.2.3 Системные акторы

| Actor | Роль | Описание |
|-------|------|----------|
| **Jira System** | Source of truth для business state | Управление задачами |
| **Git Repository** | Хранение исходного кода | Контроль версий |
| **CI System** | Сборка и тестирование | Выполнение pipeline |
| **MCP Tools** | External tools integration | Model Context Protocol |
| **Audit Log** | Хранение аудита | Immutable audit trail |

### 4.3 Mapping Build Agents на компоненты SDD

| Build Agent | Компонент SDD | Ответственность |
|-------------|---------------|-----------------|
| Build Orchestrator | Orchestration Engine | Overall coordination |
| Platform Architect | Component Architecture | System design |
| Workflow Architect | State Model, Key Workflows | Workflow design |
| Agent Runtime Architect | Agent Runtime Model | Agent execution |
| Integration Architect | Integration Boundaries | External integrations |
| Implementation Engineer | Implementation specifics | Code implementation |
| Verification Agent | Observability, Approval Gates | Quality assurance |
| Test Engineer | Retry / Failure Handling | Test design |

---

## 5. System Context — Контекст системы

### 5.1 Диаграмма контекста (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        ORCHESTRATION PLATFORM                               │
│                          [System Boundary]                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │   ┌───────────────┐    ┌────────────────────────┐                   │   │
│  │   │  Orchestration │    │    Agent Coordinator   │                   │   │
│  │   │    Engine     │◀──▶│                        │                   │   │
│  │   │               │    └───────────┬────────────┘                   │   │
│  │   │  ┌─────────┐  │                │                                │   │
│  │   │  │ State   │──▶│    ┌───────────▼──────────┐                   │   │
│  │   │  │ Store   │◀──│    │   Workflow Engine   │                    │   │
│  │   │  └─────────┘  │    │                      │                    │   │
│  │   │               │    └──────────────────────┘                   │   │
│  │   └───────────────┘                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│    ▼ External Systems                              ▲ External Systems    │
│    ┌─────────────┐    ───────────────────────▶    ┌─────────────┐      │
│    │   Jira      │                                  │  MCP Tools  │      │
│    │   System    │◀─ Business State & Status       │             │      │
│    └─────────────┘                                   └─────────────┘      │
│                                                                             │
│    ▼ External Systems                              ▲ External Systems    │
│    ┌─────────────┐    ───────────────────────▶    ┌─────────────┐      │
│    │     Git     │    ── Code & Artifact refs ──▶ │    CI/CD    │      │
│    │ Repository │                                  │   System    │      │
│    └─────────────┘                                  └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Основные информационные потоки

| Поток | Направление | Описание |
|-------|-------------|-----------|
| Business State | Jira → Platform | Статусы задач, переходы |
| Execution Request | Platform → Agent | Задачи для исполнения |
| Execution Result | Agent → Platform | Результаты выполнения |
| Artifact Reference | Agent → Platform | Ссылки на артефакты |
| Status Update | Platform → Jira | Синхронизация статусов |
| Audit Event | Platform → Audit Log | Логирование операций |

### 5.3 trust boundaries

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         TRUST BOUNDARIES                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  [TRUSTED]                           [UNTRUSTED]                         │
│  ┌─────────────────┐                 ┌─────────────────┐               │
│  │  Orchestration   │◀─────── HTTPS ──▶│   Jira API       │               │
│  │   Platform      │                 │   (External)     │               │
│  └────────┬────────┘                 └─────────────────┘               │
│           │                                                              │
│           │ HTTPS                                                       │
│           ▼                                                              │
│  ┌─────────────────┐                 ┌─────────────────┐               │
│  │  Agent Runtime  │◀─────── HTTPS ──▶│   MCP Tools     │               │
│  │  (Internal)     │                 │   (External)    │               │
│  └─────────────────┘                 └─────────────────┘               │
│                                                                           │
│  Legend:                                                                  │
│  ──── HTTPS calls are validated and signed                                │
│  ──── Internal gRPC for component communication                        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Workflows — Ключевые workflows

### 6.1 Workflow: Complete SDLC Journey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SDLC WORKFLOW — COMPLETE JOURNEY                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐             │
│  │ BA   │────▶│ SA   │────▶│ Dev  │────▶│ QA   │────▶│Done  │             │
│  │Stage │     │Stage │     │Stage │     │Stage │     │Stage │             │
│  └──────┘     └──────┘     └──────┘     └──────┘     └──────┘             │
│      │             │             │             │             │                │
│      ▼             ▼             ▼             ▼             ▼             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  Jira   │  │  Jira   │  │  Jira   │  │  Jira   │  │  Jira   │         │
│  │  TASK  │  │  TASK   │  │  TASK   │  │  TASK   │  │  TASK   │         │
│  │(Create)│  │(Refine) │  │(Build)  │  │(Test)   │  │(Deploy) │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│      │             │             │             │             │                │
│      ▼             ▼             ▼             ▼             ▼             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │Artifact│  │Artifact│  │Artifact│  │Artifact│  │Artifact│         │
│  │(BRD)   │  │(Spec)  │  │(Code)   │  │(Test   │  │(Release)│         │
│  │        │  │        │  │        │  │ Report)│  │        │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                                                                             │
│  Handoff Points:                                                             │
│  1. BA → SA: Requirements Review & Approval                                 │
│  2. SA → Dev: Technical Specification & Design Approval                  │
│  3. Dev → QA: Code & Test Artifacts with Build Status                        │
│  4. QA → Done: QA Sign-off & Deployment Approval                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Workflow: Handoff Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HANDOFF WORKFLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐                     │
│  │ Source   │         │  Handoff │         │  Target  │                     │
│  │ Agent   │────────▶│ Validator│────────▶│  Agent  │                     │
│  └──────────┘         └──────────┘         └──────────┘                     │
│        │                    │                    │                               │
│        │[1. Prepare]      │[2. Validate]     │[4. Acknowledge]             │
│        │   Payload         │   Contract        │   Receipt                   │
│        ▼                   │                   │                               │
│  ┌────────────┐           │                   │                               │
│  │Context +   │           │                   ▼                               │
│  │Artifacts   │           │           ┌───────────────┐                     │
│  │+ Metadata  │──────────▶│           │  Confirm     │                     │
│  └────────────┘           │           │  Processing  │◀── [5. Store]│
│                           ▼           └───────────────┘                     │
│                    ┌───────────────┐         │                               │
│                    │  [3. Transit ]│       │                               │
│                    │    Log Event  │────────┘                               │
│                    └───────────────┘                                       │
│                                                                             │
│  Details:                                                                   │
│  - Context includes: task_id, stage, role, artifacts[], metadata{}             │
│  - Validation: schema check, artifact existence, role permissions             │
│  - Transit: async message queue with guaranteed delivery                   │
│  - Store: persistent state update + audit log                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Workflow: Retry and Recovery

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RETRY AND RECOVERY WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                            ┌──────────────┐                               │
│                            │   Failure    │                               │
│                            │   Detected   │                               │
│                            └──────┬───────┘                               │
│                                   │                                       │
│                                   ▼                                       │
│                            ┌──────────────┐                               │
│                            │  Evaluate    │                               │
│                            │  Retry Type  │                               │
│                            └──────┬───────┘                               │
│                      ┌─────────────┴─────────────┐                        │
│                      │                           │                        │
│                      ▼                           ▼                        │
│              ┌──────────────┐           ┌──────────────┐                    │
│              │  Transient   │           │  Permanent  │                    │
│              │   Failure   │           │   Failure   │                    │
│              └──────┬───────┘           └──────┬───────┘                    │
│                     │                       │                             │
│                     ▼                       ▼                             │
│              ┌──────────────┐           ┌──────────────┐                    │
│              │  Apply      │           │   Create   │                    │
│              │  Backoff   │           │   Escalation │                   │
│              │  Policy   │           │   Alert    │                    │
│              └──────┬───────┘           └──────┬───────┘                    │
│                     │                       │                             │
│                     ▼                       ▼                             │
│              ┌──────────────┐           ┌──────────────┐                    │
│              │  Retry      │           │  Handoff to  │                    │
│              │  Execution  │           │  Human       │                    │
│              └──────────────┘           │  Reviewer    │                    │
│                                     └──────────────┘                    │
│                                                                             │
│  Backoff Strategy:                                                          │
│  - Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)            │
│  - Jitter: ±20% to prevent thundering herd                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Workflow: Approval Gate

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     APPROVAL GATE WORKFLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Artifact │───▶│ Approver │───▶│ Approve  │───▶│ Proceed  │              │
│  │ Ready    │    │ Queue   │    │ /Reject  │    │ to Next  │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │              │              │              │                       │
│       ▼              ▼              ▼              ▼                       │
│  ┌─────────┐   ┌─────────┐  ┌────────┐  ┌────────┐                      │
│  │ Collect │   │ Notify  │  │ Record │  │ Update │                      │
│  │ Criteria│   │ Approver│  │Decision│  │State + │                      │
│  │& Check  │   │ (Async) │  │ +Reason│  │Audit   │                      │
│  └─────────┘   └─────────┘  └────────┘  └────────┘                      │
│                                                                             │
│  Approval Criteria Types:                                                  │
│  - Manual: Human reviewer decision                                         │
│  - Automated: CI checks passed, coverage threshold                          │
│  - Conditional: Auto if criteria X, else Manual                           │
│                                                                             │
│  Timeout: 24 hours default, escalation after timeout                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Component Architecture — Архитектура компонентов

### 7.1 Компонентная диаграмма (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATION PLATFORM                        │    │
│  │  ┌─────────────────────────────────────────────────────────┐  │    │
│  │  │                  API GATEWAY                            │  │    │
│  │  │  (REST/gRPC, Auth, Rate Limiting, Logging)              │  │    │
│  │  └──────────────────────┬──────────────────────────────┘  │    │
│  │                           │                                    │    │
│  │  ┌───────────────────────▼────────────────────────────┐  │    │
│  │  │              ORCHESTRATION ENGINE                      │  │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌──��─��───────┐  │  │    │
│  │  │  │  Workflow  │  │   Agent    │  │   State   │  │  │    │
│  │  │  │  Manager   │  │Coordinator │  │  Manager  │  │  │    │
│  │  │  └─────────────┘  └─────────────┘  └────────────┘  │  │    │
│  │  └──────────────────────┬────────────────────────────┘  │    │
│  │                           │                                    │    │
│  │  ┌───────────────────────▼────────────────────────────┐  │    │
│  │  │                  STATE STORE                         │  │    │
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐         │  │    │
│  │  │  │ Runtime  │ │ Бизнес  │ │  Аудит   │         │  │    │
│  │  │  │  State   │ │ состояние │ │   Log     │         │  │    │
│  │  │  │ (Redis)  │ │ (Jira)    │ │(Postgres) │         │  │    │
│  │  │  └───────────┘ └───────────┘ └───────────┘         │  │    │
│  │  └─────────────────────────────────────────────────────┘  │    │
│  │                           │                                    │    │
│  │  ┌───────────────────────▼────────────────────────────┐  │    │
│  │  │                  INTEGRATION LAYER                 │  │    │
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐  │  │    │
│  │  │  │   Jira    │ │   Git     │ │    CI    │ │  MCP   │  │  │    │
│  │  │  │  Adapter  │ │ Adapter  │ │ Adapter  │ │Adapter│  │  │    │
│  │  │  └───────────┘ └───────────┘ └───────────┘ └────────┘  │  │    │
│  │  └─────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Компоненты и их ответственности

| Компонент | Ответственность | Public API |
|-----------|----------------|------------|
| **API Gateway** | Входная точка, auth, rate limiting | REST/gRPC endpoints |
| **Workflow Manager** | Управление workflow definition, execution | `start_workflow()`, `pause()`, `resume()` |
| **Agent Coordinator** | Координация агентов, handoff, lifecycle | `assign_task()`, `handoff()`, `complete_task()` |
| **State Manager** | Управление состояниями, переходы | `get_state()`, `transition()`, `validate()` |
| **Jira Adapter** | Интеграция с Jira API | CRUD for Jira issues |
| **Git Adapter** | Интеграция с Git API | `create_branch()`, `commit()`, `pr_create()` |
| **CI Adapter** | Интеграция с CI системой | `trigger_build()`, `get_status()` |
| **MCP Adapter** | Интеграция с MCP tools | `invoke_tool()`, `get_tools()` |

### 7.3 Communication Patterns

| Path | Protocol | Pattern | Description |
|------|----------|---------|-------------|
| API → Orchestration Engine | gRPC | Sync request/response |
| Engine → State Store | Redis Protocol | State read/write |
| Engine → Agent | gRPC (or HTTP) | Async task dispatch |
| Engine → Jira | REST API | Async webhook/callback |
| Engine → Audit | gRPC | Async event log |

### 7.4 ADR-001: Component Communication Protocol

#### ADR-001: Use gRPC for internal communication

**Статус:** Предложен

**Контекст:**  
Необходимо определить протокол внутренней коммуникации между компонентами.

**Решение:**  
Использовать gRPC (Protocol Buffers) для внутренней коммуникации между компонентами orchestration engine. REST только для внешних API.

**Последствия:**
- **Положительные:** Типизированные контракты, эффективная сериализация,.Code generation
- **Отрицательные:** Сложность отладки, необходимость protobuf компиляции

**Альтернативы:**
- REST: Проще для debugging, но менее эффективен
- Message queue (Kafka): Для high-volume, но добавляет complexity

---

## 8. Domain Model — Доменная модель

### 8.1 Core Entities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DOMAIN MODEL                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐       ┌─────────────────┐                         │
│  │    Workflow     │       │      Stage      │                         │
│  ├─────────────────┤       ├─────────────────┤                         │
│  │ id: UUID       │───▶   │ id: UUID        │                         │
│  │ name: string   │       │ name: string    │                         │
│  │ status: enum   │       │ type: enum      │                         │
│  │ current_stage  │       │ order: int      │                         │
│  │ created_at    │       │ agents: []     │                         │
│  │ updated_at    │       └─────────────────┘                         │
│  └─────────────────┘              │                                   │
│                                1:N                                   │
│  ┌─────────────────┐            │                                   │
│  │     Task       │            ▼                                   │
│  ├─────────────────┤       ┌─────────────────┐                         │
│  │ id: UUID       │       │     Agent      │                         │
│  │ jira_key: string│◀───   │ id: UUID       │                         │
│  │ type: enum     │       │ name: string   │                         │
│  │ status: enum │       │ type: enum    │                         │
│  │ stage: ref    │       │ skills: []    │                         │
│  │ assignee: ref│       │ status: enum │                         │
│  │ artifacts: [] │       │ capabilities │                         │
│  └─────────────────┘       └─────────────────┘                         │
│                                                                             │
│  ┌─────────────────┐       ┌─────────────────┐                         │
│  │   Artifact     │       │   Handoff       │                         │
│  ├─────────────────┤       ├─────────────────┤                         │
│  │ id: UUID       │       │ id: UUID         │                         │
│  │ type: enum    │       │ source_agent    │                         │
│  │ reference: URI│       │ target_agent   │                         │
│  │ metadata: {}  │       │ task: ref       │                         │
│  │ checksum: str │       │ context: {}     │                         │
│  │ created_by    │       │ status: enum    │                         │
│  └─────────────────┘       │ created_at    │                         │
│                             │ completed_at │                         │
│                             └─────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Entity Definitions

#### 8.2.1 Workflow

```python
class Workflow:
    """Workflow representing a complete SDLC journey."""
    
    id: UUID
    name: str                          # Human-readable name
    description: str                  # Business description
    status: WorkflowStatus             # RUNNING, PAUSED, COMPLETED, FAILED
    current_stage_id: UUID             # Current active stage
    stages: List[Stage]              # Ordered stages
    artifacts: List[Artifact]        # All artifacts produced
    metadata: Dict[str, Any]        # Custom metadata
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # ADR reference: Uses skills/state-machine-design for status transitions
```

#### 8.2.2 Stage

```python
class Stage:
    """Stage in SDLC workflow."""
    
    id: UUID
    workflow_id: UUID
    name: StageName                  # BA, SA, DEV, QA, DONE
    type: StageType                  # SEQUENTIAL, PARALLEL, APPROVAL
    order: int                      # Order in workflow
    agents: List[Agent]             # Assigned agents
    approval_criteria: Dict        # Approval requirements
    timeout: Optional[timedelta]   # Max execution time
    
    # ADR reference: Uses skills/jira-lifecycle-modeling for stage types
```

#### 8.2.3 Task

```python
class Task:
    """Work item representing a single unit of work."""
    
    id: UUID
    jira_key: str                  # Jira issue key
    workflow_id: UUID
    stage_id: UUID
    type: TaskType                  # REQUIREMENT, DESIGN, IMPLEMENTATION, TEST
    status: TaskStatus              # PENDING, IN_PROGRESS, BLOCKED, DONE, FAILED
    assignee: Optional[Agent]      # Assigned agent
    artifacts: List[Artifact]       # Produced artifacts
    retry_count: int               # Current retry count
    error: Optional[Error]         # Last error if failed
    
    # ADR reference: Uses skills/state-machine-design for status transitions
```

#### 8.2.4 Agent

```python
class Agent:
    """Agent capable of executing tasks."""
    
    id: UUID
    name: str                       # Agent name (e.g., "Build Orchestrator")
    type: AgentType                 # BUILD_ORCHESTRATOR, PLATFORM_ARCHITECT, etc.
    skills: List[str]              # Loaded skills
    status: AgentStatus            # IDLE, BUSY, OFFLINE, ERROR
    capabilities: Set[str]      # What the agent can do
    max_concurrent_tasks: int
    current_tasks: List[Task]      # Currently executing
    
    # ADR reference: Uses skills/architecture-design and agent-runtime-model
```

#### 8.2.5 Artifact

```python
class Artifact:
    """Work product produced by an agent."""
    
    id: UUID
    type: ArtifactType              # DOCUMENT, CODE, TEST_REPORT, BUILD, etc.
    name: str                     # Artifact name
    reference: URI               # URL or path to artifact
    version: str                 # Version identifier
    checksum: str               # SHA256 for verification
    metadata: Dict[str, Any]    # Type-specific metadata
    created_by: Agent            # Producer
    created_at: datetime
    
    # ADR reference: Uses skills/integration-contract-design for artifact types
```

---

## 9. State Model — Модель состояний

### 9.1 State Machine Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STATE MACHINE MODEL                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                                                                │     │
│  │    TODO ──────▶ IN_PROGRESS ──────▶ DONE                         │     │
│  │      │              │                │              │                │     │
│  │      │              │                │         ┌─────┴─────┐         │     │
│  │      │              │                │         ▼          ▼         │     │
│  │      ▼              ▼                │    APPROVED    REJECTED     │     │
│  │   BLOCKED         BLOCKED           │      │            │         │     │
│  │      │              │              │      │            │         │     │
│  │      └──────────────┴───────────────┘      ▼            ▼         │     │
│  │                                    BLOCKED       BLOCKED       │     │
│  │                                        │            │         │     │
│  │                                        └────────────┘         │     │
│  │                                                                │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  State Details:                                                           │
│  - TODO: Task created, waiting for execution                              │
│  - IN_PROGRESS: Task assigned and being executed                           │
│  - BLOCKED: Task waiting for dependency or approval                        │
│  - DONE: Task completed, awaiting approval                               │
│  - APPROVED: Approved and ready for handoff                              │
│  - REJECTED: Rejected, needs revision                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 State Transitions

| From State | To State | Trigger | Guard Condition | Action |
|------------|---------|---------|--------------|--------|
| TODO | IN_PROGRESS | `assign_task` | Agent available | Set assignee, start timer |
| IN_PROGRESS | DONE | `complete` | All checks passed | Store artifacts |
| IN_PROGRESS | BLOCKED | `block` | Dependency pending | Notify dependent |
| IN_PROGRESS | TODO | `retry` | Retry policy applied | Increment retry, schedule |
| DONE | APPROVED | `approve` | Approval granted | Log approval, trigger handoff |
| DONE | REJECTED | `reject` | Approval denied | Log rejection, notify |
| REJECTED | TODO | `revise` | New artifacts | Clear artifacts, restart |
| BLOCKED | IN_PROGRESS | `unblock` | Dependency resolved | Resume execution |
| BLOCKED | TODO | `escalate` | Timeout | Notify human reviewer |

### 9.3 State Storage Architecture

| State Type | Storage | TTL | Sync Strategy |
|-----------|---------|-----|---------------|
| **Runtime State** | Redis | Session TTL | In-memory, async write-back |
| **Business State** | Jira | N/A | Read on demand, write-through |
| **Derived State** | PostgreSQL | 1 year | Async aggregation |
| **Audit State** | PostgreSQL | 1 year | Synchronous write |

#### 9.3.1 Синхронизация между Redis (Runtime State) и Jira (Business State)

**Частота синхронизации:**
- **Read**: При каждом запуске задачи — платформа читает актуальное состояние из Jira
- **Write**: Немедленно после каждого перехода состояния (transition)
- **Periodic sync**: Каждые 5 минут для обнаружения внешних изменений в Jira

**Конфликт состояний:**
При обнаружении конфликта (runtime state в Redis отличается от business state в Jira):
1. **Jira выигрывает**: Если изменение пришло извне (через webhook), Jira считается авторитетным
2. **Runtime выигрывает**: Если изменение инициировано агентом платформы
3. **Conflict resolution**: Логирование конфликта в audit log для последующего анализа

**Event-based triggers:**
- `jira:issue_updated`: Webhook от Jira при изменении задачи
- `task:transition`: Внутреннее событие при переходе состояния
- `handoff:completed`: Событие при завершении handoff между агентами
- `approval:decision`: Событие при принятии решения об одобрении

**Eventual consistency:**
- Runtime state в Redis обновляется синхронно для низкой задержки
- Business state в Jira обновляется асинхронно с retry политикой
- Максимальное расхождение: до 30 секунд при высокой нагрузке
- Гарантия доставки: Message queue с подтверждением

### 9.4 ADR-002: State Storage Strategy

#### ADR-002: Distributed state with Jira as source of truth

**Статус:** Предложен

**Контекст:**
Как хранить состояние workflow и задач?

**Решение:**
- **Runtime state**: Redis для быстрого доступа (в памяти)
- **Business state**: Jira как source of truth для бизнес-сущностей
- **Derived state**: PostgreSQL для агрегированных метрик
- **Audit**: PostgreSQL с синхронной записью

**Последствия:**
- **Положительные:** Высокая производительность, data consistency
- **Отрицательные:** Complexity синхронизации, eventual consistency для derived metrics

**Альтернативы:**
- Single DB: Проще, но медленнее
- Event sourcing: Полный audit, но сложнее

---

## 10. Integration Boundaries — Границы интеграции

### 10.1 Интеграционная диаграмма

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION BOUNDARIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │              ORCHESTRATION PLATFORM                           │    │
│   │                                                             │    │
│   │  ┌─────────────────────────────────────────────────────────┐   │    │
│   │  │              INTEGRATION LAYER                      │   │    │
│   │  │                                                        │   │    │
│   │  │   ┌───────────┐  ┌───────────┐                     │   │    │
│   │  │   │ Contract  │  │  Error    │                     │   │    │
│   │  │   │ Validator │  │ Handler  │                     │   │    │
│   │  │   └─────┬─────┘  └──────────┘                     │   │    │
│   │  │         │                                            │   │    │
│   │  │─────────┼────────────────────────────────────────────│   │    │
│   │  │         │                  │                        │   │    │
│   │  │         ▼                  ▼                        │   │    │
│   │  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐            │   │    │
│   │  │  │Jira   │ │ Git   │ │ CI/   │ │  MCP  │            │   │    │
│   │  │  │Adapter│ │Adapter│ │CD     │ │Adapter│            │   │    │
│   │  │  └───────┘ └───────┘ └───────┘ └───────┘            │   │    │
│   │  └─────────────────────────────────────────────────────────┘   │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                          │           │           │           │              │
│                          ▼           ▼           ▼           ▼              │
│   ┌──────────────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│   │       JIRA CLOUD        │ │  GITHUB │ │  CI/CD  │ │MCP TOOLS│       │
│   │  (REST API, Webhooks)  │ │ (REST)  │ │ (API)   │ │(STDIN)  │       │
│   └───────────────────────┘ └─────────┘ └─────────┘ └─────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Integration Contracts

#### 10.2.1 Jira Integration Contract

| Operation | Endpoint | Method | Auth |
|-----------|----------|--------|------|
| Get issue | `/rest/api/3/issue/{issueId}` | GET | OAuth/API token |
| Update issue | `/rest/api/3/issue/{issueId}` | PUT | OAuth/API token |
| Transition | `/rest/api/3/issue/{issueId}/transitions` | POST | OAuth/API token |
| Create issue | `/rest/api/3/issue` | POST | OAuth/API token |
| Add comment | `/rest/api/3/issue/{issueId}/comment` | POST | OAuth/API token |

#### 10.2.2 Git Integration Contract

| Operation | Endpoint | Method | Auth |
|-----------|----------|--------|------|
| Get file | `/repos/{owner}/{repo}/contents/{path}` | GET | OAuth |
| Create branch | `/repos/{owner}/{repo}/git/refs` | POST | OAuth |
| Commit | `/repos/{owner}/{repo}/git/commits` | POST | OAuth |
| Create PR | `/repos/{owner}/{repo}/pulls` | POST | OAuth |

#### 10.2.3 CI Integration Contract

| Operation | Endpoint | Method | Auth |
|-----------|----------|--------|------|
| Trigger build | `/api/v1/builds` | POST | API key |
| Get build status | `/api/v1/builds/{id}` | GET | API key |
| Get logs | `/api/v1/builds/{id}/logs` | GET | API key |

### 10.3 Error Handling Strategy

| Error Category | Handling | Retry Policy |
|---------------|----------|-------------|
| Network timeout | Retry | Exponential backoff |
| Rate limit (429) | Retry after | RFC 7231 Retry-After |
| Auth failure (401) | Re-authenticate | No retry |
| Not found (404) | Fail | No retry |
| Server error (5xx) | Retry | Exponential backoff |

---

## 11. Jira Interaction Model — Модель взаимодействия с Jira

### 11.1 Mapping Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  JIRA INTERACTION MODEL                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ORCHESTRATION PLATFORM                         JIRA                   │
│   ┌─────────────────┐                         ┌─────────────┐          │
│   │  State Store   │                         │   Project   │          │
│   │                │◀─── Read State ─────────│             │          │
│   └────────┬───────┘                         └──────┬──────┘          │
│            │                                            │                │
│            │ Write State                                │                │
│            ▼                                            ▼                │
│   ┌─────────────────┐                         ┌─────────────┐          │
│   │ Workflow Engine│────────── Sync ─────────▶│   Issues    │          │
│   │                │                         │             │          │
│   └─────────────────┘                         └─────────────┘          │
│                                                                             │
│   Mapping:                                                                │
│   ┌──────────────┬─────────────────┬────────────────────────┐          │
│   │ Orchestration│   Jira          │    Direction           │          │
│   ├──────────────┼────────���─���──────┼────────────────────────┤          │
│   │ Workflow    │   Project       │    Create/Read          │          │
│   │ Stage       │   Issue Type    │    Create/Assign        │          │
│   │ Task        │   Issue         │    Bidirectional Sync  │          │
│   │ Task Status │   Issue Status  │    Jira Status Mapping  │          │
│   │ Artifact   │   Attachment    │    Attach Ref           │          │
│   │ Comment    │   Comment       │    Add/Read             │          │
│   └──────────────┴─────────────────┴────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Status Mapping

| Orchestration Status | Jira Status Category | Jira Status | Transition |
|---------------------|---------------------|--------------|------------|
| TODO | To Do | To Do | `start_progress` |
| IN_PROGRESS | In Progress | In Progress | `start_review` |
| BLOCKED | In Progress | Blocked | `unblock` |
| DONE | Done | Done | `approve` |
| APPROVED | Done | Verified | `deploy` |
| REJECTED | To Do | Changes Requested | `restart` |
| FAILED | Done | Failed | `restart` |

### 11.3 Custom Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `custom_orchestration_id` | String | Yes | UUID workflow |
| `custom_stage` | String | Yes | Current stage (BA/SA/DEV/QA) |
| `custom_handoff_context` | JSON | No | Handoff metadata |
| `custom_artifacts` | String | No | Comma-separated artifact refs |
| `custom_retry_count` | Number | No | Retry counter |
| `custom_approval_status` | String | No | APPROVED/PENDING/REJECTED |

### 11.4 Webhook Integration

| Event | Action | Priority |
|-------|--------|----------|
| `jira:issue_created` | Create workflow | High |
| `jira:issue_updated` | Sync state | High |
| `jira:issue_transitioned` | Process transition | High |
| `jira:comment_created` | Process comment | Medium |

---

## 12. Git / CI Interaction Model — Модель взаимодействия с Git/CI

### 12.1 Git Integration Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GIT INTEGRATION MODEL                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐              │
│   │                   OPERATIONS                      │              │
│   ├───────────────────────────────────────────────┬──┤              │
│   │                                               │  │              │
│   │   ┌─────────┐   ┌─────────┐   ┌─────────┐  │  │              │
│   │   │ Branch  ���   ��� Commit  │   │   PR   │  │  │              │
│   │   │ Create │   │ Create │   │ Create │  │  │              │
│   │   └─────────┘   └─────────┘   └─────────┘  │  │              │
│   │                                               │  │              │
│   │   ┌─────────┐   ┌─────────┐   ┌─────────┐  │  │              │
│   │   │ Branch  │   │  File   │   │   PR   │  │  │              │
│   │   │ Delete  │   │  Read   │   │ Update │  │  │              │
│   │   └─────────┘   └─────────┘   └─────────┘  │  │              │
│   │                                               │  │              │
│   └───────────────────────────────────────────────┴──┘              │
│                                                                             │
│   CI Trigger Flow:                                                        │
│   1. Agent produces code artifact                                          │
│   2. Platform triggers CI build via adapter                              │
│   3. CI updates build status                                              │
│   4. Platform syncs status to Jira                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 CI Integration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CI INTEGRATION FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Agent              Platform              CI System            Jira           │
│     │                  │                     │                   │           │
│     │ [1. Produce    │                     │                   │           │
│     │   Code]         │                     │                   │           │
│     ▼                 │                     │                   │           │
│     │ [2. Store      │                     │                   │           │
│     │   Artifact]    │                     │                   │           │
│     ├────────────────▶                     │                   │           │
│     │                  │ [3. Create PR] │                   │           │
│     │                  ├────────────────▶▶  │                   │           │
│     │                  │                     │                   │           │
│     │                  │                     │ [4. Trigger Build]          │
│     │                  │◀───────────────────▶                   │           │
│     │                  │                     │ [5. Build Status]            │
│     │                  │◀───────────────────▶                   │           │
│     │                  │                     │                   │           │
│     │                  │ [6. Update Task Status]               │           │
│     │                  ├─────────────────────────────────────▶            │
│     │                  │                     │                   │           │
│     │                  │ [7. Update Jira]  │                   │           │
│     │                  ├─────────────────────────────────────▶            │
│     │                  │                     │                   │           │
│     ▼                 ▼                     ▼                   ▼           │
│                                                                             │
│   Artifacts Produced:                                                         │
│   - build.json: CI build metadata                                          │
│   - test-results.xml: Test results                                        │
│   - coverage.xml: Code coverage report                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 CI Pipeline Mapping

| CI Stage | Orchestration Action | Status Update |
|----------|-----------------------|---------------|
| Build | Trigger CI build | IN_PROGRESS |
| Unit Tests | Run unit tests | IN_PROGRESS |
| Integration Tests | Run integration tests | IN_PROGRESS |
| Static Analysis | Run analysis | IN_PROGRESS |
| Deploy to Staging | Deploy | IN_PROGRESS |
| Smoke Tests | Run smoke tests | DONE |
| Deploy to Prod | Manual approval | APPROVED |

---

## 13. Agent Runtime Model — Модель runtime агентов

### 13.1 Agent Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT RUNTIME LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐                                                            │
│   │  Dormant│                                                            │
│   └───┬────┘                                                            │
│       │                                                                   │
│       │ [Load Skills]                                                      │
│       ▼                                                                   │
│   ┌─────────┐                                                            │
│   │ Initial │─── [Validation] ───▶ [Load Config]                       │
│   └───┬────┘                                                            │
│       │                                                                   │
│       │ [Start]                                                           │
│       ▼                                                                   │
│   ┌─────────┐                                                            │
│   │  Ready │──── [Heartbeat] ───▶ OK                                      │
│   └───┬────┘                                                            │
│       │                                                                   │
│       │ [Receive Task]                                                     │
│       ▼                                                                   │
│   ┌─────────────────┐                                                   │
│   │  Executing ──────── [Execute Task] ──── [Complete/Fail]            │
│   └─────────────────┘                                                   │
│       │                                                                   │
│       │ [Complete]                                                       │
│       ▼                                                                   │
│   ┌─────────┐                                                            │
│   │  Ready │                                                            │
│   └───┬────┘                                                            │
│       │                                                                   │
│       │ [Stop]                                                           │
│       ▼                                                                   │
│   ┌─────────┐                                                            │
│   │  Dormant│                                                            │
│   └─────────┘                                                            │
│                                                                             │
│   Agent States:                                                            │
│   - DORMANT: Not loaded, no skills                                        │
│   - INITIAL: Loading, validation in progress                               │
│   - READY: Idle, waiting for tasks                                       │
│   - EXECUTING: Processing task                                               │
│   - ERROR: Failed, needs intervention                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Agent Capabilities Mapping

| Build Agent | Capabilities | Primary Stage |
|------------|--------------|---------------|
| **Build Orchestrator** | workflow_coordination, task_assignment, handoff_management | Cross-cutting |
| **Platform Architect** | architecture_design, component_design | Planning |
| **Workflow Architect** | workflow_design, state_machine_design, process_modeling | Planning |
| **Agent Runtime Architect** | runtime_design, execution_model, resource_management | Implementation |
| **Integration Architect** | integration_design, api_design, contract_design | Implementation |
| **Implementation Engineer** | code_implementation, refactoring, bug_fixing | Implementation |
| **Verification Agent** | code_review, verification, quality_assessment | Verification |
| **Test Engineer** | test_design, test_automation, coverage_analysis | Testing |

### 13.3 Agent Execution Model

```python
class AgentExecutor:
    """Manages agent execution with concurrent task support."""
    
    concurrent_tasks: int          # Max parallel tasks
    task_timeout: timedelta        # Default task timeout
    
    def execute_task(self, task: Task, agent: Agent) -> ExecutionResult:
        """Execute a single task."""
        # 1. Validate task
        # 2. Load skills if needed
        # 3. Execute with timeout
        # 4. Handle result
        
    def execute_batch(self, tasks: List[Task], agent: Agent) -> List[ExecutionResult]:
        """Execute multiple tasks with concurrency control."""
        # Use semaphore for concurrency
```

### 13.4 ADR-003: Agent Skill Loading Strategy

#### ADR-003: Lazy skill loading with caching

**Статус:** Предложен

**Контекст:**  
Как загружать skills для агентов?

**Решение:**  
Lazy loading skills при первом использовании с TTL-based caching.

**Последствия:**
- **Положительные:** Экономия памяти, быстрый старт
- **Отрицательные:** Первый вызов медленнее

---

## 14. Skill Loading Model — Модель загрузки skills

### 14.1 Skill Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SKILL LOADING MODEL                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                    SKILL REGISTRY                                   │    │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │    │
│   │  │architecture│ │state-     │ │  jira-    │ │integration│        │    │
│   │  │-design    │ │machine-   │ │lifecycle- │ │contract- │        │    │
│   │  │           │ │design     │ │modeling  │ │design    │        │    │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │    │
│   │         │             │             │             │                  │    │
│   │         └─────────────┼─────────────┼─────────────┘                  │    │
│   │                       │           │                               │    │
│   │                       ▼           ▼                               │    │
│   │  ┌────────────────────────────────────────────────────────┐      │    │
│   │  │              SKILL LOADER                             │      │    │
│   │  │                                                        │      │    │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │      │    │
│   │  │  │ Validate │  │  Parse   │  │  Cache   │           │      │    │
│   │  │  │  Skill   │  │  Config  │  │  Loaded  │           │      │    │
│   │  │  └──────────┘  └──────────┘  └──────────┘           │      │    │
│   │  └────────────────────────────────────────────────────────┘      │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│   Skill Loading Flow:                                                       │
│   1. Request skill → 2. Check cache → 3. Load if needed → 4. Validate    │
│   → 5. Initialize → 6. Return to agent                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.2 Skill Definition

| Skill Name | Description | Dependencies | Used By |
|------------|-------------|---------------|----------|
| **architecture-design** | Проектирование системной архитектуры | - | Platform Architect |
| **state-machine-design** | Проектирование state machine | architecture-design | Workflow Architect |
| **jira-lifecycle-modeling** | Моделирование Jira workflow | state-machine-design | Integration Architect |
| **integration-contract-design** | Проектирование API контрактов | architecture-design | Integration Architect |
| **security-access-model** | Проектирование модели безопасности | architecture-design | Platform Architect |
| **observability-design** | Проектирование observability | architecture-design | Platform Architect |
| **test-strategy** | Определение тестовой стратегии | architecture-design | Test Engineer |
| **coding-standards** | Стандарты кодирования | - | Implementation Engineer |
| **handoff-packaging** | Упаковка и передача контекста между агентами | state-machine-design | Build Orchestrator |
| **implementation-planning** | Планирование реализации компонентов | architecture-design | Workflow Architect |
| **repo-structure-design** | Проектирование структуры репозитория | architecture-design | Integration Architect |
| **architecture-review** | Проверка и ревью архитектурных решений | architecture-design | Verification Agent |

### 14.3 Skill Loading Flow

```
Request Skill
     │
     ▼
┌────────────┐
│Check Cache │──Yes──▶ Return cached skill
└─────┬──────┘
      │No
      ▼
┌────────────┐
│ Load Skill │───▶ Parse SKILL.md
└─────┬─────┘
      │
      ▼
┌────────────┐
│Validate   │───▶ Check required fields
└─────┬─────┘
      │
      ▼
┌────────────┐
│ Initialize │───▶ Load dependencies
└─────┬─────┘
      │
      ▼
┌────────────┐
│Cache Skill │
└─────┬─────┘
      │
      ▼
  Return skill
```

---

## 15. Artifact Model — Модель артефактов

### 15.1 Artifact Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARTIFACT MODEL                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Artifact Types by Stage:                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │  BA Stage    │  SA Stage   │   Dev Stage   │   QA Stage           │     │
│   ├──────────────┼────────────┼───────────────┼──────────────────────┤     │
│   │  PRD         │  SPEC      │  CODE        │  TEST_REPORT         │     │
│   │  - Business  │  - Tech   │  - Source    │  - Test Results     │     │
│   │    Require-  │    Spec   │    Files     │  - Coverage Report │     │
│   │    ments     │  - Design │  - Config    │  - Smoke Tests      │     │
│   │  - User      │    Doc    │  - Scripts   │                    │     │
│   │    Stories   │  - API    │  - Tests     │  BUILD             │     │
│   │              │    Specs  │              │  - Build Artifacts│     │
│   │  EPIC        │           │              │  - Binaries       │     │
│   │  - Feature   │  ARCHI-   │  BUILD      │  - Packages       │     │
│   │    Epic      │    TECT   │  - Compiled │                    │     │
│   │              │    Doc   │    Binaries │  DEPLOYMENT       │     │
│   │              │          │  - Docker   │  - Deployment     │     │
│   │              │          │    Image    │    Config         │     │
│   └──────────────┴──────────┴──────────────┴──────────────────────┘     │
│                                                                             │
│   Artifact Metadata:                                                        │
│   - id: Unique identifier                                                   │
│   - type: ArtifactType                                                     │
│   - name: Human-readable name                                               │
│   - reference: URI to stored artifact                                      │
│   - checksum: SHA256 for verification                                      │
│   - version: Semantic version                                               │
│   - created_by: Agent that produced                                         │
│   - created_at: Timestamp                                                  │
│   - metadata: Type-specific data                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Artifact Storage

| Artifact Type | Storage | Reference | Retention |
|---------------|----------|-----------|-----------|
| DOCUMENT | Object Storage | URL | 1 year |
| CODE | Git Repository | Git URL | Indefinite |
| BUILD | Object Storage | URL | 30 days |
| TEST_REPORT | Object Storage | URL | 1 year |
| DEPLOYMENT_CONFIG | Git / Vault | Git URL / Vault path | Indefinite |

### 15.3 Artifact Metadata Schema

```json
{
  "id": "uuid",
  "type": "ARTIFACT_TYPE",
  "name": "artifact name",
  "reference": "s3://bucket/path or git://repo/path",
  "checksum": "sha256:abc123...",
  "version": "1.0.0",
  "created_by": {
    "agent_id": "uuid",
    "agent_name": "Build Orchestrator"
  },
  "created_at": "2026-04-11T10:00:00Z",
  "metadata": {
    "stage": "DEV",
    "commit_hash": "abc123",
    "build_id": "12345"
  }
}
```

---

## 16. Handoff Model — Модель handoff

### 16.1 Handoff Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HANDOFF PROCESS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Source Agent                                                        Target │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐      │
│   │Prepare   │────▶│Validate   │────▶│Package   │────▶│Transmit  │      │
│   │Payload   │     │Contract  │     │Context   │     │via Queue │      │
│   └──────────┘     └──────────┘     └──────────┘     └────┬─────┘      │
│                                                           │              │
│                                                           ▼              │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐      │
│   │Retrieve │◀────│Validate  │◀────│Unpack    │◀────│Receive   │      │
│   │Context  │     │Receipt   │     │Context   │     │Payload  │      │
│   └──────────┘     └──────────┘     └──────────┘     └──────────┘      │
│                                                                             │
│   Handoff Payload:                                                          │
│   {                                                                         │
│     "handoff_id": "uuid",                                                  │
│     "source_agent": {...},                                                 │
│     "target_agent": {...},                                                │
│     "task": {...},                                                         │
│     "artifacts": [...],                                                   │
│     "context": {...},                                                      │
│     "metadata": {...}                                                     │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Handoff Guarantees

| Guarantee | Mechanism | Description |
|-----------|-----------|-------------|
| **Delivery** | Message queue with ack | Гарантированная доставка |
| **Ordering** | FIFO queue | Порядок сохранён |
| **Idempotency** | Deduplication | Обработка дубликатов |
| **Timeout** | TTL + retry | Повторная попытка при таймауте |
| **Audit** | Complete log | Полный аудит всех handoff |

### 16.3 ADR-004: Handoff Protocol

#### ADR-004: Async message-based handoff

**Статус:** Предложен

**Контекст:**  
Какой протокол использовать для handoff между агентами?

**Решение:**  
Async message queue (Redis Streams или Kafka) с подтверждением и retry.

**Последствия:**
- **Положительные:** Надёжность, decoupling, scalability
- **Отрицательные:** eventual consistency, complexity

**Альтернативы:**
- Sync HTTP: Проще, но блокирующий
- Direct gRPC: Эффективен, но coupling

---

## 17. Retry / Failure Handling — Обработка ошибок и retry

### 17.1 Retry Policy Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RETRY POLICY                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    RETRY STRATEGY                              │      │
│   │                                                                 │      │
│   │  Failure Type:                                                    │      │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │      │
│   │  │   TRANSIENT     │  │    PERMANENT    │  │    UNKNOWN     │  │      │
│   │  │   (Retry)      │  │   (No Retry)   │  │  (Escalate)    │  │      │
│   │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │      │
│   │           │                      │                      │            │       │
│   │           ▼                      ▼                      ▼            │       │
│   │  ┌──────────────┐        ┌──────────────┐       ┌──────────────┐    │      │
│   │  │  Network    │        │  Validation │       │  Unknown   │    │      │
│   │  │  Timeout   │        │  Error     │       │  Error    │    │      │
│   │  │  429 Rate  │        │  404 Not   │       │  Timeout  │    │      │
│   │  │  Limit     │        │  Found     │       │  Human    │    │      │
│   │  │  5xx Error │        │  Auth     │       │  Review   │    │      │
│   │  │           │        │  Failed    │       │           │    │      │
│   │  └──────────────┘        └──────────────┘       └──────────────┘    │      │
│   │                                                                 │      │
│   │  Backoff Strategy: Exponential with jitter                        ���      │
│   │  - Initial: 1s, Max: 32s, Jitter: ±20%                        │      │
│   │  - Max retries: 5                                                 │      │
│   │  - Circuit breaker: 10 failures → open                         │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.2 Failure Categories

| Category | Examples | Retry | Action |
|----------|----------|-------|--------|
| **TRANSIENT** | Network timeout, rate limit, 5xx | Yes | Exponential backoff |
| **PERMANENT** | Invalid input, not found, auth failed | No | Fail immediately |
| **RETRYABLE_TRANSIENT** | Resource busy, temporary failure | Yes | Fixed delay |

### 17.3 Circuit Breaker

```python
class CircuitBreaker:
    """Circuit breaker for external dependencies."""
    
    failure_threshold = 10        # Open after 10 failures
    recovery_timeout = 60s         # Try half-open after 60s
    half_open_requests = 3         # Success threshold
    
    # States: CLOSED → OPEN → HALF_OPEN → CLOSED
```

---

## 18. Approval Gates — Шлюзы одобрения

### 18.1 Approval Gate Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    APPROVAL GATE TYPES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    APPROVAL GATE                                  │      │
│   │                                                                 │      │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │      │
│   │   │  MANUAL   │    │AUTOMATED   │    │CONDITIONAL│             │      │
│   │   │           │    │           │    │           │             │      │
│   │   │ Human     │    │ CI Checks │    │ If X then │             │      │
│   │   │ Reviewer  │    │ Passed   │    │ Auto else │             │      │
│   │   │ Decision  │    │          │    │ Manual    │             │      │
│   │   └─────────────┘    └─────────────┘    └─────────────┘             │      │
│   │                                                                 │      │
│   │   Gate Criteria:                                                   │      │
│   │   - Code Review: ≥ 2 approvals, no changes requested              │      │
│   │   - Tests: 100% unit tests pass, ≥80% coverage                    │      │
│   │   - Security: No critical vulnerabilities                          │      │
│   │   - Build: Successful build with no errors                       │      │
│   │   - Regression: No regression in smoke tests                  │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 18.2 Approval Flow

| Stage | Gate | Approver | Timeout | Escalation |
|-------|------|----------|---------|------------|
| BA → SA | Requirements Review | BA Lead | 24h | Project Manager |
| SA → Dev | Design Approval | Architect | 24h | Tech Lead |
| Dev → QA | Code Review | Peer Review | 24h | Team Lead |
| QA → Done | QA Sign-off | QA Lead | 24h | Project Manager |

### 18.3 Approval Decision Schema

```json
{
  "approval_id": "uuid",
  "task_id": "uuid",
  "gate_type": "MANUAL|AUTOMATED|CONDITIONAL",
  "decision": "APPROVED|REJECTED|PENDING",
  "approver": {
    "id": "uuid",
    "type": "AGENT|HUMAN",
    "name": "string"
  },
  "reason": "string",
  "conditions_met": [
    {"criterion": "code_review", "passed": true},
    {"criterion": "tests_passed", "passed": true}
  ],
  "decided_at": "datetime",
  "notified_at": "datetime"
}
```

---

## 19. Observability and Audit — Observability и аудит

### 19.1 Observability Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    METRICS                                       │      │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐                    │      │
│   │  │  Counter  │  │   Gauge   │  │ Histogram │                    │      │
│   │  │  (count)  │  │  (value)  │  │ (distrib) │                    │      │
│   │  └───────────┘  └───────────┘  └───────────┘                    │      │
│   │                                                                 │      │
│   │  Key Metrics:                                                    │      │
│   │  - workflow_duration_seconds                                   │      │
│   │  - handoff_latency_seconds                                      │      │
│   │  - task_success_total (by stage)                               │      │
│   │  - retry_count_total                                            │      │
│   │  - approval_latency_seconds                                     │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    LOGGING                                       │      │
│   │  -Structured JSON logs                                          │      │
│   │  -Level: DEBUG, INFO, WARN, ERROR                               │      │
│   │  -Correlation via trace_id                                      │      │
│   │  -Source: Component + Agent                                       │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    TRACING                                        │      │
│   │  -Distributed tracing via OpenTelemetry                         │      │
│   │  -Trace spans for each operation                                │      │
│   │  -Span attributes: task_id, stage, agent                        │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 19.2 Audit Log Schema

```json
{
  "audit_id": "uuid",
  "timestamp": "ISO8601",
  "event_type": "TASK_CREATED|TASK_COMPLETED|HANDOFF|APPROVAL|...",
  "actor": {
    "id": "uuid",
    "type": "AGENT|HUMAN|SYSTEM",
    "name": "string"
  },
  "target": {
    "entity_type": "TASK|WORKFLOW|ARTIFACT|...",
    "entity_id": "uuid"
  },
  "action": "CREATE|UPDATE|DELETE|TRANSITION",
  "changes": {
    "before": {...},
    "after": {...}
  },
  "context": {
    "trace_id": "uuid",
    "source_ip": "ip",
    "metadata": {...}
  }
}
```

### 19.3 ADR-005: Audit Storage Strategy

#### ADR-005: Immutable audit log with synchronous writes

**Статус:** Предложен

**Контекст:**  
Как хранить audit log?

**Решение:**  
Immutable audit log в PostgreSQL с синхронной записью для critical events.

**Последствия:**
- **Положительные:** Data integrity, real-time analytics
- **Отрицательные:** Write performance overhead

---

## 20. Security Model — Модель безопасности

### 20.1 Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY MODEL                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                   SECURITY LAYERS                               │      │
│   │                                                                 │      │
│   │   ┌─────────────────────────────────────────────────────────┐   │      │
│   │   │  INPUT VALIDATION                                        │   │      │
│   │   │  - Request schema validation                           │   │      │
│   │   │  - Input sanitization                                │   │      │
│   │   │  - Size limits                                     │   │      │
│   │   └─────────────────────────────────────────────────────────┘   │      │
│   │                              │                                   │      │
│   │   ┌─────────────────────────────────────────────────────────┐   │      │
│   │   │  AUTHENTICATION & AUTHORIZATION                      │   │      │
│   │   │  - JWT tokens for human users                       │   │      │
│   │   │  - API keys for agents                              │   │      │
│   │   │  - Role-based access control                       │   │      │
│   │   └─────────────────────────────────────────────────────────┘   │      │
│   │                              │                                   │      │
│   │   ┌─────────────────────────────────────────────────────────┐   │      │
│   │   │  NETWORK SECURITY                                       │   │      │
│   │   │  - TLS for all external communication                   │   │      │
│   │   │  - Internal mTLS for components                       │   │      │
│   │   │  - Network policies (Kubernetes)                     │   │      │
│   │   └─────────────────────────────────────────────────────────┘   │      │
│   │                              │                                   │      │
│   │   ┌─────────────────────────────────────────────────────────┐   │      │
│   │   │  DATA SECURITY                                        │   │      │
│   │   │  - Encryption at rest                               │   │      │
│   │   │  - Secret management (Vault)                         │   │      │
│   │   │  - Input/output validation                          │   │      │
│   │   └─────────────────────────────────────────────────────────┘   │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 20.2 Access Control Model

| Role | Permissions |
|------|-------------|
| **Platform Admin** | Full access to all resources |
| **Project Manager** | Start/stop workflows, view all, configure |
| **Agent** | Execute tasks, create artifacts, update own status |
| **Developer** | Work on assigned tasks, view code artifacts |
| **QA Engineer** | Work on QA tasks, view test results |
| **Reviewer** | Approve/reject, view all artifacts |

#### Agent Permissions

| Агент | Permissions |
|--------|-------------|
| Build Orchestrator | workflow:create, workflow:manage, agent:coordinate |
| Platform Architect | architecture:design, adr:create |
| Workflow Architect | workflow:design, state-machine:create |
| Agent Runtime Architect | agent-runtime:design, skill-load:configure |
| Integration Architect | integration:design, contract:define |
| Implementation Engineer | implementation:write, test:write |
| Verification Agent | architecture:review, code:review |
| Test Engineer | test-strategy:design, test:implement |

### 20.3 Security Best Practices

- **Authentication**: JWT with short-lived access tokens (15 min)
- **Authorization**: RBAC с принципом минимальных привилегий
- **Secrets**: HashiCorp Vault для хранения secrets
- **Input Validation**: Все входные данные валидируются по схеме
- **Rate Limiting**: 100 req/min per user, 1000 req/min per agent

---

## 21. Configuration Model — Модель конфигурации

### 21.1 Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION MODEL                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Configuration Precedence (highest to lowest):                           │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  1. Environment Variables                                        │      │
│   │     - Used for secrets and critical config                      │      │
│   │     - Example: JIRA_API_KEY, DATABASE_URL                       │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                               │                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  2. Config Files (config.yaml)                                   │      │
│   │     - Application configuration                                 │      │
│   │     - Example: stage_definitions, agent_configs                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                               │                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  3. Database Config (runtime)                                   │      │
│   │     - Dynamic configuration from state store                    │      │
│   │     - Example: feature flags, feature-specific configs          │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Conflict Resolution между уровнями:                                         │
│   1. **Environment Variables → Config Files**:                                  │
│      - Environment variables переопределяют значения из config.yaml               │
│      - Пример: DATABASE_URL из env имеет приоритет над db.url в yaml          │
│   2. **Config Files → Database Config**:                                        │
│      - Статические значения из yaml переопределяют динамические из БД           │
│      - Database config используется только для runtime feature flags               │
│                                                                             │
│   **Resolution механизм:**                                                  │
│   - При запуске: Все источники сливаются в единый config object              │
│   - При изменении: Hot reload с перезагрузкой только изменённых секций       │
│   - При конфликте: Логирование warning с указанием источника              │
│                                                                             │
│   Config Schema (config.yaml):                                             │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │  platform:                                                       │           │
│   │    name: orchestration-platform                                │           │
│   │    version: 1.0.0                                              │           │
│   │    environment: production                                       │           │
│   │                                                                 │           │
│   │  workflows:                                                      │           │
│   │    default: sdlc-default                                        │           │
│   │    definitions:                                                 │           │
│   │      sdlc-default:                                              │           │
│   │        stages: [ba, sa, dev, qa]                                 │           │
│   │        approval_gates: true                                       │           │
│   │                                                                 │           │
│   │  agents:                                                         │           │
│   │    max_concurrent_tasks: 5                                      │           │
│   │    task_timeout: 30m                                            │           │
│   │                                                                 │           │
│   │  integrations:                                                   │           │
│   │    jira:                                                        │           │
│   │      base_url: ${JIRA_URL}                                       │           │
│   │      api_version: v3                                            │           │
│   │    git:                                                         │           │
│   │      provider: github                                            │           │
│   │    ci:                                                          │           │
│   │      provider: github_actions                                    │           │
│   │                                                                 │           │
│   │  retry:                                                          │           │
│   │    max_retries: 5                                               │           │
│   │    initial_delay: 1s                                            │           │
│   │    max_delay: 32s                                               │           │
│   │    jitter: 0.2                                                  │           │
│   └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 21.2 Configuration Validation

- **At startup**: Full config validation
- **At runtime**: Hot reload with validation
- **Schema**: JSON Schema для всех конфигураций

---

## 22. Deployment Model — Модель деплоя

### 22.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODEL                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │            CONTAINER ORCHESTRATION (Kubernetes)                  │      │
│   │                                                                 │      │
│   │   ┌────────────────┐  ┌────────────────┐  ┌────────────┐  │      │
│   │   │ orchestration- │  │ agent-runtime  │  │   state-   │  │      │
│   │   │    engine      │  │    (pods)      │  │   store    │  │      │
│   │   │  (deployment) │  │  (HPA)        │  │ (stateful) │  │      │
│   │   └────────────────┘  └────────────────┘  └────────────┘  │      │
│   │                                                                 │      │
│   │   ┌────────────────┐  ┌────────────────┐  ┌────────────┐  │      │
│   │   │  api-gateway   │  │  postgres      │  │    redis   │  │      │
│   │   │   (ingress)   │  │(persistent)    │  │ (cluster)  │  │      │
│   │   └────────────────┘  └────────────────┘  └────────────┘  │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Environment:                                                              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌───────���─���───────┐           │
│   │   Development   │  │    Staging      │  │   Production    │           │
│   │   - Minikube    │  │   - K3s cluster │  │   - GKE/EKS    │           │
│   │   - Local DB    │  │   - Cloud DB    │  │   - Multi-AZ   │           │
│   │   - Debug      │  │   - Test data  │  │   - HA         │           │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 22.2 Kubernetes Resources

| Resource | Replicas | Storage | Resources |
|----------|---------|---------|-----------|
| orchestration-engine | 3 | N/A | 2CPU, 2Gi |
| agent-runtime | N | N/A | 1CPU, 1Gi |
| api-gateway | 3 | N/A | 1CPU, 512Mi |
| postgres | 1 | 20Gi PVC | 2CPU, 4Gi |
| redis | 3 | N/A (in-memory) | 2CPU, 4Gi |

### 22.3 Deployment Strategy

- **Blue/Green** для orchestration-engine
- **Rolling** для agent-runtime
- **Canary** для api-gateway

---

## 23. Extensibility Model — Модель расширяемости

### 23.1 Extension Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXTENSIBILITY MODEL                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Extension Points:                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                                                                 │      │
│   │  ┌─────────────────┐                                              │      │
│   │  │ Stage Type     │  Add new stage types (e.g., SECURITY_REVIEW)│   │      │
│   │  │               │                                              │      │
│   │  └─────────────────┘                                              │      │
│   │                                                                 │      │
│   │  ┌─────────────────┐                                              │      │
│   │  │ Agent Type      │  Add new agent capabilities              │   │      │
│   │  │               │                                              │   │      │
│   │  └─────────────────┘                                              │      │
│   │                                                                 │      │
│   │  ┌─────────────────┐                                              │      │
│   │  │ Integration     │  Add new external system adapters        │   │      │
│   │  │ Adapter         │                                              │   │      │
│   │  └────────────────���┘                                              │      │
│   │                                                                 │      │
│   │  ┌─────────────────┐                                              │      │
│   │  │ Approval Gate   │  Add new approval criteria types            │   │      │
│   │  │               │                                              │   │      │
│   │  └─────────────────┘                                              │      │
│   │                                                                 │      │
│   │  ┌─────────────────┐                                              │      │
│   │  │ Retry Policy    │  Add new retry strategies                  │   │      │
│   │  │               │                                              │   │      │
│   │  └─────────────────┘                                              │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Plugin Development:                                                       │
│   1. Define plugin interface                                                │
│   2. Implement plugin                                                     │
│   3. Register in config                                                   │
│   4. Hot reload                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 23.2 Plugin Interface Example

```python
class StagePlugin(ABC):
    """Base class for custom stage types."""
    
    @abstractmethod
    def validate(self, context: StageContext) -> ValidationResult:
        """Validate stage prerequisites."""
        pass
    
    @abstractmethod
    def execute(self, context: StageContext) -> ExecutionResult:
        """Execute stage logic."""
        pass
    
    @abstractmethod
    def get_approval_criteria(self, context: StageContext) -> List[Criterion]:
        """Get approval criteria."""
        pass
```

---

## 24. Risks and Tradeoffs — Риски и компромиссы

### 24.1 Identified Risks

| Risk | Severity | Impact | Mitigation Strategy |
|------|----------|--------|---------------------|
| **Jira API rate limiting** | High | Workflow stalls | Implement caching, request queue |
| **Single point of failure** | High | Platform downtime | Multi-region deployment, failover |
| **State sync conflicts** | Medium | Data inconsistency | Optimistic locking, reconciliation |
| **Agent timeout** | Medium | Workflow delay | Retry policies, escalation |
| **Security vulnerabilities** | High | Data breach | Regular audits, dependency scanning |
| **Complexity of integration** | Medium | Delivery delay | phased rollout, mock integration |

### 24.2 Architectural Tradeoffs

| Decision | Tradeoff | Rationale |
|----------|----------|-----------|
| **Distributed state** | Consistency vs Performance | Performance wins for v1.0 |
| **Async handoff** | Simplicity vs Reliability | Reliability prioritized |
| **Lazy skill loading** | Startup time vs Memory | Memory efficiency |
| **Jira as source of truth** | Coupling vs Single source | Single source required for business |

### 24.3 Future Considerations

- **v1.1**: Event sourcing для полного audit trail
- **v1.2**: Multi-tenant support
- **v1.3**: Visual workflow editor
- **v2.0**: AI-powered task assignment

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Handoff** | Process of transferring work from one agent to another |
| **Stage** | A logical phase in SDLC (BA, SA, Dev, QA) |
| **Artifact** | Work product produced by an agent |
| **Approval Gate** | Checkpoint requiring approval before proceeding |
| **Retry Policy** | Configuration for automatic retry on failure |
| **Source of truth** | Primary authoritative data source |

---

## Appendix B: References

- Build Agents Documentation
- Skills: architecture-design, state-machine-design, jira-lifecycle-modeling, integration-contract-design
- ADR templates from architecture-design skill

---

## Appendix C: Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-04-11 | Build Team | Initial SDD |

---

*Document generated using architecture-design and state-machine-design skills*