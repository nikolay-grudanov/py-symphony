# Integration Architect - Handoff контракты

## Обзор

Handoff контракты определяют правила передачи интеграционных контрактов между агентами.

## Общие принципы handoff

### Правила передачи
1. Контракт полностью определен и задокументирован
2. ADR создан и approved
3. Все edge cases рассмотрены
4. Error handling стратегия определена
5. Примеры использования предоставлены

### Формат передачи
Стандартный формат handoff:

```
## Handoff: Контракт интеграции [Название]

**От**: integration-architect
**Кому**: implementation-engineer / verification-agent

**Что было спроектировано**:
- [ ] ADR для контракта интеграции
- [ ] Детальная спецификация контракта
- [ ] Error handling стратегия
- [ ] Примеры использования

**Артефакты**:
- [ ] ADR: [ссылка]
- [ ] Спецификация (OpenAPI/GraphQL/Protobuf): [ссылка]
- [ ] HOWTO guide: [ссылка]
- [ ] Примеры кода: [ссылка]

**Важные аспекты**:
- Authentication flow: [описание]
- Error handling: [описание]
- Rate limiting: [описание]
- Known limitations: [если есть]

**Следующие шаги**:
1. [Шаг 1]
2. [Шаг 2]

**QA Gate**: [Что нужно проверить]
**Дедлайн**: [Дата]
```

## Входные handoff контракты

### От build-orchestrator

#### Входные требования для проектирования контракта

**Что получает integration-architect**:
- Описание интеграции (какую внешнюю систему подключаем)
- Функциональные требования (что нужно от интеграции)
- Non-functional требования (performance, security, reliability)
- Связанные ADR и спецификации

**Пример**:
```
## Задача для Integration Architect

**Тип**: Интеграция
**Описание**: Спроектировать контракт интеграции с Linear API
**Требования**:
- Создавать issues в Linear проектах
- Получать статус issues
- Обновлять issues
- Получать уведомления об изменениях

**Non-functional**:
- Max latency: 200ms
- Availability: 99.9%
- Authentication: OAuth2
- Rate limit: 100 req/min

**Контекст**:
- SPEC.md раздел 5.3
- Связанные задачи: #123, #124
```

#### Критерии принятия задачи

Интеграционный архитектор принимает задачу если:
- [ ] Требования ясны и полные
- [ ] Внешняя система определена
- [ ] Ограничения (rate limits, auth) известны
- [ ] Связанные документы доступны

### От platform-architect / agent-runtime-architect

#### Архитектурный контекст

**Что получает integration-architect**:
- ADR для платформенной архитектуры
- Требования к интеграциям с платформенной точки зрения
- Runtime архитектура для интеграций

**Пример**:
```
## Архитектурный контекст для интеграции

**ADR**: ADR-010: Микросервисная архитектура
**Требования**:
- Все интеграции через dedicated integration layer
- Circuit breaker для всех внешних вызовов
- Retry с exponential backoff
- Observability (metrics, logging, tracing)

**Runtime спецификация**: docs/runtime/integrations.md
```

## Выходные handoff контракты

### К implementation-engineer

#### Передача контракта для реализации

**Что передает integration-architect**:
- ADR с детальным описанием контракта интеграции
- Спецификация (OpenAPI, GraphQL schema, Protobuf)
- Error handling стратегия
- Примеры использования

**Пример handoff**:
```
## Handoff: Контракт интеграции Linear API

**От**: integration-architect
**Кому**: implementation-engineer

**ADR**: ADR-025: Linear API Integration Contract
**Спецификация**: docs/integrations/linear/openapi.yaml

**Контракт**:

### Authentication
- Method: OAuth2
- Token endpoint: https://api.linear.app/oauth/token
- Scopes: read, write, admin

### Endpoints
- POST /graphql: GraphQL endpoint
- Webhooks для issue events

### Data structures
- Issue type, status, priority
- Project и team mappings
- Custom fields handling

### Error handling
- 401: Refresh token
- 429: Exponential backoff (max 5 attempts)
- 5xx: Circuit breaker (threshold: 5 failures)

### Rate limiting
- 100 requests per 60 seconds
- Respect X-RateLimit-Reset header

**Артефакты**:
- [ ] ADR: docs/adr/025-linear-integration.md
- [ ] OpenAPI: docs/integrations/linear/openapi.yaml
- [ ] GraphQL schema: docs/integrations/linear/schema.graphql
- [ ] HOWTO guide: docs/integrations/linear/howto.md
- [ ] Examples: examples/integrations/linear/

**Ожидаемая реализация**:
- [ ] Authentication flow (OAuth2)
- [ ] GraphQL client
- [ ] Error handling (retry, circuit breaker)
- [ ] Rate limiting enforcement
- [ ] Webhook handler
- [ ] Logging и metrics

**QA Gate**:
- [ ] Код соответствует спецификации
- [ ] Error handling реализован согласно ADR
- [ ] Unit tests для всех методов
- [ ] Integration tests с Linear API
- [ ] Документация API создана

**Дедлайн**: 2024-04-20
```

#### Критерии отклонения реализации

Implementation-engineer отклоняет контракт если:
- [ ] Спецификация неоднозначна
- [ ] Протокол или формат недоступен в выбранном стеке
- [ ] External API не поддерживает требуемую функциональность
- [ ] Error handling стратегия нереализуема

### К verification-agent

#### Передача контракта для верификации

**Что передает integration-architect**:
- Контракт интеграции для валидации
- ADR с требованиями
- Спецификации

**Пример handoff**:
```
## Handoff: Валидация контракта Linear API

**От**: integration-architect
**Кому**: verification-agent

**Что нужно проверить**:
- [ ] Контракт покрывает все бизнес-требования
- [ ] Error handling стратегия полная
- [ ] Все edge cases рассмотрены
- [ ] Примеры корректны
- [ ] Спецификация соответствует внешней API

**Артефакты для проверки**:
- [ ] ADR-025
- [ ] OpenAPI спецификация
- [ ] HOWTO guide
- [ ] Примеры использования

**Ссылки на требования**:
- SPEC.md раздел 5.3
- Issue #123

**QA Gate**:
- [ ] Все бизнес-требования покрыты
- [ ] Нет пропущенных edge cases
- [ ] Error handling адекватен
- [ ] Спецификация соответствует внешней API

**Ожидаемый результат**:
- Отчет о верификации с findings
- Список issues если есть
- Approval если контракт валиден
```

#### Критерии отклонения контракта

Verification-agent отклоняет контракт если:
- [ ] Требования не покрыты полностью
- [ ] Edge cases не рассмотрены
- [ ] Error handling недостаточный
- [ ] Спецификация не соответствует внешней API
- [ ] Примеры некорректны

### К test-engineer

#### Передача требований к тестированию

**Что передает integration-architect**:
- Контракт интеграции
- Test scenarios для edge cases
- Error handling стратегии для тестирования

**Пример handoff**:
```
## Handoff: Тестовые требования Linear API Integration

**От**: integration-architect
**Кому**: test-engineer

**Что нужно протестировать**:
- [ ] Authentication flow (token acquisition, refresh)
- [ ] CRUD operations с Linear API
- [ ] Error handling (retry logic, circuit breaker)
- [ ] Rate limiting enforcement
- [ ] Webhook handling

**Test scenarios**:
- Happy path: create/read/update/delete issue
- Error path: 401 unauthorized → token refresh
- Error path: 429 rate limit → exponential backoff
- Error path: 5xx server error → circuit breaker
- Edge case: simultaneous requests
- Edge case: malformed responses

**Mock API specs**:
- Success responses
- Error responses (400, 401, 429, 500)
- Rate limit headers

**Артефакты**:
- [ ] ADR-025
- [ ] OpenAPI спецификация
- [ ] Test scenarios document

**Ожидаемый результат**:
- Unit tests для всех методов
- Integration tests с Linear API
- Error handling tests
- Performance tests (rate limiting)
- Mock API для локального тестирования

**QA Gate**:
- [ ] Test coverage > 80%
- [ ] Все сценарии протестированы
- [ ] Error handling verified
- [ ] Performance benchmarks met
```

## Handoff между архитекторами

### С platform-architect

#### Получение архитектурного контекста

**Что получает integration-architect**:
- Платформенная архитектура
- Требования к интеграциям (patterns, constraints)
- Runtime архитектура

#### Передача интеграционных требований

**Что передает integration-architect**:
- Требования к integration layer
- Observability требования для интеграций
- Circuit breaker и retry patterns

### С agent-runtime-architect

#### Получение runtime контекста

**Что получает integration-architect**:
- Runtime архитектура для интеграций
- Lifecycle management для интеграционных компонентов
- Deployment спецификации

#### Передача runtime требований

**Что передает integration-architect**:
- Runtime требования для интеграций
- Health check спецификации
- Metrics и logging спецификация

## Специфичные handoff сценарии

### 1. Изменение внешней API

**Когда**: Внешняя система изменила свой API

**Процесс**:
```
## Обновление контракта: [Название]

**Причина**: External API change
**Внешняя система**: [Имя]
**Breaking change**: [да/нет]

**Изменения**:
- [ ] Изменение 1: [описание]
- [ ] Изменение 2: [описание]

**Влияние**:
- Breaking: [описание если есть]
- Deprecated: [список]
- New features: [список]

**Действия**:
- [ ] Обновить ADR
- [ ] Обновить спецификацию
- [ ] Обновить документацию
- [ ] Handoff implementation-engineer

**Дедлайн для обновления**: [дата]
```

### 2. Добавление нового фичи к существующей интеграции

**Когда**: Требуется новая функциональность

**Процесс**:
```
## Расширение контракта: [Название]

**Новая фича**: [описание]
**ADR**: [ссылка на новый ADR или update существующего]

**Изменения**:
- [ ] Добавлены новые endpoints: [список]
- [ ] Добавлены новые типы данных: [список]
- [ ] Обновлен error handling: [описание]

**Backwards compatibility**: [да/нет]

**Артефакты**:
- [ ] Обновленный ADR
- [ ] Обновленная спецификация
- [ ] Новые примеры

**Handoff to**: implementation-engineer
```

### 3. Удаление интеграции

**Когда**: Интеграция больше не нужна

**Процесс**:
```
## Удаление контракта: [Название]

**Причина**: [описание]
**ADR**: ADR для deprecation

**Действия**:
- [ ] Отметить контракт как deprecated
- [ ] Создать migration guide (если есть замена)
- [ ] Handoff implementation-engineer для removal

**Дедлайн для удаления**: [дата]
```

## Handoff формат для критических ситуаций

### 1. Критическая проблема безопасности

```
## 🚨 🚨 SECURITY ISSUE IN CONTRACT 🚨 🚨

**Контракт**: [Название]
**Внешняя система**: [Имя]
**Проблема**: [Описание уязвимости]
**Влияние**: [Как это влияет на безопасность]

**Mitigation required**:
- [ ] Действие 1
- [ ] Действие 2

**Требуемое действие**: [от кого]
**Приоритет**: CRITICAL
**Дедлайн**: [максимальное время]
```

### 2. Блокирующая проблема в контракте

```
## 🚨 BLOCKING ISSUE IN CONTRACT

**Контракт**: [Название]
**Проблема**: [Описание]
**Влияние**: [Что блокирует]

**Временное решение**: [если есть]
**Требуемое действие**: [от кого]
**Дедлайн**: [дата]
```

## Обратная связь и итерации

### Обработка feedback от implementation-engineer

```
## Feedback от implementation-engineer

**Контракт**: [Название]
**От**: implementation-engineer

**Комментарии**:
- [ ] Комментарий 1: [что нужно изменить]
- [ ] Комментарий 2: [что нужно изменить]

**Решение**:
- [ ] Принято: [действие]
- [ ] Отклонено: [обоснование]
- [ ] Требует обсуждения: [причина]

**Обновление контракта**: [ссылка на обновление]
**Версия**: v1.X
```

### Обработка feedback от verification-agent

```
## Feedback от verification-agent

**Контракт**: [Название]
**От**: verification-agent

**Findings**:
- [ ] Finding 1: [описание]
- [ ] Finding 2: [описание]

**Severity**:
- [ ] Critical
- [ ] High
- [ ] Medium
- [ ] Low

**Требуемые исправления**:
- [ ] Исправление 1
- [ ] Исправление 2

**Обновление контракта**: [ссылка на обновление]
**Версия**: v1.Y
```
