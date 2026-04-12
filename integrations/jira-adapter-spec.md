# Jira Adapter Specification

**Статус**: Draft | **Версия**: 0.1

## Назначение и область применения

Данный документ определяет спецификацию интеграции с Jira для Symphony сервиса.

**Цель**:
- Обеспечить синхронизацию задач Jira с workflow Symphony
- Предоставить стандартизированный интерфейс для работы с Jira API

**Область применения**:
- Fetch (получение) задач из Jira
- Получение текущего состояния задач
- Опциональное обновление состояния задач
- Маппинг сущностей Jira ↔ Issue entity (см. SPEC.md Section 4.1.1)

## Архитектура интеграции

### Протокол
- **Тип**: REST API
- **Базовый URL**: Конфигурируемый (по умолчанию `https://<domain>.atlassian.net/rest/api/3/`)
- **Версия API**: Jira REST API v3 (рекомендуется)

### Компоненты
```
┌─────────────────┐
│   Orchestrator  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Jira Adapter   │
│ - HTTP Client   │
│ - Normalizer    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Jira REST API  │
└─────────────────┘
```

## Требуемые операции

### 1. `fetch_candidate_issues()`
**Назначение**: Получение списка активных задач для обработки

**Параметры**:
- `project_key` (string) - ключ проекта (например: "PROJ")
- `active_states` (list of strings) - список статусов для фильтрации
- `limit` (integer) - максимальное количество задач (опционально)

**Возвращает**: Список нормализованных Issue entities

**Детали реализации**:
- Использует Jira Search API (`/rest/api/3/search`)
- Фильтрует по проекту и статусам
- Пагинация при необходимости
- Сортировка по приоритету и дате создания

### 2. `fetch_issue_states_by_ids(issue_ids)`
**Назначение**: Получение текущих состояний задач по ID

**Параметры**:
- `issue_ids` (list of strings) - список Jira Issue IDs

**Возвращает**: Map `<issue_id -> state>`

**Детали реализации**:
- Использует Jira API для batch-запроса
- Оптимизация для reconciliation (см. SPEC.md Section 8.5)

### 3. `fetch_issues_by_states(state_names)` (опционально)
**Назначение**: Получение задач в терминальных состояниях для cleanup

**Параметры**:
- `state_names` (list of strings) - список статусов

**Возвращает**: Список Issue entities

**Детали реализации**:
- Используется при startup cleanup (см. SPEC.md Section 8.6)

### 4. `update_issue_state(issue_id, new_state)` (опционально)
**Назначение**: Обновление статуса задачи

**Параметры**:
- `issue_id` (string) - ID задачи
- `new_state` (string) - новый статус

**Возвращает**: Boolean indicating success

**Детали реализации**:
- Использует Jira Transitions API
- Опциональная операция (по умолчанию отключена)

## Маппинг модели данных

### Jira → Issue Entity

| Jira поле | Issue Entity поле | Тип трансформации |
|-----------|-------------------|-------------------|
| `id` | `id` | Прямое маппинг |
| `key` | `identifier` | Прямое маппинг |
| `fields.summary` | `title` | Прямое маппинг |
| `fields.description` | `description` | Прямое маппинг |
| `fields.priority.id` | `priority` | Преобразование в integer |
| `fields.status.name` | `state` | Прямое маппинг |
| `fields.labels` | `labels` | Lowercase нормализация |
| `fields.created` | `created_at` | ISO-8601 parsing |
| `fields.updated` | `updated_at` | ISO-8601 parsing |
| `url` | `url` | Конструкция из baseURL + key |

### Blockers маппинг
- Jira Issue Links (relation type: "is blocked by")
- Трансформация в формат `blocked_by` из SPEC.md Section 4.1.1

## Аутентификация

### Поддерживаемые методы

#### 1. API Token (рекомендуется)
- **Метод**: HTTP Basic Auth
- **Формат**: `Authorization: Basic <base64(email:api_token)>`
- **Конфигурация**:
  - `tracker.api_key`: API токен или `$JIRA_API_TOKEN`
  - `tracker.username`: Email пользователя или `$JIRA_USERNAME`
  - `tracker.endpoint`: Base URL Jira инстанса

#### 2. OAuth 2.0
- **Метод**: OAuth 2.0 Bearer Token
- **Формат**: `Authorization: Bearer <access_token>`
- **Конфигурация**:
  - `tracker.oauth_client_id`: Client ID
  - `tracker.oauth_client_secret`: Client Secret
  - `tracker.oauth_refresh_token`: Refresh token
  - Автоматическое обновление токена

### Проверка аутентификации
- Валидация при запуске сервиса
- Повторная попытка при 401/403 ошибках
- Логирование failed auth attempts

## Обработка ошибок

### Категории ошибок

| Категория | Описание | Обработка |
|-----------|-----------|-----------|
| `jira_network_error` | Ошибки сети/timeout | Retry с backoff |
| `jira_auth_error` | Ошибка аутентификации | Лог + skip dispatch |
| `jira_rate_limit` | Rate limit exceeded | Retry с backoff |
| `jira_invalid_response` | Неверный формат ответа | Лог + skip |
| `jira_not_found` | Задача не найдена | Лог + skip |
| `jira_permission_denied` | Нет прав доступа | Лог + skip |
| `jira_server_error` | Ошибка сервера (5xx) | Retry с backoff |

### Retry политика
- Сетевые ошибки: exponential backoff
- Rate limits: retry после `Retry-After` header
- Auth errors: немедленный failure (no retry)

## Конфигурация

### WORKFLOW.md front matter
```yaml
tracker:
  kind: "jira"
  endpoint: "https://company.atlassian.net"
  api_key: "$JIRA_API_TOKEN"
  username: "$JIRA_USERNAME"
  project_key: "PROJ"
  active_states: ["Todo", "In Progress"]
  terminal_states: ["Closed", "Done"]
```

## TODO

### GraphQL адаптер для Linear
- **Ссылка**: SPEC.md Section 11
- **Задача**: Реализовать GraphQL адаптер для Linear по аналогии с Jira REST адаптером
- **Детали**:
  - Использовать Linear GraphQL API
  - Реализовать операции: `fetch_candidate_issues()`, `fetch_issue_states_by_ids()`, `fetch_issues_by_states()`
  - Нормализовать ответы в Issue entity
  - Поддержать пагинацию
  - Обработка ошибок Linear GraphQL API

### Дополнительные задачи
- [ ] Определить полный список Jira полей для маппинга
- [ ] Реализовать поддержку custom fields
- [ ] Добавить поддержку Jira Webhooks для real-time updates
- [ ] Определить стратегию обработки Jira Workflow transitions
- [ ] Реализовать unit tests для Jira adapter
- [ ] Добавить интеграционные тесты с Jira API mock server
- [ ] Определить ограничения на количество concurrent API calls
- [ ] Реализовать caching layer для уменьшения API calls

## Ссылки

- SPEC.md: Symphony Service Specification
- SPEC.md Section 4.1.1: Issue Entity
- SPEC.md Section 11: Issue Tracker Integration Contract
- Jira REST API Documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
