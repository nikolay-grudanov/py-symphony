# Repository Structure

**Версия:** 1.0.0  
**Дата:** 2026-04-11  
**Статус:** Draft  
**Автор:** Build Team  

---

## Содержание

1. [Обзор структуры](#обзор-структуры)
2. [Детальное описание директорий](#детальное-описание-директорий)
3. [Конвенции именования файлов](#конвенции-именования-файлов)
4. [Git Ignore Patterns](#git-ignore-patterns)
5. [README.md Структура](#readme-md-структура)
6. [.opencode/ Directory](#opencode-directory)
7. [Deployment Configs](#deployment-configs)

---

## Обзор структуры

```
py-symphony/
├── .github/                          # GitHub конфигурации
│   ├── workflows/                    # CI/CD workflows
│   └── ISSUE_TEMPLATE/               # Шаблоны issue
├── .opencode/                        # OpenCode специальная директория
│   ├── agents/                       # Build и продуктовые агенты
│   ├── skills/                       # Навыки агентов
│   └── rules/                        # Правила для агентов
├── docs/                             # Документация
│   ├── adr/                          # Architecture Decision Records
│   ├── specs/                        # Спецификации компонентов
│   ├── diagrams/                     # Диаграммы архитектуры
│   ├── guides/                       # Руководства и HOW-TO
│   └── api/                          # API документация
├── agents/                           # Агенты (дубликат .opencode/agents/)
│   ├── build/                        # Build-агенты
│   └── product/                      # Продуктовые агенты (BA, SA, Dev, QA)
├── skills/                           # Навыки (дубликат .opencode/skills/)
│   ├── architecture/                 # Архитектурные навыки
│   ├── development/                  # Навыки разработки
│   ├── testing/                      # Навыки тестирования
│   └── operations/                   # Навыки операций
├── workflows/                        # Workflows и State Machines
│   ├── definitions/                  # Определения workflows
│   ├── state-machines/              # State machine спецификации
│   └── templates/                    # Шаблоны workflows
├── schemas/                          # Схемы данных и контракты
│   ├── handoff/                      # Handoff контракты
│   ├── data/                         # Схемы данных
│   ├── api/                          # API схемы
│   └── validation/                   # Валидационные схемы
├── integrations/                     # Интеграции
│   ├── jira/                         # Jira интеграция
│   ├── git/                          # Git интеграция
│   ├── ci/                           # CI/CD интеграция
│   └── mcp/                          # MCP tools интеграция
├── runtime/                          # Runtime компоненты
│   ├── engine/                       # Orchestration engine
│   ├── agents/                       # Agent runtime
│   ├── skills/                       # Skill loading
│   ├── state/                        # State management
│   └── adapters/                     # Адаптеры интеграций
├── tests/                            # Тесты
│   ├── unit/                         # Unit тесты
│   ├── integration/                  # Интеграционные тесты
│   ├── e2e/                          # E2E тесты
│   └── fixtures/                     # Тестовые данные и mock-объекты
├── examples/                         # Примеры использования
│   ├── workflows/                    # Примеры workflows
│   ├── agents/                       # Примеры агентов
│   └── integrations/                 # Примеры интеграций
├── scripts/                          # Скрипты
│   ├── setup/                        # Setup скрипты
│   ├── deployment/                   # Deployment скрипты
│   ├── maintenance/                  # Maintenance скрипты
│   └── utils/                        # Утилитарные скрипты
├── deploy/                           # Deployment конфигурации
│   ├── k8s/                          # Kubernetes manifests
│   ├── helm/                         # Helm charts
│   └── terraform/                    # Terraform конфигурации
├── pyproject.toml                    # Python проект конфигурация
├── requirements.txt                  # Зависимости Python
├── setup.py                          # Setup скрипт
├── .gitignore                        # Git ignore patterns
├── README.md                         # Основная документация проекта
└── LICENSE                           # Лицензия
```

---

## Детальное описание директорий

### docs/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `sdd-orchestration-platform.md` | Design-time, Human-authored | Software Design Document - основной архитектурный документ |
| `state-machines.md` | Design-time, Human-authored | State Machine спецификации для Platform и Build-Process |
| `handoff-contracts.md` | Design-time, Human-authored | Handoff контракты между build-агентами |
| `repository-structure.md` | Design-time, Human-authored | Документ структуры репозитория |
| `adr/` | Design-time, Human-authored | Architecture Decision Records |
| `adr/adr-001-component-communication.md` | Design-time, Human-authored | ADR: gRPC vs REST для внутренней коммуникации |
| `adr/adr-002-state-storage.md` | Design-time, Human-authored | ADR: Выбор хранилища состояний |
| `specs/` | Design-time, Human-authored | Спецификации компонентов платформы |
| `specs/orchestrator.md` | Design-time, Human-authored | Спецификация Orchestration Engine |
| `specs/workflow-engine.md` | Design-time, Human-authored | Спецификация Workflow Engine |
| `specs/agent-coordinator.md` | Design-time, Human-authored | Спецификация Agent Coordinator |
| `diagrams/` | Design-time, Human-authored | Диаграммы архитектуры |
| `diagrams/c4-context.svg` | Design-time, Human-authored | C4 Level 1: System Context |
| `diagrams/c4-components.svg` | Design-time, Human-authored | C4 Level 2: Component Architecture |
| `diagrams/state-machine-platform.svg` | Design-time, Human-authored | State Machine: Platform Workflow |
| `diagrams/state-machine-build.svg` | Design-time, Human-authored | State Machine: Build Process |
| `guides/` | Design-time, Human-authored | Руководства и HOW-TO |
| `guides/getting-started.md` | Design-time, Human-authored | Руководство для начала работы |
| `guides/agent-development.md` | Design-time, Human-authored | Руководство по разработке агентов |
| `guides/skill-development.md` | Design-time, Human-authored | Руководство по разработке навыков |
| `guides/workflow-development.md` | Design-time, Human-authored | Руководство по разработке workflows |
| `api/` | Design-time, Agent-generated | API документация (автогенерация из OpenAPI spec) |
| `api/rest-api.yaml` | Design-time, Human-authored | OpenAPI спецификация REST API |
| `api/grpc/` | Design-time, Human-authored | gRPC proto файлы |

**Примечания:**
- Большинство файлов в `docs/` — design-time и human-authored
- `api/` содержит агент-генерируемую документацию
- ADR документы создаются архитекторами, но могут быть сгенерированы агентами

---

### agents/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `build/` | Design-time, Human-authored | Build-агенты (дубликат .opencode/agents/) |
| `build/build-orchestrator.md` | Design-time, Human-authored | Описание Build Orchestrator агента |
| `build/platform-architect.md` | Design-time, Human-authored | Описание Platform Architect агента |
| `build/workflow-architect.md` | Design-time, Human-authored | Описание Workflow Architect агента |
| `build/agent-runtime-architect.md` | Design-time, Human-authored | Описание Agent Runtime Architect агента |
| `build/integration-architect.md` | Design-time, Human-authored | Описание Integration Architect агента |
| `build/implementation-engineer.md` | Design-time, Human-authored | Описание Implementation Engineer агента |
| `build/verification-agent.md` | Design-time, Human-authored | Описание Verification Agent агента |
| `build/test-engineer.md` | Design-time, Human-authored | Описание Test Engineer агента |
| `product/` | Runtime, Human-authored | Продуктовые агенты (BA, SA, Dev, QA) |
| `product/business-analyst.md` | Runtime, Human-authored | Описание Business Analyst агента |
| `product/system-architect.md` | Runtime, Human-authored | Описание System Architect агента |
| `product/developer.md` | Runtime, Human-authored | Описание Developer агента |
| `product/qa-engineer.md` | Runtime, Human-authored | Описание QA Engineer агента |
| `product/product-owner.md` | Runtime, Human-authored | Описание Product Owner агента |

**Примечания:**
- `build/` директория содержит определения build-агентов (design-time)
- `product/` директория содержит определения продуктовых агентов (runtime)
- Оба типа агентов: human-authored с возможностью расширения агентами

---

### skills/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `architecture/` | Design-time, Human-authored | Архитектурные навыки |
| `architecture/architecture-design.md` | Design-time, Human-authored | Навык: Design Architecture |
| `architecture/architecture-review.md` | Design-time, Human-authored | Навык: Architecture Review |
| `development/` | Runtime, Human-authored | Навыки разработки |
| `development/coding-standards.md` | Design-time, Human-authored | Навык: Coding Standards |
| `development/implementation-planning.md` | Design-time, Human-authored | Навык: Implementation Planning |
| `testing/` | Runtime, Human-authored | Навыки тестирования |
| `testing/test-strategy.md` | Design-time, Human-authored | Навык: Test Strategy Design |
| `testing/code-review.md` | Design-time, Human-authored | Навык: Code Review |
| `operations/` | Runtime, Human-authored | Навыки операций |
| `operations/handoff-packaging.md` | Design-time, Human-authored | Навык: Handoff Packaging |
| `operations/state-machine-design.md` | Design-time, Human-authored | Навык: State Machine Design |
| `operations/security-access-model.md` | Design-time, Human-authored | Навык: Security Access Model |
| `operations/observability-design.md` | Design-time, Human-authored | Навык: Observability Design |
| `operations/integration-contract-design.md` | Design-time, Human-authored | Навык: Integration Contract Design |
| `operations/jira-lifecycle-modeling.md` | Design-time, Human-authored | Навык: Jira Lifecycle Modeling |

**Примечания:**
- Большинство навыков: design-time и human-authored
- Навыки могут быть загружены агентами во время выполнения
- Навыки в `.opencode/skills/` дублируются в `skills/` для удобства

---

### workflows/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `definitions/` | Runtime, Human-authored | Определения workflows |
| `definitions/sdlc-workflow.yaml` | Runtime, Human-authored | Определение полного SDLC workflow |
| `definitions/handoff-workflow.yaml` | Runtime, Human-authored | Определение handoff workflow |
| `definitions/retry-workflow.yaml` | Runtime, Human-authored | Определение retry workflow |
| `state-machines/` | Runtime, Human-authored | State machine спецификации |
| `state-machines/platform-sm.json` | Runtime, Human-authored | State machine для Platform |
| `state-machines/build-sm.json` | Runtime, Human-authored | State machine для Build Process |
| `templates/` | Design-time, Human-authored | Шаблоны workflows |
| `templates/sequential-workflow.yaml` | Design-time, Human-authored | Шаблон последовательного workflow |
| `templates/parallel-workflow.yaml` | Design-time, Human-authored | Шаблон параллельного workflow |
| `templates/conditional-workflow.yaml` | Design-time, Human-authored | Шаблон условного workflow |

**Примечания:**
- `definitions/` содержит рабочие определения workflows (runtime)
- `state-machines/` содержит спецификации state machines (runtime)
- `templates/` содержит шаблоны для создания новых workflows (design-time)

---

### schemas/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `handoff/` | Runtime, Human-authored | Handoff контракты и схемы |
| `handoff/handoff-package-schema.json` | Runtime, Human-authored | JSON Schema для Handoff Package |
| `handoff/contract-schema.json` | Runtime, Human-authored | JSON Schema для Handoff Contract |
| `data/` | Runtime, Human-authored | Схемы данных доменной модели |
| `data/workflow-schema.json` | Runtime, Human-authored | JSON Schema для Workflow |
| `data/stage-schema.json` | Runtime, Human-authored | JSON Schema для Stage |
| `data/task-schema.json` | Runtime, Human-authored | JSON Schema для Task |
| `data/agent-schema.json` | Runtime, Human-authored | JSON Schema для Agent |
| `data/artifact-schema.json` | Runtime, Human-authored | JSON Schema для Artifact |
| `api/` | Runtime, Human-authored | API схемы |
| `api/rest-api-schema.json` | Runtime, Human-authored | JSON Schema для REST API |
| `api/grpc-schemas/` | Runtime, Agent-generated | gRPC proto схемы (автогенерация) |
| `validation/` | Runtime, Human-authored | Валидационные схемы |
| `validation/validation-rules.json` | Runtime, Human-authored | Правила валидации |
| `validation/error-codes.json` | Runtime, Human-authored | Коды ошибок |

**Примечания:**
- Большинство схем: runtime и human-authored
- gRPC схемы могут быть автогенерированы агентами
- Валидационные схемы используются для handoff validation

---

### integrations/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `jira/` | Runtime, Human-authored | Jira интеграция |
| `jira/adapter.py` | Runtime, Human-authored | Jira адаптер |
| `jira/schema.json` | Runtime, Human-authored | Jira data mapping schema |
| `jira/config.yaml` | Runtime, Human-authored | Jira конфигурация |
| `git/` | Runtime, Human-authored | Git интеграция |
| `git/adapter.py` | Runtime, Human-authored | Git адаптер |
| `git/schema.json` | Runtime, Human-authored | Git data mapping schema |
| `git/config.yaml` | Runtime, Human-authored | Git конфигурация |
| `ci/` | Runtime, Human-authored | CI/CD интеграция |
| `ci/adapter.py` | Runtime, Human-authored | CI адаптер |
| `ci/schema.json` | Runtime, Human-authored | CI data mapping schema |
| `ci/config.yaml` | Runtime, Human-authored | CI конфигурация |
| `mcp/` | Runtime, Human-authored | MCP tools интеграция |
| `mcp/adapter.py` | Runtime, Human-authored | MCP адаптер |
| `mcp/schema.json` | Runtime, Human-authored | MCP data mapping schema |
| `mcp/config.yaml` | Runtime, Human-authored | MCP конфигурация |

**Примечания:**
- Все интеграции: runtime и human-authored
- Каждый адаптер использует свой schema для data mapping
- Конфигурации хранятся в YAML файлах

---

### runtime/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `engine/` | Runtime, Human-authored | Orchestration engine |
| `engine/orchestrator.py` | Runtime, Human-authored | Основной оркестратор |
| `engine/workflow-manager.py` | Runtime, Human-authored | Управление workflows |
| `engine/agent-coordinator.py` | Runtime, Human-authored | Координация агентов |
| `engine/state-manager.py` | Runtime, Human-authored | Управление состояниями |
| `agents/` | Runtime, Human-authored | Agent runtime |
| `agents/base-agent.py` | Runtime, Human-authored | Базовый класс агента |
| `agents/agent-loader.py` | Runtime, Human-authored | Загрузка агентов |
| `agents/agent-executor.py` | Runtime, Human-authored | Исполнение агентов |
| `skills/` | Runtime, Human-authored | Skill loading |
| `skills/skill-loader.py` | Runtime, Human-authored | Загрузка навыков |
| `skills/skill-executor.py` | Runtime, Human-authored | Исполнение навыков |
| `state/` | Runtime, Human-authored | State management |
| `state/state-store.py` | Runtime, Human-authored | Хранилище состояний |
| `state/transition-manager.py` | Runtime, Human-authored | Управление переходами |
| `state/retry-handler.py` | Runtime, Human-authored | Обработка retries |
| `adapters/` | Runtime, Human-authored | Адаптеры интеграций |
| `adapters/jira-adapter.py` | Runtime, Human-authored | Jira адаптер |
| `adapters/git-adapter.py` | Runtime, Human-authored | Git адаптер |
| `adapters/ci-adapter.py` | Runtime, Human-authored | CI адаптер |
| `adapters/mcp-adapter.py` | Runtime, Human-authored | MCP адаптер |

**Примечания:**
- Все runtime компоненты: runtime и human-authored
- Компоненты написаны на Python
- Каждый компонент имеет свои unit тесты

---

### tests/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `unit/` | Runtime, Human-authored | Unit тесты |
| `unit/test_orchestrator.py` | Runtime, Human-authored | Unit тесты для orchestrator |
| `unit/test_workflow-manager.py` | Runtime, Human-authored | Unit тесты для workflow manager |
| `unit/test_agent-coordinator.py` | Runtime, Human-authored | Unit тесты для agent coordinator |
| `unit/test_state-manager.py` | Runtime, Human-authored | Unit тесты для state manager |
| `integration/` | Runtime, Human-authored | Интеграционные тесты |
| `integration/test-workflow-integration.py` | Runtime, Human-authored | Интеграционные тесты для workflows |
| `integration/test-agent-integration.py` | Runtime, Human-authored | Интеграционные тесты для агентов |
| `integration/test-integration-integration.py` | Runtime, Human-authored | Интеграционные тесты для интеграций |
| `e2e/` | Runtime, Human-authored | E2E тесты |
| `e2e/test-complete-sdlc.py` | Runtime, Human-authored | E2E тест для полного SDLC |
| `e2e/test-handoff-workflow.py` | Runtime, Human-authored | E2E тест для handoff workflow |
| `fixtures/` | Runtime, Human-authored | Тестовые данные и mock-объекты |
| `fixtures/mock-jira.py` | Runtime, Human-authored | Mock для Jira |
| `fixtures/mock-git.py` | Runtime, Human-authored | Mock для Git |
| `fixtures/test-data/` | Runtime, Human-authored | Тестовые данные |

**Примечания:**
- Все тесты: runtime и human-authored
- Unit тесты тестируют изолированные компоненты
- Интеграционные тесты тестируют взаимодействие компонентов
- E2E тесты тестируют полные сценарии
- Fixtures используются для создания тестовых окружений

---

### examples/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `workflows/` | Design-time, Human-authored | Примеры workflows |
| `workflows/simple-sdlc.yaml` | Design-time, Human-authored | Пример простого SDLC workflow |
| `workflows/complex-sdlc.yaml` | Design-time, Human-authored | Пример сложного SDLC workflow |
| `workflows/custom-handoff.yaml` | Design-time, Human-authored | Пример custom handoff workflow |
| `agents/` | Design-time, Human-authored | Примеры агентов |
| `agents/custom-agent.md` | Design-time, Human-authored | Пример custom агента |
| `agents/custom-skill.md` | Design-time, Human-authored | Пример custom навыка |
| `integrations/` | Design-time, Human-authored | Примеры интеграций |
| `integrations/custom-integration.py` | Design-time, Human-authored | Пример custom интеграции |

**Примечания:**
- Все примеры: design-time и human-authored
- Примеры служат для обучения и шаблонов для новых функций

---

### scripts/

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `setup/` | Runtime, Human-authored | Setup скрипты |
| `setup/install.sh` | Runtime, Human-authored | Скрипт установки |
| `setup/init-db.sh` | Runtime, Human-authored | Скрипт инициализации базы данных |
| `deployment/` | Runtime, Human-authored | Deployment скрипты |
| `deployment/deploy.sh` | Runtime, Human-authored | Скрипт деплоя |
| `deployment/rollback.sh` | Runtime, Human-authored | Скрипт отката |
| `maintenance/` | Runtime, Human-authored | Maintenance скрипты |
| `maintenance/cleanup.sh` | Runtime, Human-authored | Скрипт очистки |
| `maintenance/backup.sh` | Runtime, Human-authored | Скрипт бэкапа |
| `utils/` | Runtime, Human-authored | Утилитарные скрипты |
| `utils/format-code.sh` | Runtime, Human-authored | Скрипт форматирования кода |
| `utils/run-tests.sh` | Runtime, Human-authored | Скрипт запуска тестов |
| `utils/lint.sh` | Runtime, Human-authored | Скрипт линтинга |

**Примечания:**
- Все скрипты: runtime и human-authored
- Скрипты упрощают разработку и деплой

---

## Конвенции именования файлов

### Общие правила

| Тип файла | Формат | Пример |
|-----------|--------|--------|
| Python файл | `{component}.py` | `orchestrator.py` |
| Тест Python | `test_{component}.py` | `test_orchestrator.py` |
| Markdown документ | `{document-name}.md` | `getting-started.md` |
| YAML конфигурация | `{config-name}.yaml` | `sdlc-workflow.yaml` |
| JSON схема | `{schema-name}.json` | `workflow-schema.json` |
| ADR документ | `adr-NNN-{slug}.md` | `adr-001-component-communication.md` |
| Спецификация | `spec-{component}.md` | `spec-orchestrator.md` |
| Диаграмма | `diag-{component}-{type}.{ext}` | `diag-workflow-state-machine.svg` |
| Скрипт | `{action}-{component}.sh` | `deploy.sh` |

### Имена директорий

| Тип директории | Формат | Пример |
|---------------|--------|--------|
| Агент | `{agent-name}/` | `platform-architect/` |
| Навык | `{skill-name}/` | `architecture-design/` |
| Интеграция | `{system}/` | `jira/` |
| Компонент | `{component}/` | `orchestrator/` |

### Версионирование

| Тип файла | Версионирование | Пример |
|-----------|----------------|--------|
| Документ | SemVer | `sdd-orchestration-platform.md:1.0.0` |
| Спецификация | SemVer | `spec-orchestrator-1.0.0.md` |
| ADR | Последовательный номер | `adr-001-...md` |
| API | SemVer | `rest-api-1.0.0.yaml` |

---

## Git Ignore Patterns

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
.env
.secrets
*.local

# Generated
runtime/agents/generated/
runtime/skills/generated/
api/grpc/generated/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Documentation
docs/_build/
docs/.doctrees/

# Database
*.db
*.sqlite
*.sqlite3

# Temporary
*.tmp
*.bak
*.swp
```

---

## README.md Структура

```markdown
# Py-Symphony

## Description
[Краткое описание проекта]

## Features
- [Основные возможности]

## Installation
[Инструкция по установке]

## Quick Start
[Быстрый старт]

## Architecture
[Ссылка на архитектурную документацию]

## Documentation
- [Getting Started](docs/guides/getting-started.md)
- [Architecture Overview](docs/sdd-orchestration-platform.md)
- [State Machines](docs/state-machines.md)
- [Handoff Contracts](docs/handoff-contracts.md)
- [API Documentation](docs/api/)

## Development
- [Repository Structure](docs/repository-structure.md)
- [Agent Development](docs/guides/agent-development.md)
- [Skill Development](docs/guides/skill-development.md)
- [Workflow Development](docs/guides/workflow-development.md)

## Testing
[Инструкция по тестированию]

## Deployment
[Инструкция по деплою]

## Contributing
[Руководство по контрибьюции]

## License
[Информация о лицензии]

## Contact
[Контактная информация]
```

---

## .opencode/ Directory

### Overview

`.opencode/` — специальная директория OpenCode, содержащая конфигурации агентов и навыков.

### Структура

```
.opencode/
├── agents/                      # Определения агентов
│   ├── build-orchestrator.md
│   ├── platform-architect.md
│   ├── workflow-architect.md
│   ├── agent-runtime-architect.md
│   ├── integration-architect.md
│   ├── implementation-engineer.md
│   ├── verification-agent.md
│   └── test-engineer.md
├── skills/                      # Определения навыков
│   ├── architecture/
│   │   ├── architecture-design/
│   │   └── architecture-review/
│   ├── development/
│   │   ├── coding-standards/
│   │   └── implementation-planning/
│   ├── testing/
│   │   ├── test-strategy/
│   │   └── code-review/
│   └── operations/
│       ├── handoff-packaging/
│       ├── state-machine-design/
│       ├── security-access-model/
│       ├── observability-design/
│       ├── integration-contract-design/
│       └── jira-lifecycle-modeling/
└── rules/                       # Правила для агентов
    ├── 02-language-safety.md
    └── 06-planning-workflow.md
```

### Классификация файлов

| Файл/Директория | Тип | Описание |
|------------------|-----|----------|
| `agents/*.md` | Design-time, Human-authored | Определения build-агентов |
| `skills/*/*/SKILL.md` | Design-time, Human-authored | Определения навыков |
| `rules/*.md` | Design-time, Human-authored | Правила для агентов |

**Примечания:**
- Все файлы в `.opencode/` — design-time и human-authored
- Эти файлы используются для загрузки агентов и навыков во время выполнения
- Изменения в этих файлах отражаются на runtime поведении агентов

---

## Deployment Configs

### Kubernetes

```
deploy/k8s/
├── namespace.yaml
├── configmap.yaml
├── secrets.yaml
├── deployments/
│   ├── orchestrator.yaml
│   ├── workflow-engine.yaml
│   ├── agent-coordinator.yaml
│   └── state-manager.yaml
├── services/
│   ├── orchestrator-service.yaml
│   ├── workflow-engine-service.yaml
│   └── agent-coordinator-service.yaml
├── ingress/
│   └── api-ingress.yaml
└── jobs/
    ├── db-migration.yaml
    └── data-seeding.yaml
```

| Файл | Тип | Описание |
|------|-----|----------|
| `namespace.yaml` | Design-time, Human-authored | Namespace definition |
| `configmap.yaml` | Design-time, Human-authored | Configuration values |
| `secrets.yaml` | Runtime, Human-authored | Sensitive data (encrypted) |
| `deployments/*.yaml` | Design-time, Human-authored | Deployment manifests |
| `services/*.yaml` | Design-time, Human-authored | Service manifests |
| `ingress/*.yaml` | Design-time, Human-authored | Ingress manifests |
| `jobs/*.yaml` | Design-time, Human-authored | Job manifests |

### Helm

```
deploy/helm/
├── py-symphony/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── configmap.yaml
│       └── ingress.yaml
```

| Файл | Тип | Описание |
|------|-----|----------|
| `Chart.yaml` | Design-time, Human-authored | Helm chart metadata |
| `values.yaml` | Runtime, Human-authored | Configuration values |
| `templates/*.yaml` | Design-time, Human-authored | Kubernetes templates |

### Terraform

```
deploy/terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── vpc/
│   ├── database/
│   └── redis/
└── environments/
    ├── dev/
    ├── staging/
    └── production/
```

| Файл | Тип | Описание |
|------|-----|----------|
| `main.tf` | Design-time, Human-authored | Main Terraform configuration |
| `variables.tf` | Design-time, Human-authored | Variable definitions |
| `outputs.tf` | Design-time, Human-authored | Output definitions |
| `modules/*/*.tf` | Design-time, Human-authored | Reusable modules |
| `environments/*/*.tf` | Runtime, Human-authored | Environment-specific configs |

**Примечания:**
- Большинство deployment конфигураций: design-time и human-authored
- `secrets.yaml` и environment-specific configs: runtime и human-authored
- Все deployment конфигурации управляются через GitOps

---

## Заключение

Этот документ описывает предложенную структуру репозитория для Orchestration Platform. Структура разработана с учётом:

1. **Чёткого разделения** между design-time и runtime артефактами
2. **Модульности** для лёгкого расширения
3. **Стандартизации** имён и конвенций
4. **Отслеживаемости** всех артефактов
5. **Автоматизации** там, где это возможно

Следование этой структуре гарантирует:
- Лёгкую навигацию по проекту
- Понятную организацию кода
- Возможность автоматического тестирования
- Эффективное CI/CD
- Простую интеграцию с внешними системами

### Дополнительные ресурсы

- **Software Design Document**: `docs/sdd-orchestration-platform.md`
- **State Machines**: `docs/state-machines.md`
- **Handoff Contracts**: `docs/handoff-contracts.md`
- **OpenCode Documentation**: `docs/llm.txt`

---

**Версия документа:** 1.0.0  
**Дата последнего обновления:** 2026-04-11  
**Статус:** Draft
