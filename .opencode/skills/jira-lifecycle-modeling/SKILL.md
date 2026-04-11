---
name: jira-lifecycle-modeling
description: Моделирование Jira lifecycle для бизнес-процессов
license: MIT
compatibility:
  opencode: ">=1.0.0"
metadata:
  author: Build Team
  version: 1.0.0
  tags: [jira, integration, workflow]
allowed-tools:
  - read
  - write
---

# Jira Lifecycle Modeling

## Описание
Навык моделирования интеграции с Jira API для бизнес-процессов. Включает маппинг статусов Jira, определение переходов, конфигурацию полей и валидацию workflow.

## Когда использовать
- Интеграция с Jira для управления задачами
- Синхронизация статусов задач между системами
- Автоматизация переходов задач
- Создание кастомных workflow в Jira

## Когда НЕ использовать
- Для систем без Jira интеграции
- Для написания кода интеграции
- Для простого импорта/экспорта задач

## Входные данные
- Документация Jira API
- Описание бизнес-процесса
- Текущая конфигурация Jira (если есть)
- Требования к интеграции

## Выходные данные
- Маппинг Jira lifecycle
- Определение статусов и их соответствия
- Правила переходов
- Спецификация полей для синхронизации
- Документация API интеграции

## Зависимости
- state-machine-design - для моделирования workflow

## Режимы отказа
- Ограничения Jira API
- Несоответствие возможностям Jira
- Конфликты с существующими workflow
- Ограничения прав доступа

## Шаблоны и чек-листы

### Шаблон Jira Lifecycle Mapping
```markdown
## Status Mapping
| System Status | Jira Status | Description |
|---------------|--------------|-------------|
| TODO          | To Do        | Задачи в работе|
| IN_PROGRESS   | In Progress  | Активная работа|
| DONE          | Done         | Завершено     |

## Transitions
| From Status | To Status | Trigger | Conditions |
|-------------|----------|---------|------------|
| To Do | In Progress | start_work | assignee assigned |
| In Progress | Done | complete | all checks passed |

## Custom Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| custom_123 | Text | Yes | Идентификатор |
```

### Чек-лист
- [ ] Jira поля замаппированы с внутренними сущностями
- [ ] Переходы определены с триггерами
- [ ] Workflow валидирован
- [ ] Права доступа учтены
- [ ] Обработка ошибок определена
- [ ] Custom fields задокументированы

## Usage
```json
{
  "tool": "skill",
  "name": "jira-lifecycle-modeling"
}
```