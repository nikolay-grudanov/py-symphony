# Jira-Driven Orchestration Platform for Agentic SDLC

![Status](https://img.shields.io/badge/status-bootstrap-green)  
![Version](https://img.shields.io/badge/version-0.1.0-blue)  
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

---

## Overview

Jira-driven orchestration platform - это платформа для автоматизации Software Development Life Cycle (SDLC) с использованием агентов. Платформа координирует разработку от требований до деплоя, используя Jira как source of truth.

### Ключевая концепция

**Build Team** из 8 специализированных агентов, которые координируют разработку через чётко определённые handoff контракты, state machines, и approval gates.

---

## What is it?

Это система, которая превращает ручной процесс разработки в автоматизированный агентный workflow:

1. **Stakeholder** создаёт задачу в Jira
2. **Build Orchestrator** принимает задачу и классифицирует её
3. **Build Team** (8 агентов) координирует разработку:
   - Platform Architect проектирует архитектуру платформы
   - Workflow Architect проектирует workflows и state machines
   - Agent Runtime Architect проектирует runtime для агентов
   - Integration Architect проектирует интеграции (Jira, Git, CI/CD)
   - Implementation Engineer реализует код
   - Verification Agent проверяет реализацию
   - Test Engineer создаёт и запускает тесты
4. **Product Agents** (BA, SA, Dev, QA) выполняют конкретные задачи на каждой стадии SDLC
5. **Build Orchestrator** координирует переходы между стадиями через approval gates
6. **Result**: PR создан, протестирован, и готов к деплою

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Jira (Source of Truth)                  │
│              Business State + Task Metadata                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Build Orchestrator                       │
│           Central Coordinator of Build Team                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌────────────┐ ┌─────────────┐
│ Build Team      │ │ Product    │ │ Integrations │
│ (8 agents)      │ │ Agents     │ │ (Jira, Git, │
│                 │ │ (BA, SA,   │ │ CI/CD)      │
│ Platform Arch   │ │ Dev, QA)   │ │             │
│ Workflow Arch   │ │            │ │             │
│ Runtime Arch    │ │            │ │             │
│ Integration Arch│ │            │ │             │
│ Implementation  │ │            │ │             │
│ Verification    │ │            │ │             │
│ Test Engineer   │ │            │ │             │
└─────────────────┘ └────────────┘ └─────────────┘
```

### State Management

```
┌─────────────────────────────────────────────────────────────┐
│                   Jira (Business State)                     │
│   Source of truth for task lifecycle and approvals          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Redis (Runtime State)                     │
│   Temporary state during execution (ephemeral)              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL (Derived State)                   │
│   Derived data for optimization and reporting              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL (Audit Artifacts)                  │
│   Immutable log of all actions and handoffs                │
└─────────────────────────────────────────────────────────────┘
```

---

## Build Team

### 8 Build Agents

| Agent | Mission | Key Responsibilities |
|-------|---------|---------------------|
| **Build Orchestrator** | Центральный координатор | Координация build-агентов, управление state machine, handoff |
| **Platform Architect** | Архитектор платформы | Проектирование архитектуры платформы, API, компонентов |
| **Workflow Architect** | Архитектор workflows | Проектирование workflows, state machines, бизнес-процессов |
| **Agent Runtime Architect** | Архитектор runtime | Проектирование runtime для агентов, загрузка skills, execution |
| **Integration Architect** | Архитектор интеграций | Проектирование интеграций (Jira, Git, CI/CD) |
| **Implementation Engineer** | Инженер-реализатор | Реализация кода по спецификациям |
| **Verification Agent** | Агент верификации | Проверка реализации на соответствие спецификациям |
| **Test Engineer** | Инженер тестирования | Создание тестов, тестирование реализации |

### Handoff Model

Агенты передают работу друг другу через **Handoff Packages** - структурированные пакеты с артефактами:

```json
{
  "metadata": {
    "id": "uuid",
    "source_agent": "Platform Architect",
    "target_agent": "Implementation Engineer",
    "timestamp": "2026-04-11T12:00:00Z",
    "version": "1.0.0"
  },
  "artifacts": [
    {
      "type": "design_doc",
      "path": "docs/architecture/platform-design.md",
      "description": "Платформенная архитектура",
      "checksum": "sha256:..."
    }
  ],
  "context": {
    "task_id": "TASK-123",
    "stage": "Foundation",
    "previous_handoff_id": "uuid"
  }
}
```

**17 Handoff Contracts** определены между всеми build-агентами с чёткими quality gates.

---

## State Machines

### Platform State Machine (11 состояний)

```
Task Intake → Classification → Planning → Stage Assignment → Execution → Waiting for Approval → Completed
                          ↓            ↓            ↓
                        Retrying ← Failed ← Blocked
                          ↓
                        Cancelled
```

### Build-Process State Machine (9 состояний)

```
Discovery → Design in Progress → Architecture Review → Implementation Ready → Implementation in Progress
                ↑                                            ↓
                └────────────────── Verification ←────────────┘
                                ↓
                              Rework (если не пройдена проверка)
                                ↓
                              Testing → Accepted
```

---

## Documentation

### Quick Links

- 📚 [Документация](docs/README.md) - Полная документация проекта
- 🏗️ [Software Design Document](docs/sdd-orchestration-platform.md) - Архитектура платформы (24 секции)
- 🔄 [State Machines](docs/state-machines.md) - State machine спецификации
- 🤝 [Handoff Contracts](docs/handoff-contracts.md) - Контракты между агентами
- 📁 [Repository Structure](docs/repository-structure.md) - Структура репозитория
- 🗺️ [Implementation Roadmap](docs/planning/implementation-roadmap.md) - План реализации (5 фаз)

### Build Team Documentation

- 👥 [Build Agents](.opencode/agents/) - Каталог build-агентов
- 🛠️ [Skills](.opencode/skills/) - Каталог навыков агентов

---

## Quick Start

### Prerequisites

- Jira Cloud или Jira Server с API доступом
- Git репозиторий
- Kubernetes cluster
- Redis instance
- PostgreSQL database

### Bootstrap Phase (Completed) ✅

Bootstrap Phase уже завершён. Все артефакты созданы:

```bash
# Проверить созданные файлы
ls -la docs/                # Документация
ls -la .opencode/agents/    # Build агенты
ls -la .opencode/skills/    # Skills
```

### Phase 1: Foundation (Next)

Следующая фаза - создание базовой инфраструктуры:

1. **Создание Kubernetes manifests**
2. **Настройка Config Loader**
3. **Создание State Store (Redis)**
4. **Базовое логирование**

Ожидаемая длительность: **2-3 недели**

---

## Implementation Roadmap

| Phase | Name | Duration | Status |
|-------|------|----------|--------|
| 0 | Bootstrap | 1 week | ✅ Completed |
| 1 | Foundation | 2-3 weeks | ⏳ Next |
| 2 | Core Integration | 3-4 weeks | ⏳ Planned |
| 3 | Multi-Stage | 4-5 weeks | ⏳ Planned |
| 4 | Advanced Features | 6-8 weeks | ⏳ Planned |
| 5 | Production Ready | 2-3 weeks | ⏳ Planned |

**Total:** ~20-24 weeks (5-6 months)

### MVP vs Target Architecture

| Category | MVP | Target |
|-----------|------|--------|
| Jira Integration | Read-only | Read/Write |
| Stages | Dev only | BA, SA, Dev, QA |
| Handoff | Basic | Full with retry/escalation |
| State Storage | Local | Distributed (Redis + Jira + PostgreSQL) |
| Observability | Basic logs | Full observability |

---

## Contributing

Этот проект находится в Bootstrap Phase. Основная документация и артефакты уже созданы.

Для вклада:
1. Изучите [Software Design Document](docs/sdd-orchestration-platform.md)
2. Изучите [Build Agents](.opencode/agents/)
3. Следуйте [Implementation Roadmap](docs/planning/implementation-roadmap.md)
4. Создайте PR для review

---

## Architecture Decision Records (ADRs)

5 ключевых архитектурных решений:

- **ADR-001:** Component Communication (gRPC)
- **ADR-002:** State Storage (Distributed: Redis + Jira + PostgreSQL)
- **ADR-003:** Skill Loading (Lazy + Caching)
- **ADR-004:** Handoff Protocol (Async message queue)
- **ADR-005:** Audit Storage (Immutable synchronous writes)

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Status

**Current Phase:** Bootstrap ✅ Completed  
**Next Phase:** Phase 1: Foundation ⏳  
**Estimated Time to Production:** 5-6 months

---

*Created: April 11, 2026*  
*Last Updated: April 11, 2026*
