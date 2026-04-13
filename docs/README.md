# Документация Orchestration Platform

**Дата:** 11 апреля 2026  
**Статус:** Bootstrap Phase - Завершено

---

## Overview

Этот репозиторий содержит полную документацию для Jira-driven orchestration platform - платформы для автоматизации SDLC (Software Development Life Cycle) с использованием агентов.

**Ключевая концепция:** Build Team из 8 специализированных агентов, которые координируют разработку от требований до деплоя, используя Jira как source of truth.

---

## Getting Started

### Для начала работы с платформой:

1. **Понимание архитектуры:** Начните с [Software Design Document](sdd-orchestration-platform.md)
2. **State Machines:** Изучите [State Machine Specifications](state-machines.md)
3. **Handoff Contracts:** Поймите, как агенты передают работу друг другу в [Handoff Contracts](handoff-contracts.md)

### Для разработчиков:

1. **Build Team:** Изучите [Build Agent Catalog](../.opencode/agents/) - кто за что отвечает
2. **Skills:** Ознакомьтесь с [Skill Catalog](../.opencode/skills/) - какие навыки есть у каждого агента
3. **Implementation:** Следуйте [Implementation Roadmap](planning/implementation-roadmap.md) - план по фазам

---

## Core Documents

### 1. Software Design Document (SDD)

**Файл:** [sdd-orchestration-platform.md](sdd-orchestration-platform.md)  
**Размер:** 142 KB (24 секции)

Полное описание архитектуры платформы:

| Секция | Описание |
|--------|----------|
| System Purpose | Цель системы и значение для бизнеса |
| Goals / Non-Goals | Чего мы достигаем и чего НЕ достигаем |
| Actors and Roles | Роли в системе (Stakeholders, Build Team, Product Agents) |
| System Context | Как платформа взаимодействует с внешними системами |
| Key Workflows | Основные сценарии использования |
| Component Architecture | Архитектура компонентов (API Gateway, Config Loader, State Store, etc.) |
| Domain Model | Основные сущности (Task, BuildSession, HandoffPackage, Agent, Skill) |
| State Model | Управление состоянием (Jira = source of truth, Redis = runtime) |
| Integration Boundaries | Границы интеграций (Jira, Git, CI/CD) |
| Jira/Git/CI Interaction Models | Модели взаимодействия с Jira, Git, CI/CD |
| Agent/Skill/Artifact Models | Модели агентов, навыков, артефактов |
| Handoff Model | Как агенты передают работу друг другу |
| Retry/Failure Handling | Обработка ошибок и повторные попытки |
| Approval Gates | Ворота одобрения на каждой стадии SDLC |
| Observability and Audit | Мониторинг и аудит всех действий |
| Security Model | Модель безопасности и доступов |
| Configuration Model | Конфигурация (YAML, env vars, Jira) |
| Deployment Model | Модель деплоя (Kubernetes, Helm, ArgoCD) |
| Extensibility Model | Как расширять платформу |
| Risks and Tradeoffs | Риски и компромиссы |

**ADR Proposals:**
- ADR-001: Component Communication (gRPC)
- ADR-002: State Storage (Distributed: Redis + Jira + PostgreSQL)
- ADR-003: Skill Loading (Lazy + Caching)
- ADR-004: Handoff Protocol (Async message queue)
- ADR-005: Audit Storage (Immutable synchronous writes)

---

### 2. State Machine Specifications

**Файл:** [state-machines.md](state-machines.md)  
**Размер:** 47 KB (2 state machines)

Описание state machines для управления жизненным циклом задач:

#### A. Platform State Machine (11 состояний)

| Состояние | Описание | Владелец |
|-----------|----------|----------|
| Task Intake | Приём новой задачи | Build Orchestrator |
| Classification | Классификация задачи | Build Orchestrator |
| Planning | Планирование этапов | Build Orchestrator |
| Stage Assignment | Назначение стадии (BA, SA, Dev, QA) | Build Orchestrator |
| Execution | Выполнение задачи Product Agent'ом | Product Agent |
| Waiting for Approval | Ожидание одобрения на gate | Build Orchestrator |
| Blocked | Задача заблокирована | Build Orchestrator |
| Failed | Ошибка выполнения | Build Orchestrator |
| Retrying | Повторная попытка (exponential backoff) | Build Orchestrator |
| Completed | Задача завершена | Build Orchestrator |
| Cancelled | Задача отменена | Build Orchestrator |

#### B. Build-Process State Machine (9 состояний)

| Состояние | Описание | Владелец |
|-----------|----------|----------|
| Discovery | Исследование требований | Build Orchestrator |
| Design in Progress | Разработка дизайна (архитектура, workflow, интеграции) | Platform/Workflow/Integration Architect |
| Architecture Review | Архитектурный review | Verification Agent |
| Implementation Ready | Готовность к реализации | Build Orchestrator |
| Implementation in Progress | Реализация кода | Implementation Engineer |
| Verification | Верификация результата | Verification Agent |
| Rework | Переделка по замечаниям | Implementation Engineer |
| Testing | Тестирование | Test Engineer |
| Accepted | Результат принят | Build Orchestrator |

**Особенности:**
- Exponential backoff для retry logic
- Approval gates на каждой стадии SDLC
- Handling blocked state
- State transitions с guard conditions

---

### 3. Handoff Contracts

**Файл:** [handoff-contracts.md](handoff-contracts.md)  
**Размер:** 68 KB (17 контрактов)

Контракты передачи работы между build-агентами:

| # | От | Куда | Тип контракта |
|---|-----|-------|--------------|
| 1 | Build Orchestrator | Platform Architect | Начало дизайна платформы |
| 2 | Build Orchestrator | Workflow Architect | Начало дизайна workflows |
| 3 | Build Orchestrator | Agent Runtime Architect | Начало дизайна runtime |
| 4 | Build Orchestrator | Integration Architect | Начало дизайна интеграций |
| 5 | Platform Architect | Workflow Architect | Платформа → Workflows |
| 6 | Platform Architect | Integration Architect | Платформа → Интеграции |
| 7 | Platform Architect | Implementation Engineer | Дизайн → Реализация |
| 8 | Workflow Architect | Agent Runtime Architect | Workflows → Runtime |
| 9 | Workflow Architect | Implementation Engineer | Workflows → Реализация |
| 10 | Agent Runtime Architect | Implementation Engineer | Runtime → Реализация |
| 11 | Integration Architect | Implementation Engineer | Интеграции → Реализация |
| 12 | Implementation Engineer | Verification Agent | Реализация → Верификация |
| 13 | Implementation Engineer | Test Engineer | Реализация → Тестирование |
| 14 | Verification Agent | Implementation Engineer | Верификация → Переделка |
| 15 | Test Engineer | Build Orchestrator | Тестирование → Завершение |
| 16 | Verification Agent | Platform Architect | Верификация → Архитектор |
| 17 | Verification Agent | Workflow Architect | Верификация → Workflow Architect |

**Для каждого handoff определено:**
- Required inputs (что нужно передать)
- Output schema (формат JSON)
- Quality checklist (таблица с критериями качества)
- Rejection reasons (почему могут отклонить)
- What happens on ambiguity (что делать при неясности)
- What happens on missing artifact (что делать при отсутствии артефакта)

**Формат Handoff Package:**
```json
{
  "metadata": {
    "id": "uuid",
    "source_agent": "string",
    "target_agent": "string",
    "timestamp": "ISO8601",
    "version": "SemVer"
  },
  "artifacts": [
    {
      "type": "design_doc|code|test|config",
      "path": "string",
      "description": "string",
      "checksum": "string"
    }
  ],
  "context": {
    "task_id": "string",
    "stage": "string",
    "previous_handoff_id": "string|null"
  }
}
```

---

## Architecture

### Repository Structure

**Файл:** [repository-structure.md](repository-structure.md)  
**Размер:** 34 KB

Полная структура репозитория с классификацией файлов:

| Директория | Описание | Количество файлов |
|-------------|----------|-------------------|
| `docs/` | Документация (SDD, State Machines, Handoff Contracts) | 25 |
| `.opencode/agents/` | Build агенты (8 агентов + конфигурация) | 15 |
| `.opencode/skills/` | Навыки агентов (12 skills) | 12 |
| `agents/` | Product агенты (Business Analyst, Solution Architect, Dev, QA) | 15 |
| `workflows/` | Workflows и state machines | 8 |
| `schemas/` | Схемы данных и контракты | 9 |
| `integrations/` | Интеграции (Jira, Git, CI/CD) | 12 |
| `runtime/` | Runtime компоненты | 14 |
| `tests/` | Тесты | 14 |
| `examples/` | Примеры использования | 6 |
| `scripts/` | Скрипты (build, deploy, utils) | 8 |

**Классификация файлов:**
- Design-time vs Runtime
- Human-authored vs Agent-generated
- Git ignore patterns

---

### Integration Design

Модели взаимодействия с внешними системами:

| Система | Тип интеграции | Файл спецификации |
|---------|----------------|-------------------|
| Jira | Source of truth для бизнес-состояния | TBD |
| Git | Хранение артефактов и кода | TBD |
| CI/CD | Тестирование и деплой | TBD |
| Kubernetes | Runtime платформы | TBD |

---

## Implementation

### Implementation Roadmap

**Файл:** [planning/implementation-roadmap.md](planning/implementation-roadmap.md)  
**Размер:** 40 KB

План реализации по фазам:

#### MVP vs Target Architecture

| Категория | MVP | Target |
|-----------|------|--------|
| Jira Integration | Read-only | Read/Write |
| Stages | Dev only | BA, SA, Dev, QA |
| Handoff | Basic | Full with retry/escalation |
| State Storage | Local | Distributed (Redis + Jira + PostgreSQL) |
| Observability | Basic logs | Full observability (metrics, traces, alerts) |

#### Phased Implementation Plan

| Фаза | Название | Длительность | Статус |
|------|-----------|---------------|--------|
| 0 | Bootstrap | 1 неделя | ✅ Завершён |
| 1 | Foundation | 2-3 недели | ⏳ Запланирован |
| 2 | Core Integration | 3-4 недели | ⏳ Запланирован |
| 3 | Multi-Stage | 4-5 недель | ⏳ Запланирован |
| 4 | Advanced Features | 6-8 недель | ⏳ Запланирован |
| 5 | Production Ready | 2-3 недели | ⏳ Запланирован |

**Общая длительность:** ~20-24 недели (5-6 месяцев)

#### Risks and Design Decisions

**Risks (8):**
- Jira API stability
- Integration complexity
- Agent coordination overhead
- Performance bottlenecks
- Security concerns
- Scalability challenges
- Maintenance burden
- Adoption resistance

**Design Decisions (6):**
- gRPC для внутренней коммуникации
- Distributed state storage
- Lazy loading для skills
- Async message queue для handoff
- Immutable storage для audit
- Kubernetes для runtime

---

## Build Team

### Build Agent Catalog

**Директория:** [../.opencode/agents/](../.opencode/agents/)

8 специализированных build-агентов:

| # | Агент | Миссия | Ключевые обязанности |
|---|--------|--------|----------------------|
| 1 | [Build Orchestrator](../.opencode/agents/build-orchestrator.md) | Центральный координатор разработки | Координация build-агентов, управление state machine, handoff между агентами |
| 2 | [Platform Architect](../.opencode/agents/platform-architect.md) | Архитектор платформы | Проектирование архитектуры платформы, API, компонентов |
| 3 | [Workflow Architect](../.opencode/agents/workflow-architect.md) | Архитектор workflows | Проектирование workflows, state machines, бизнес-процессов |
| 4 | [Agent Runtime Architect](../.opencode/agents/agent-runtime-architect.md) | Архитектор runtime агентов | Проектирование runtime для агентов, загрузка skills, execution |
| 5 | [Integration Architect](../.opencode/agents/integration-architect.md) | Архитектор интеграций | Проектирование интеграций с Jira, Git, CI/CD |
| 6 | [Implementation Engineer](../.opencode/agents/implementation-engineer.md) | Инженер-реализатор | Реализация кода по спецификациям архитекторов |
| 7 | [Verification Agent](../.opencode/agents/verification-agent.md) | Агент верификации | Проверка реализации на соответствие спецификациям |
| 8 | [Test Engineer](../.opencode/agents/test-engineer.md) | Инженер тестирования | Создание тестов, тестирование реализации |

**Для каждого агента определено:**
- Name, mission, responsibilities, non-goals
- Allowed decisions, forbidden decisions
- Required inputs, expected outputs
- Handoff targets, quality gates
- Tools needed, skills allowed
- Escalation conditions

---

### Skill Catalog

**Директория:** [../.opencode/skills/](../.opencode/skills/)

12 специализированных навыков:

| # | Skill | Описание | Кто использует |
|---|-------|----------|----------------|
| 1 | [architecture-design](../.opencode/skills/architecture-design/SKILL.md) | Систематическое проектирование архитектуры | Platform Architect |
| 2 | [state-machine-design](../.opencode/skills/state-machine-design/SKILL.md) | Проектирование state machine | Workflow Architect |
| 3 | [jira-lifecycle-modeling](../.opencode/skills/jira-lifecycle-modeling/SKILL.md) | Моделирование Jira lifecycle | Build Orchestrator, Workflow Architect |
| 4 | [integration-contract-design](../.opencode/skills/integration-contract-design/SKILL.md) | Проектирование контрактов интеграции | Integration Architect |
| 5 | [repo-structure-design](../.opencode/skills/repo-structure-design/SKILL.md) | Проектирование структуры репозитория | All build agents |
| 6 | [coding-standards](../.opencode/skills/coding-standards/SKILL.md) | Стандарты кодирования | Implementation Engineer, Test Engineer |
| 7 | [implementation-planning](../.opencode/skills/implementation-planning/SKILL.md) | Планирование реализации | Implementation Engineer |
| 8 | [architecture-review](../.opencode/skills/architecture-review/SKILL.md) | Проверка архитектуры | Verification Agent |
| 9 | [test-strategy](../.opencode/skills/test-strategy/SKILL.md) | Стратегия тестирования | Test Engineer |
| 10 | [observability-design](../.opencode/skills/observability-design/SKILL.md) | Проектирование observability | Platform Architect, Integration Architect |
| 11 | [security-access-model](../.opencode/skills/security-access-model/SKILL.md) | Модель безопасности и доступа | Platform Architect, Integration Architect |
| 12 | [handoff-packaging](../.opencode/skills/handoff-packaging/SKILL.md) | Упаковка handoff-пакетов | All build agents |

**Формат навыков:** YAML-frontmatter + Markdown (AgentSkills.io spec)

---

## Reference

### Glossary

| Термин | Определение |
|--------|-------------|
| **Build Team** | Команда из 8 build-агентов, координирующих разработку |
| **Product Agent** | Агент, выполняющий конкретную задачу (BA, SA, Dev, QA) |
| **Handoff** | Передача работы от одного агента к другому |
| **Handoff Package** | Структурированный пакет с артефактами для передачи |
| **Quality Gate** | Точка проверки качества на каждом этапе |
| **Approval Gate** | Точка одобрения на каждой стадии SDLC |
| **State Machine** | Конечный автомат для управления жизненным циклом задачи |
| **Source of Truth** | Основной источник правды для бизнес-состояния (Jira) |
| **Runtime State** | Временное состояние выполнения (Redis) |
| **Derived State** | Производное состояние для оптимизации (PostgreSQL) |
| **Audit Artifact** | Неизменяемый лог всех действий (PostgreSQL) |
| **Skill** | Специализированный навык агента для конкретного типа работы |
| **ADR** | Architecture Decision Record - запись архитектурного решения |

### Links

- [OpenCode Documentation](https://opencode.ai) - Документация OpenCode
- [AgentSkills.io](https://agentskills.io) - Спецификация навыков агентов
- [Jira API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/) - API Jira
- [Kubernetes Documentation](https://kubernetes.io/docs/) - Документация Kubernetes

---

## Final Report

**Файл:** [reports/build-team-package-final-report.md](reports/build-team-package-final-report.md)

Итоговый отчёт о создании Build Team и всех артефактов:

- ✅ Build Agent Catalog: 8 build-агентов
- ✅ Skill Catalog: 12 skill-ов
- ✅ SDD: 24 секции, 5 ADR
- ✅ State Machines: 2 state machines
- ✅ Handoff Contracts: 17 контрактов
- ✅ Repository Structure: Полная структура
- ✅ Implementation Roadmap: 5 фаз + MVP vs Target

---

**Статус Bootstrap Phase:** ✅ Завершено  
**Следующая фаза:** Phase 1: Foundation (2-3 недели)

---

*Документ создан: 11 апреля 2026*
