# Handoff Contracts

**Версия:** 1.0.0  
**Дата:** 2026-04-11  
**Статус:** Draft  
**Автор:** Build Team  

---

## Содержание

1. [Общий формат Handoff Package](#общий-формат-handoff-package)
2. [Конвенции именования файлов](#конвенции-именования-файлов)
3. [Версионирование контрактов](#версионирование-контрактов)
4. [Обработка исключений](#обработка-исключений)
5. [Handoff Contracts](#handoff-contracts-1)

---

## Общий формат Handoff Package

### Структура пакета

Handoff Package — это структурированный контейнер для передачи данных между агентами. Он должен содержать:

```json
{
  "package_version": "1.0.0",
  "handoff_id": "uuid",
  "timestamp": "ISO8601",
  "source_agent": "agent-name",
  "target_agent": "agent-name",
  "workflow_id": "uuid",
  "task_id": "uuid",
  "context": {
    "stage": "stage-name",
    "previous_handoffs": ["handoff-id-1", "handoff-id-2"],
    "metadata": {}
  },
  "artifacts": [
    {
      "type": "document|code|test_report|spec|adr|other",
      "reference": "URI|file-path",
      "checksum": "sha256",
      "metadata": {}
    }
  ],
  "payload": {},
  "quality_checks": {
    "passed": true,
    "issues": [],
    "warnings": []
  }
}
```

### Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `package_version` | string | Версия формата пакета (SemVer) |
| `handoff_id` | uuid | Уникальный идентификатор handoff |
| `timestamp` | string | ISO8601 timestamp |
| `source_agent` | string | Имя агента-источника |
| `target_agent` | string | Имя агента-получателя |
| `workflow_id` | uuid | ID workflow |
| `task_id` | uuid | ID задачи |
| `context` | object | Контекст выполнения |
| `artifacts` | array | Список артефактов |
| `payload` | object | Специфичные для контракта данные |
| `quality_checks` | object | Результаты проверки качества |

---

## Конвенции именования файлов

### Имена файлов артефактов

| Тип артефакта | Формат | Пример |
|---------------|--------|--------|
| ADR документ | `adr-NNN-{slug}.md` | `adr-001-component-communication.md` |
| Спецификация | `spec-{component}-{version}.md` | `spec-orchestrator-1.0.0.md` |
| Диаграмма | `diag-{component}-{type}.{ext}` | `diag-workflow-state-machine.svg` |
| Реализация | `{component}.{ext}` | `orchestrator.ex` |
| Тест | `test_{component}.{ext}` | `test_orchestrator.exs` |
| Документация | `doc-{topic}.md` | `doc-architecture-overview.md` |

### Имена директорий

```
project-root/
├── docs/
│   ├── adr/
│   ├── specs/
│   └── diagrams/
├── src/
│   ├── orchestrator/
│   ├── adapters/
│   └── runners/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## Версионирование контрактов

### Правила SemVer

- **MAJOR**:Breaking changes в структуре handoff package
- **MINOR**: Добавление новых полей (backwards compatible)
- **PATCH**: Исправление документации, уточнения

### Версии контрактов

Каждый handoff контракт имеет версию:
- Версия документа: `handoff-contracts.md:1.0.0`
- Версия схемы: указывается в `package_version`
- Версия артефакта: указывается в имени файла

### Обновление версий

При изменении контракта:
1. Увеличить версию документа
2. Обновить `package_version` в схеме
3. Добавить запись в CHANGELOG.md
4. Сообщить всем затронутым агентам

---

## Обработка исключений

### Типы ошибок

| Тип | Код | Обработка |
|-----|-----|-----------|
| Missing required artifact | `MISSING_ARTIFACT` | Отклонение handoff |
| Invalid schema | `INVALID_SCHEMA` | Отклонение handoff |
| Permission denied | `PERMISSION_DENIED` | Эскалация |
| Validation failed | `VALIDATION_FAILED` | Запрос исправления |
| Timeout | `TIMEOUT` | Эскалация |
| Ambiguous input | `AMBIGUOUS_INPUT` | Запрос уточнения |

### Процедура обработки

1. **Детекция ошибки**: Агент-получатель обнаруживает проблему
2. **Логирование**: Запись в audit log с деталями
3. **Решение**:
   - Лёгкие ошибки: запрос уточнения/исправления
   - Критические ошибки: отклонение handoff
4. **Notification**: Уведомление Build Orchestrator
5. **Escalation**: При необходимости передача человеку

### Retry политика

- Транзиентные ошибки: до 5 попыток с exponential backoff
- Перманентные ошибки: немедленная эскалация
- Ambiguous inputs: до 2 запросов уточнения

---

# Handoff Contracts

## 1. Build Orchestrator → Platform Architect

### Required inputs

- **Инициирующий запрос** от пользователя или системы
- **Бизнес-требования** (если доступны)
- **Технические ограничения** (если доступны)
- **Контекст проекта** (существующая архитектура, технологии)
- **Приоритет задачи** (high/medium/low)

### Output schema

```json
{
  "type": "object",
  "properties": {
    "task_specification": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "task_type": {"type": "string", "enum": ["architecture_design", "component_design", "security_design"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "deadline": {"type": "string", "format": "date-time"}
      }
    },
    "requirements": {
      "type": "object",
      "properties": {
        "business": {"type": "array", "items": {"type": "string"}},
        "technical": {"type": "array", "items": {"type": "string"}},
        "security": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}}
      }
    },
    "context": {
      "type": "object",
      "properties": {
        "existing_architecture": {"type": "string"},
        "current_technologies": {"type": "array", "items": {"type": "string"}},
        "related_tasks": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Task ID является валидным UUID | ☐ |
| 2 | Тип задачи определён корректно | ☐ |
| 3 | Бизнес-требования сформулированы чётко | ☐ |
| 4 | Технические ограничения указаны | ☐ |
| 5 | Требования безопасности включены | ☐ |
| 6 | Контекст проекта предоставлен | ☐ |
| 7 | Приоритет установлен | ☐ |
| 8 | Дедлайн задан (если применимо) | ☐ |

### Rejection reasons

- Отсутствие бизнес-требований
- Неоднозначные или противоречивые требования
- Недостаточный контекст проекта
- Неверный формат task_id
- Противоречивые технические ограничения
- Отсутствие требований безопасности

### What happens on ambiguity

Build Orchestrator:
1. Запрашивает уточнение у пользователя
2. Дополняет контекст доступной информацией
3. Повторно передаёт задачу Platform Architect
4. Если не удаётся уточнить — эскалирует человеку

### What happens on missing artifact

- **Отсутствуют требования**: Запрос к Build Orchestrator на补充
- **Отсутствует контекст**: Build Orchestrator предоставляет контекст из проекта
- **Критичные артефакты отсутствуют**: Отклонение handoff с указанием отсутствующих артефактов

---

## 2. Build Orchestrator → Workflow Architect

### Required inputs

- **Инициирующий запрос** от пользователя или системы
- **Бизнес-требования к workflow**
- **Архитектура платформы** (от Platform Architect)
- **Требования к error handling**
- **Предпочтительный тип workflow** (sequential, parallel, conditional)

### Output schema

```json
{
  "type": "object",
  "properties": {
    "task_specification": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "task_type": {"type": "string", "enum": ["workflow_design", "state_machine", "retry_logic"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "deadline": {"type": "string", "format": "date-time"}
      }
    },
    "workflow_requirements": {
      "type": "object",
      "properties": {
        "business_requirements": {"type": "array", "items": {"type": "string"}},
        "architecture_reference": {"type": "string"},
        "error_handling_requirements": {"type": "array", "items": {"type": "string"}},
        "workflow_type": {"type": "string", "enum": ["sequential", "parallel", "conditional", "mixed"]},
        "performance_requirements": {"type": "object"}
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "max_timeout": {"type": "integer"},
        "max_retries": {"type": "integer"},
        "allowed_states": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Task ID является валидным UUID | ☐ |
| 2 | Тип задачи определён корректно | ☐ |
| 3 | Бизнес-требования к workflow сформулированы | ☐ |
| 4 | Ссылка на архитектуру платформы предоставлена | ☐ |
| 5 | Требования к error handling указаны | ☐ |
| 6 | Тип workflow выбран | ☐ |
| 7 | Ограничения по timeout и retries заданы | ☐ |
| 8 | Разрешённые состояния указаны | ☐ |

### Rejection reasons

- Отсутствие бизнес-требований к workflow
- Не предоставлена ссылка на архитектуру платформы
- Не указаны требования к error handling
- Не выбран тип workflow
- Противоречивые ограничения

### What happens on ambiguity

Build Orchestrator:
1. Запрашивает уточнение типа workflow
2. Запрашивает детали error handling
3. Предоставляет недостающую архитектуру
4. Повторно передаёт задачу

### What happens on missing artifact

- **Отсутствует архитектура**: Запрос к Platform Architect
- **Отсутствуют требования к error handling**: Запрос уточнения
- **Отсутствуют ограничения**: Build Orchestrator предоставляет стандартные ограничения

---

## 3. Build Orchestrator → Agent Runtime Architect

### Required inputs

- **Инициирующий запрос** от пользователя или системы
- **Требования к агентам** (типы агентов, навыки)
- **Архитектура платформы** (от Platform Architect)
- **Требования к навыкам (skills)**
- **Требования к handoff механизму**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "task_specification": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "task_type": {"type": "string", "enum": ["agent_runtime", "skill_loading", "prompt_design", "handoff_protocol"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "deadline": {"type": "string", "format": "date-time"}
      }
    },
    "agent_requirements": {
      "type": "object",
      "properties": {
        "agent_types": {"type": "array", "items": {"type": "string"}},
        "required_skills": {"type": "array", "items": {"type": "string"}},
        "architecture_reference": {"type": "string"},
        "handoff_requirements": {"type": "array", "items": {"type": "string"}}
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "max_concurrent_agents": {"type": "integer"},
        "skill_loading_timeout": {"type": "integer"},
        "handoff_timeout": {"type": "integer"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Task ID является валидным UUID | ☐ |
| 2 | Тип задачи определён корректно | ☐ |
| 3 | Типы агентов указаны | ☐ |
| 4 | Требуемые навыки перечислены | ☐ |
| 5 | Ссылка на архитектуру предоставлена | ☐ |
| 6 | Требования к handoff механизму указаны | ☐ |
| 7 | Ограничения по concurrency заданы | ☐ |
| 8 | Таймауты определены | ☐ |

### Rejection reasons

- Отсутствие списка типов агентов
- Не указаны требуемые навыки
- Не предоставлена ссылка на архитектуру
- Отсутствуют требования к handoff механизму
- Противоречивые ограничения

### What happens on ambiguity

Build Orchestrator:
1. Запрашивает список типов агентов
2. Уточняет требования к навыкам
3. Предоставляет архитектуру
4. Повторно передаёт задачу

### What happens on missing artifact

- **Отсутствуют типы агентов**: Запрос к Build Orchestrator на определение
- **Отсутствуют навыки**: Использовать стандартные навыки
- **Отсутствует архитектура**: Запрос к Platform Architect

---

## 4. Build Orchestrator → Integration Architect

### Required inputs

- **Инициирующий запрос** от пользователя или системы
- **Список внешних систем** для интеграции
- **API требования** для каждой системы
- **Требования к синхронизации данных**
- **Существующие интеграции** (если есть)

### Output schema

```json
{
  "type": "object",
  "properties": {
    "task_specification": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "task_type": {"type": "string", "enum": ["integration_design", "data_sync", "error_handling"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "deadline": {"type": "string", "format": "date-time"}
      }
    },
    "integration_requirements": {
      "type": "object",
      "properties": {
        "external_systems": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "system_name": {"type": "string"},
              "system_type": {"type": "string", "enum": ["jira", "git", "ci", "mcp", "other"]},
              "api_requirements": {"type": "object"}
            }
          }
        },
        "sync_requirements": {"type": "array", "items": {"type": "string"}},
        "existing_integrations": {"type": "array", "items": {"type": "string"}}
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "sync_frequency": {"type": "string"},
        "max_batch_size": {"type": "integer"},
        "retry_policy": {"type": "string"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Task ID является валидным UUID | ☐ |
| 2 | Тип задачи определён корректно | ☐ |
| 3 | Список внешних систем предоставлен | ☐ |
| 4 | Для каждой системы указан тип | ☐ |
| 5 | API требования определены | ☐ |
| 6 | Требования к синхронизации указаны | ☐ |
| 7 | Существующие интеграции учтены | ☐ |
| 8 | Ограничения заданы | ☐ |

### Rejection reasons

- Отсутствие списка внешних систем
- Не указан тип хотя бы для одной системы
- Отсутствуют API требования
- Не указаны требования к синхронизации
- Противоречивые ограничения по частоте синхронизации

### What happens on ambiguity

Build Orchestrator:
1. Запрашивает список внешних систем
2. Уточняет API требования для каждой системы
3. Предоставляет информацию о существующих интеграциях
4. Повторно передаёт задачу

### What happens on missing artifact

- **Отсутствуют внешние системы**: Запрос к Build Orchestrator на определение
- **Отсутствуют API требования**: Запрос к владельцу системы
- **Отсутствуют существующие интеграции**: Использовать пустой список

---

## 5. Platform Architect → Workflow Architect

### Required inputs

- **Архитектурные решения** (ADR документы)
- **Спецификация компонентов**
- **Диаграммы архитектуры**
- **Требования к интерфейсам**
- **Контекст workflow** (от Build Orchestrator)

### Output schema

```json
{
  "type": "object",
  "properties": {
    "architecture_package": {
      "type": "object",
      "properties": {
        "adr_documents": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "adr_number": {"type": "string"},
              "title": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "component_specification": {
          "type": "object",
          "properties": {
            "components": {"type": "array", "items": {"type": "string"}},
            "interfaces": {"type": "array", "items": {"type": "string"}},
            "dependencies": {"type": "array", "items": {"type": "string"}}
          }
        },
        "architecture_diagrams": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "diagram_type": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        }
      }
    },
    "workflow_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "workflow_type": {"type": "string"},
        "stage": {"type": "string"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | ADR документы предоставлены | ☐ |
| 2 | Каждое ADR имеет номер и title | ☐ |
| 3 | Спецификация компонентов определена | ☐ |
| 4 | Интерфейсы перечислены | ☐ |
| 5 | Зависимости указаны | ☐ |
| 6 | Архитектурные диаграммы включены | ☐ |
| 7 | Контекст workflow предоставлен | ☐ |
| 8 | Все ссылки на артефакты валидны | ☐ |

### Rejection reasons

- Отсутствие ADR документов
- Не определены компоненты
- Не указаны интерфейсы
- Не указаны зависимости
- Отсутствуют архитектурные диаграммы
- Невалидные ссылки на артефакты

### What happens on ambiguity

Platform Architect:
1. Уточняет требования к компонентам
2. Дополняет диаграммы при необходимости
3. Предоставляет дополнительные ADR
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют ADR документы**: Создание недостающих ADR
- **Отсутствует спецификация**: Создание спецификации компонентов
- **Отсутствуют диаграммы**: Создание архитектурных диаграмм

---

## 6. Platform Architect → Integration Architect

### Required inputs

- **Архитектурные решения** (ADR документы)
- **Модель безопасности**
- **Спецификация компонентов**
- **Интерфейсы взаимодействия**
- **Контекст интеграций** (от Build Orchestrator)

### Output schema

```json
{
  "type": "object",
  "properties": {
    "architecture_package": {
      "type": "object",
      "properties": {
        "adr_documents": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "adr_number": {"type": "string"},
              "title": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "security_model": {
          "type": "object",
          "properties": {
            "authentication": {"type": "string"},
            "authorization": {"type": "string"},
            "encryption": {"type": "string"}
          }
        },
        "interfaces": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "interface_name": {"type": "string"},
              "protocol": {"type": "string"},
              "authentication_required": {"type": "boolean"}
            }
          }
        }
      }
    },
    "integration_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "external_systems": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | ADR документы предоставлены | ☐ |
| 2 | Модель безопасности определена | ☐ |
| 3 | Методы аутентификации указаны | ☐ |
| 4 | Методы авторизации указаны | ☐ |
| 5 | Требования к шифрованию определены | ☐ |
| 6 | Интерфейсы перечислены | ☐ |
| 7 | Для каждого интерфейса указан протокол | ☐ |
| 8 | Требования аутентификации указаны | ☐ |

### Rejection reasons

- Отсутствие ADR документов
- Не определена модель безопасности
- Не указаны методы аутентификации
- Не указаны методы авторизации
- Не определены требования к шифрованию
- Отсутствуют интерфейсы

### What happens on ambiguity

Platform Architect:
1. Уточняет требования безопасности
2. Дополняет модель безопасности
3. Предоставляет дополнительные интерфейсы
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствует модель безопасности**: Создание модели безопасности
- **Отсутствуют интерфейсы**: Определение интерфейсов взаимодействия
- **Отсутствуют ADR документы**: Создание ADR для интеграций

---

## 7. Platform Architect → Implementation Engineer

### Required inputs

- **Архитектурные решения** (ADR документы)
- **Спецификация компонентов**
- **Модель безопасности**
- **Интерфейсы взаимодействия**
- **Требования к реализации**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "implementation_package": {
      "type": "object",
      "properties": {
        "adr_documents": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "adr_number": {"type": "string"},
              "title": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "component_specifications": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component_name": {"type": "string"},
              "specification_reference": {"type": "string"},
              "dependencies": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "security_requirements": {
          "type": "object",
          "properties": {
            "authentication": {"type": "string"},
            "authorization": {"type": "string"},
            "encryption": {"type": "string"}
          }
        },
        "interface_definitions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "interface_name": {"type": "string"},
              "protocol": {"type": "string"},
              "endpoints": {"type": "array", "items": {"type": "string"}}
            }
          }
        }
      }
    },
    "implementation_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "priority": {"type": "string"},
        "deadline": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | ADR документы предоставлены | ☐ |
| 2 | Спецификации компонентов определены | ☐ |
| 3 | Для каждого компонента есть спецификация | ☐ |
| 4 | Зависимости указаны | ☐ |
| 5 | Требования безопасности определены | ☐ |
| 6 | Интерфейсы определены | ☐ |
| 7 | Для каждого интерфейса указаны endpoints | ☐ |
| 8 | Все ссылки на артефакты валидны | ☐ |

### Rejection reasons

- Отсутствие ADR документов
- Не определены спецификации компонентов
- Не указаны зависимости
- Не определены требования безопасности
- Отсутствуют интерфейсы
- Невалидные ссылки на артефакты

### What happens on ambiguity

Platform Architect:
1. Уточняет спецификации компонентов
2. Дополняет зависимости
3. Предоставляет детализированные интерфейсы
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют ADR документы**: Создание ADR
- **Отсутствуют спецификации**: Создание спецификаций компонентов
- **Отсутствуют интерфейсы**: Определение интерфейсов

---

## 8. Workflow Architect → Agent Runtime Architect

### Required inputs

- **Спецификация состояний workflow**
- **Диаграмма переходов**
- **Спецификация retry логики**
- **Правила эскалации**
- **Архитектура платформы** (от Platform Architect)

### Output schema

```json
{
  "type": "object",
  "properties": {
    "workflow_package": {
      "type": "object",
      "properties": {
        "state_specification": {
          "type": "object",
          "properties": {
            "states": {"type": "array", "items": {"type": "string"}},
            "initial_state": {"type": "string"},
            "final_states": {"type": "array", "items": {"type": "string"}},
            "transitions": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "from": {"type": "string"},
                  "to": {"type": "string"},
                  "condition": {"type": "string"}
                }
              }
            }
          }
        },
        "diagram_reference": {"type": "string"},
        "retry_specification": {
          "type": "object",
          "properties": {
            "max_retries": {"type": "integer"},
            "backoff_strategy": {"type": "string"},
            "retryable_errors": {"type": "array", "items": {"type": "string"}}
          }
        },
        "escalation_rules": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "condition": {"type": "string"},
              "escalation_target": {"type": "string"},
              "action": {"type": "string"}
            }
          }
        }
      }
    },
    "architecture_reference": {"type": "string"}
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Состояния workflow определены | ☐ |
| 2 | Начальное состояние указано | ☐ |
| 3 | Финальные состояния указаны | ☐ |
| 4 | Переходы определены | ☐ |
| 5 | Для каждого перехода указано условие | ☐ |
| 6 | Диаграмма переходов предоставлена | ☐ |
| 7 | Retry логика определена | ☐ |
| 8 | Правила эскалации указаны | ☐ |

### Rejection reasons

- Не определены состояния workflow
- Не указано начальное состояние
- Не определены переходы
- Отсутствует диаграмма переходов
- Не определена retry логика
- Не указаны правила эскалации

### What happens on ambiguity

Workflow Architect:
1. Уточняет состояния и переходы
2. Дополняет диаграмму переходов
3. Уточняет retry логику
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствует спецификация состояний**: Создание спецификации
- **Отсутствует диаграмма**: Создание диаграммы переходов
- **Отсутствует retry логика**: Определение retry логики

---

## 9. Workflow Architect → Implementation Engineer

### Required inputs

- **Спецификация состояний workflow**
- **Диаграмма переходов**
- **Спецификация retry логики**
- **Правила эскалации**
- **Требования к реализации**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "workflow_implementation_package": {
      "type": "object",
      "properties": {
        "state_specification": {
          "type": "object",
          "properties": {
            "states": {"type": "array", "items": {"type": "string"}},
            "initial_state": {"type": "string"},
            "final_states": {"type": "array", "items": {"type": "string"}},
            "transitions": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "from": {"type": "string"},
                  "to": {"type": "string"},
                  "condition": {"type": "string"}
                }
              }
            }
          }
        },
        "diagram_reference": {"type": "string"},
        "retry_implementation_spec": {
          "type": "object",
          "properties": {
            "max_retries": {"type": "integer"},
            "backoff_strategy": {"type": "string"},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        },
        "escalation_implementation_spec": {
          "type": "object",
          "properties": {
            "rules": {"type": "array", "items": {"type": "string"}},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "implementation_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "priority": {"type": "string"},
        "deadline": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Состояния workflow определены | ☐ |
| 2 | Переходы определены | ☐ |
| 3 | Диаграмма переходов предоставлена | ☐ |
| 4 | Retry спецификация содержит implementation notes | ☐ |
| 5 | Эскалация содержит implementation notes | ☐ |
| 6 | Все ограничения указаны | ☐ |
| 7 | Контекст реализации предоставлен | ☐ |

### Rejection reasons

- Не определены состояния workflow
- Не определены переходы
- Отсутствует диаграмма переходов
- Не определена retry логика
- Не указаны правила эскалации
- Отсутствуют implementation notes

### What happens on ambiguity

Workflow Architect:
1. Уточняет детали реализации
2. Дополняет implementation notes
3. Предоставляет дополнительные детали
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствует спецификация состояний**: Создание спецификации
- **Отсутствует диаграмма**: Создание диаграммы переходов
- **Отсутствуют implementation notes**: Добавление notes

---

## 10. Agent Runtime Architect → Implementation Engineer

### Required inputs

- **Спецификация загрузки агентов**
- **Паттерны промптов**
- **Протокол handoff**
- **Модель генерации артефактов**
- **Требования к реализации**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "runtime_implementation_package": {
      "type": "object",
      "properties": {
        "agent_loading_spec": {
          "type": "object",
          "properties": {
            "loading_mechanism": {"type": "string"},
            "agent_types": {"type": "array", "items": {"type": "string"}},
            "skill_loading_pattern": {"type": "string"},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        },
        "prompt_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern_name": {"type": "string"},
              "pattern_type": {"type": "string"},
              "template": {"type": "string"}
            }
          }
        },
        "handoff_protocol_spec": {
          "type": "object",
          "properties": {
            "protocol_version": {"type": "string"},
            "message_format": {"type": "object"},
            "retry_mechanism": {"type": "string"},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        },
        "artifact_generation_spec": {
          "type": "object",
          "properties": {
            "supported_types": {"type": "array", "items": {"type": "string"}},
            "generation_patterns": {"type": "array", "items": {"type": "string"}},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "implementation_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "priority": {"type": "string"},
        "deadline": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Спецификация загрузки агентов определена | ☐ |
| 2 | Механизм загрузки указан | ☐ |
| 3 | Паттерны промптов предоставлены | ☐ |
| 4 | Для каждого паттерна указан тип | ☐ |
| 5 | Протокол handoff определён | ☐ |
| 6 | Версия протокола указана | ☐ |
| 7 | Модель генерации артефактов определена | ☐ |
| 8 | Implementation notes включены | ☐ |

### Rejection reasons

- Не определена спецификация загрузки агентов
- Не указан механизм загрузки
- Отсутствуют паттерны промптов
- Не определён протокол handoff
- Не определена модель генерации артефактов
- Отсутствуют implementation notes

### What happens on ambiguity

Agent Runtime Architect:
1. Уточняет детали загрузки
2. Дополняет паттерны промптов
3. Уточняет протокол handoff
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствует спецификация загрузки**: Создание спецификации
- **Отсутствуют паттерны**: Определение паттернов промптов
- **Отсутствует протокол**: Определение протокола handoff

---

## 11. Integration Architect → Implementation Engineer

### Required inputs

- **Спецификация интеграций**
- **Контракты данных**
- **Модель синхронизации**
- **Обработка ошибок**
- **Требования к реализации**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "integration_implementation_package": {
      "type": "object",
      "properties": {
        "integration_specs": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "system_name": {"type": "string"},
              "integration_type": {"type": "string"},
              "api_endpoint": {"type": "string"},
              "authentication_method": {"type": "string"},
              "implementation_notes": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "data_contracts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "contract_name": {"type": "string"},
              "data_format": {"type": "string"},
              "schema": {"type": "object"},
              "validation_rules": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "sync_spec": {
          "type": "object",
          "properties": {
            "sync_frequency": {"type": "string"},
            "sync_method": {"type": "string"},
            "batch_size": {"type": "integer"},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        },
        "error_handling_spec": {
          "type": "object",
          "properties": {
            "retry_policy": {"type": "string"},
            "error_codes": {"type": "array", "items": {"type": "string"}},
            "handling_strategies": {"type": "array", "items": {"type": "string"}},
            "implementation_notes": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "implementation_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "priority": {"type": "string"},
        "deadline": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Спецификации интеграций определены | ☐ |
| 2 | Для каждой интеграции указан тип | ☐ |
| 3 | API endpoints определены | ☐ |
| 4 | Методы аутентификации указаны | ☐ |
| 5 | Контракты данных определены | ☐ |
| 6 | Модель синхронизации определена | ☐ |
| 7 | Обработка ошибок определена | ☐ |
| 8 | Implementation notes включены | ☐ |

### Rejection reasons

- Не определены спецификации интеграций
- Не указаны API endpoints
- Не определены методы аутентификации
- Отсутствуют контракты данных
- Не определена модель синхронизации
- Не определена обработка ошибок
- Отсутствуют implementation notes

### What happens on ambiguity

Integration Architect:
1. Уточняет детали интеграций
2. Дополняет контракты данных
3. Уточняет обработку ошибок
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют спецификации**: Создание спецификаций интеграций
- **Отсутствуют контракты**: Определение контрактов данных
- **Отсутствует обработка ошибок**: Определение обработки ошибок

---

## 12. Implementation Engineer → Verification Agent

### Required inputs

- **Реализованные компоненты**
- **Unit тесты**
- **Документация кода**
- **Артефакты реализации**
- **Спецификации от архитекторов**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "verification_package": {
      "type": "object",
      "properties": {
        "implemented_components": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component_name": {"type": "string"},
              "implementation_reference": {"type": "string"},
              "test_reference": {"type": "string"},
              "documentation_reference": {"type": "string"}
            }
          }
        },
        "test_artifacts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "test_type": {"type": "string", "enum": ["unit", "integration", "e2e"]},
              "test_reference": {"type": "string"},
              "coverage": {"type": "number"}
            }
          }
        },
        "documentation": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "doc_type": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "specification_references": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "spec_type": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        }
      }
    },
    "verification_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "component_type": {"type": "string"},
        "verification_type": {"type": "string", "enum": ["code_review", "architecture_check", "compliance_check"]}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Реализованные компоненты предоставлены | ☐ |
| 2 | Для каждого компонента есть тесты | ☐ |
| 3 | Покрытие тестами ≥ 80% | ☐ |
| 4 | Документация кода присутствует | ☐ |
| 5 | Ссылки на спецификации предоставлены | ☐ |
| 6 | Все ссылки валидны | ☐ |
| 7 | Контекст верификации определён | ☐ |
| 8 | Тип верификации указан | ☐ |

### Rejection reasons

- Отсутствие реализованных компонентов
- Отсутствие тестов для компонентов
- Покрытие тестами < 80%
- Отсутствие документации кода
- Не предоставлены ссылки на спецификации
- Невалидные ссылки на артефакты

### What happens on ambiguity

Implementation Engineer:
1. Уточняет список компонентов
2. Дополняет тесты при необходимости
3. Предоставляет документацию
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют компоненты**: Уведомление Build Orchestrator
- **Отсутствуют тесты**: Запрос на создание тестов
- **Отсутствует документация**: Запрос на создание документации

---

## 13. Implementation Engineer → Test Engineer

### Required inputs

- **Реализованные компоненты**
- **Существующие unit тесты**
- **Спецификации компонентов**
- **Требования к тестированию**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "testing_package": {
      "type": "object",
      "properties": {
        "components_to_test": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component_name": {"type": "string"},
              "implementation_reference": {"type": "string"},
              "existing_tests": {"type": "array", "items": {"type": "string"}},
              "test_requirements": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "specifications": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "spec_type": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "test_requirements": {
          "type": "object",
          "properties": {
            "test_types": {"type": "array", "items": {"type": "string"}},
            "coverage_threshold": {"type": "number"},
            "critical_paths": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "testing_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "priority": {"type": "string"},
        "deadline": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Компоненты для тестирования определены | ☐ |
| 2 | Реализация компонентов доступна | ☐ |
| 3 | Существующие тесты перечислены | ☐ |
| 4 | Спецификации предоставлены | ☐ |
| 5 | Требования к типам тестов указаны | ☐ |
| 6 | Порог покрытия определён | ☐ |
| 7 | Критические пути указаны | ☐ |
| 8 | Контекст тестирования предоставлен | ☐ |

### Rejection reasons

- Отсутствие компонентов для тестирования
- Не предоставлены спецификации
- Не указаны требования к типам тестов
- Не определён порог покрытия
- Не указаны критические пути
- Невалидные ссылки на артефакты

### What happens on ambiguity

Implementation Engineer:
1. Уточняет требования к тестированию
2. Указывает критические пути
3. Предоставляет дополнительные спецификации
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют компоненты**: Уведомление Build Orchestrator
- **Отсутствуют спецификации**: Запрос к архитекторам
- **Отсутствуют требования**: Уточнение требований

---

## 14. Verification Agent → Implementation Engineer (при возврате на исправление)

### Required inputs

- **Отчёт о проверке**
- **Список проблем**
- **Рекомендации**
- **Оценка качества**
- **Конкретные шаги для исправления**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "feedback_package": {
      "type": "object",
      "properties": {
        "verification_report": {
          "type": "object",
          "properties": {
            "report_id": {"type": "string", "format": "uuid"},
            "timestamp": {"type": "string", "format": "date-time"},
            "overall_status": {"type": "string", "enum": ["passed", "failed", "partial"]},
            "quality_score": {"type": "number"}
          }
        },
        "issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue_id": {"type": "string", "format": "uuid"},
              "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
              "issue_type": {"type": "string"},
              "description": {"type": "string"},
              "file_reference": {"type": "string"},
              "line_number": {"type": "integer"},
              "suggested_fix": {"type": "string"}
            }
          }
        },
        "recommendations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "recommendation_id": {"type": "string", "format": "uuid"},
              "type": {"type": "string"},
              "description": {"type": "string"},
              "priority": {"type": "string"}
            }
          }
        },
        "fix_steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "step_number": {"type": "integer"},
              "action": {"type": "string"},
              "file_reference": {"type": "string"},
              "line_range": {"type": "string"}
            }
          }
        }
      }
    },
    "feedback_context": {
      "type": "object",
      "properties": {
        "original_task_id": {"type": "string", "format": "uuid"},
        "verification_type": {"type": "string"},
        "deadline": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Отчёт о проверке создан | ☐ |
| 2 | Общий статус указан | ☐ |
| 3 | Оценка качества предоставлена | ☐ |
| 4 | Список проблем составлен | ☐ |
| 5 | Для каждой проблемы указана severity | ☐ |
| 6 | Проблемы содержат file references | ☐ |
| 7 | Проблемы содержат line numbers | ☐ |
| 8 | Рекомендации предоставлены | ☐ |
| 9 | Конкретные шаги для исправления определены | ☐ |

### Rejection reasons

- Отсутствие отчёта о проверке
- Не указан общий статус
- Отсутствие списка проблем
- Проблемы не содержат file references
- Проблемы не содержат line numbers
- Отсутствие конкретных шагов для исправления

### What happens on ambiguity

Verification Agent:
1. Уточняет детали проблем
2. Дополняет конкретные шаги
3. Предоставляет дополнительные рекомендации
4. Повторно передаёт feedback

### What happens on missing artifact

- **Отсутствует отчёт**: Создание отчёта о проверке
- **Отсутствуют проблемы**: Проведение проверки и составление списка
- **Отсутствуют шаги**: Определение конкретных шагов для исправления

---

## 15. Test Engineer → Build Orchestrator (при завершении)

### Required inputs

- **Unit тесты**
- **Интеграционные тесты**
- **E2E тесты**
- **Отчёт о покрытии**
- **Результаты выполнения тестов**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "testing_completion_package": {
      "type": "object",
      "properties": {
        "test_artifacts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "test_type": {"type": "string", "enum": ["unit", "integration", "e2e"]},
              "test_reference": {"type": "string"},
              "passed": {"type": "integer"},
              "failed": {"type": "integer"},
              "total": {"type": "integer"}
            }
          }
        },
        "coverage_report": {
          "type": "object",
          "properties": {
            "overall_coverage": {"type": "number"},
            "line_coverage": {"type": "number"},
            "branch_coverage": {"type": "number"},
            "coverage_by_component": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {"type": "string"},
                  "coverage": {"type": "number"}
                }
              }
            }
          }
        },
        "test_results": {
          "type": "object",
          "properties": {
            "all_passed": {"type": "boolean"},
            "total_tests": {"type": "integer"},
            "passed_tests": {"type": "integer"},
            "failed_tests": {"type": "integer"},
            "flaky_tests": {"type": "array", "items": {"type": "string"}}
          }
        },
        "quality_assessment": {
          "type": "object",
          "properties": {
            "meets_coverage_threshold": {"type": "boolean"},
            "no_flaky_tests": {"type": "boolean"},
            "critical_paths_covered": {"type": "boolean"},
            "overall_quality": {"type": "string", "enum": ["excellent", "good", "acceptable", "needs_improvement"]}
          }
        }
      }
    },
    "completion_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "component_type": {"type": "string"},
        "completion_timestamp": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Все типы тестов предоставлены | ☐ |
| 2 | Unit тесты определены | ☐ |
| 3 | Интеграционные тесты определены | ☐ |
| 4 | E2E тесты определены | ☐ |
| 5 | Отчёт о покрытии создан | ☐ |
| 6 | Покрытие ≥ 80% | ☐ |
| 7 | Все тесты прошли | ☐ |
| 8 | Нет flaky тестов | ☐ |
| 9 | Критические пути покрыты | ☐ |

### Rejection reasons

- Отсутствие одного или нескольких типов тестов
- Покрытие < 80%
- Не все тесты прошли
- Присутствуют flaky тесты
- Критические пути не покрыты

### What happens on ambiguity

Test Engineer:
1. Дополняет недостающие тесты
2. Увеличивает покрытие
3. Исправляет failing тесты
4. Устраняет flaky тесты
5. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют unit тесты**: Создание unit тестов
- **Отсутствуют интеграционные тесты**: Создание интеграционных тестов
- **Отсутствуют E2E тесты**: Создание E2E тестов
- **Отсутствует отчёт о покрытии**: Генерация отчёта

---

## 16. Verification Agent → Platform Architect (для проверки архитектуры)

### Required inputs

- **Архитектурные решения** (ADR документы)
- **Архитектурные диаграммы**
- **Спецификации компонентов**
- **Модель безопасности**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "architecture_verification_package": {
      "type": "object",
      "properties": {
        "adr_documents": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "adr_number": {"type": "string"},
              "title": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "architecture_diagrams": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "diagram_type": {"type": "string"},
              "reference": {"type": "string"}
            }
          }
        },
        "component_specs": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component_name": {"type": "string"},
              "spec_reference": {"type": "string"}
            }
          }
        },
        "security_model": {
          "type": "object",
          "properties": {
            "model_reference": {"type": "string"},
            "authentication": {"type": "string"},
            "authorization": {"type": "string"}
          }
        }
      }
    },
    "verification_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "verification_type": {"type": "string"},
        "focus_area": {"type": "string"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | ADR документы предоставлены | ☐ |
| 2 | Архитектурные диаграммы включены | ☐ |
| 3 | Спецификации компонентов определены | ☐ |
| 4 | Модель безопасности предоставлена | ☐ |
| 5 | Все ссылки валидны | ☐ |
| 6 | Контекст верификации определён | ☐ |
| 7 | Focus area указан | ☐ |

### Rejection reasons

- Отсутствие ADR документов
- Отсутствие архитектурных диаграмм
- Не определены спецификации компонентов
- Не предоставлена модель безопасности
- Невалидные ссылки на артефакты

### What happens on ambiguity

Verification Agent:
1. Уточняет детали архитектуры
2. Запрашивает дополнительные диаграммы
3. Предоставляет спецификации
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствуют ADR документы**: Создание ADR
- **Отсутствуют диаграммы**: Создание архитектурных диаграмм
- **Отсутствуют спецификации**: Создание спецификаций компонентов

---

## 17. Verification Agent → Workflow Architect (для проверки workflows)

### Required inputs

- **Спецификация состояний workflow**
- **Диаграмма переходов**
- **Спецификация retry логики**
- **Правила эскалации**

### Output schema

```json
{
  "type": "object",
  "properties": {
    "workflow_verification_package": {
      "type": "object",
      "properties": {
        "state_specification": {
          "type": "object",
          "properties": {
            "states": {"type": "array", "items": {"type": "string"}},
            "initial_state": {"type": "string"},
            "final_states": {"type": "array", "items": {"type": "string"}},
            "transitions": {"type": "array", "items": {"type": "object"}}
          }
        },
        "transition_diagram": {
          "type": "object",
          "properties": {
            "diagram_reference": {"type": "string"},
            "format": {"type": "string"}
          }
        },
        "retry_specification": {
          "type": "object",
          "properties": {
            "max_retries": {"type": "integer"},
            "backoff_strategy": {"type": "string"},
            "retryable_errors": {"type": "array", "items": {"type": "string"}}
          }
        },
        "escalation_rules": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "condition": {"type": "string"},
              "escalation_target": {"type": "string"},
              "action": {"type": "string"}
            }
          }
        }
      }
    },
    "verification_context": {
      "type": "object",
      "properties": {
        "task_id": {"type": "string", "format": "uuid"},
        "verification_type": {"type": "string"},
        "focus_area": {"type": "string"}
      }
    }
  }
}
```

### Quality checklist

| # | Checkpoint | Status |
|---|-----------|--------|
| 1 | Спецификация состояний определена | ☐ |
| 2 | Начальное состояние указано | ☐ |
| 3 | Финальные состояния указаны | ☐ |
| 4 | Переходы определены | ☐ |
| 5 | Диаграмма переходов предоставлена | ☐ |
| 6 | Retry спецификация определена | ☐ |
| 7 | Правила эскалации указаны | ☐ |
| 8 | Все ссылки валидны | ☐ |

### Rejection reasons

- Не определены состояния workflow
- Не указано начальное состояние
- Не определены финальные состояния
- Не определены переходы
- Отсутствует диаграмма переходов
- Не определена retry спецификация
- Не указаны правила эскалации

### What happens on ambiguity

Verification Agent:
1. Уточняет состояния и переходы
2. Запрашивает дополнительные диаграммы
3. Предоставляет retry спецификацию
4. Повторно передаёт артефакты

### What happens on missing artifact

- **Отсутствует спецификация состояний**: Создание спецификации
- **Отсутствует диаграмма**: Создание диаграммы переходов
- **Отсутствует retry спецификация**: Определение retry логики

---

## Заключение

Этот документ определяет 17 Handoff Contracts между build-агентами платформы оркестрации. Каждый контракт обеспечивает:

1. **Чёткую структуру** передачи данных между агентами
2. **Валидацию** входных и выходных данных
3. **Проверку качества** артефактов
4. **Обработку исключений** и неопределённостей
5. **Процедуры возврата** на исправление

Следование этим контрактам гарантирует:
- Надёжность handoff процессов (99.9%)
- Прозрачность коммуникации между агентами
- Согласованность артефактов
- Отслеживаемость всех изменений
- Эффективное разрешение проблем

### Дополнительные ресурсы

- **SDD документация**: `docs/sdd-orchestration-platform.md`
- **Конфигурации агентов**: `.opencode/agents/`
- **State machine документация**: `docs/state-machines.md`

---

**Версия документа**: 1.0.0  
**Дата последнего обновления**: 2026-04-11  
**Статус**: Draft
