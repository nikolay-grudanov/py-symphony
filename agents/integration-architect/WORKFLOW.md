# Integration Architect - Рабочий процесс

## Обзор процесса

Integration Architect следует workflow: анализ требований → проектирование интерфейсов → определение контрактов → документация спецификаций.

## Шаг 1: Анализ требований

### Изучение входных данных

Анализ входящих требований от build-orchestrator:

```
## Анализ требований к интеграции

**Задача**: [ID и описание]
**Внешняя система**: [Имя сервиса]
**Тип интеграции**: [push/pull/bidirectional]

**Функциональные требования**:
- [ ] Требование 1
- [ ] Требование 2

**Non-functional требования**:
- Performance: [latency/throughput]
- Availability: [%]
- Security: [requirements]
- Rate limits: [если есть]

**Связанные документы**:
- ADR: [ссылки]
- SPEC.md: [разделы]
```

### Изучение внешней спецификации

Изучение документации внешней системы:

- Аутентификация и авторизация
- Доступные endpoints/методы
- Форматы запросов и ответов
- Rate limiting политика
- Error handling

**Результаты анализа**:
```
## Внешняя спецификация: [Название]

**Документация**: [ссылка]
**Version**: [версия]

**Authentication**:
- Метод: [OAuth2/API Key/Basic]
- Scopes: [список]

**Rate limits**:
- Endpoint limits: [описание]
- Headers: [X-RateLimit-*]

**Available endpoints**:
- [ ] [Endpoint 1]: [описание]
- [ ] [Endpoint 2]: [описание]
```

## Шаг 2: Проектирование интерфейсов

### Выбор протокола интеграции

На основе требований выбрать подходящий протокол:

| Сценарий | Рекомендуемый протокол | Обоснование |
|----------|------------------------|-------------|
| Простые CRUD операции | REST | Simplicity, wide support |
| Сложные запросы | GraphQL | Flexible queries |
| High-performance коммуникация | gRPC | Binary, low latency |
| Асинхронная обработка | Message Queue | Decoupling, reliability |
| Event-driven | Webhooks | Real-time events |

### Проектирование структуры данных

Определить формат данных:

**Для REST API**:
```
## API Contract: [Название]

**Base URL**: [url]
**Version**: [v1/v2]

**Endpoints**:

### POST /api/v1/resources
Создание ресурса

**Request**:
```json
{
  "field1": "string",
  "field2": "number",
  "metadata": {
    "key": "value"
  }
}
```

**Response** (200):
```json
{
  "id": "uuid",
  "field1": "string",
  "field2": "number",
  "metadata": {
    "key": "value",
    "created_at": "ISO8601"
  }
}
```

**Errors**:
- 400: Bad Request
- 401: Unauthorized
- 429: Too Many Requests
```

**Для GraphQL**:
```
## GraphQL Schema

```graphql
type Query {
  resource(id: ID!): Resource
  resources(limit: Int = 10): [Resource!]!
}

type Mutation {
  createResource(input: CreateResourceInput!): Resource!
  updateResource(id: ID!, input: UpdateResourceInput!): Resource!
}

type Resource {
  id: ID!
  field1: String!
  field2: Int!
  metadata: Metadata!
}

input CreateResourceInput {
  field1: String!
  field2: Int!
  metadata: MetadataInput
}
```
```

**Для Message Queue**:
```
## Message Contract

**Exchange**: [имя]
**Queue**: [имя]
**Routing key**: [ключ]

**Message format**:
```json
{
  "type": "resource.created",
  "timestamp": "ISO8601",
  "data": {
    "id": "uuid",
    "field1": "value"
  }
}
```

**Message types**:
- resource.created
- resource.updated
- resource.deleted
```

## Шаг 3: Определение контрактов

### Детализация контракта

Создать детальный контракт с примерами:

```
## Детальный контракт: [Название]

### 1. Authentication
**Method**: OAuth2 Bearer token
**Token endpoint**: [url]
**Scopes**: [список]
**Refresh logic**: [описание]

### 2. Data transformation
**Mapping rules**:
- external_field1 → internal_field1
- external_field2 → internal_field2 (transform: [описание])

**Normalization**:
- Даты: ISO8601 → UTC datetime
- Numbers: string → float (validate range)
- Enums: string → enum (validate values)

### 3. Error handling
**Retry policy**:
- 429: exponential backoff (1s, 2s, 4s, 8s, 16s)
- 500: exponential backoff (2s, 4s, 8s)

**Circuit breaker**:
- Threshold: 5 consecutive failures
- Timeout: 60s
- Recovery: half-open

**Non-retryable**:
- 400: Bad Request - validate input
- 401: Unauthorized - refresh token
- 403: Forbidden - check permissions

### 4. Rate limiting
**Client limits**:
- Burst: 100 requests per minute
- Sustained: 1000 requests per hour

**Backoff strategy**:
- On 429: Retry-After header
- Default: 5 seconds

### 5. Monitoring
**Metrics**:
- request_count
- request_latency
- error_count (by error type)
- circuit_breaker_state

**Logging**:
- Request/response bodies (debug level)
- Errors (error level)
- Rate limit hits (warn level)
```

### Создание ADR

Создать Architecture Decision Record:

```
# ADR-XXX: [Название контракта интеграции]

## Статус
Accepted

## Контекст
[Описание требований к интеграции]

## Рассмотренные альтернативы

### Вариант 1: REST API
**Преимущества**:
- [преимущество 1]
- [преимущество 2]

**Недостатки**:
- [недостаток 1]
- [недостаток 2]

### Вариант 2: GraphQL
[аналогично]

## Решение
[Выбранный подход и обоснование]

## Последствия

### Положительные
- [последствие 1]
- [последствие 2]

### Отрицательные
- [последствие 1]
- [последствие 2]

## Соответствие SPEC.md
- Раздел X.Y: [требование]

## Ссылки
- Внешняя спецификация: [url]
- Связанные ADR: [ссылки]
```

## Шаг 4: Документация спецификаций

### Создание OpenAPI спецификации (для REST)

```yaml
openapi: 3.0.0
info:
  title: [Название API]
  version: 1.0.0

servers:
  - url: [base url]

security:
  - BearerAuth: []

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer

paths:
  /resources:
    post:
      summary: Create resource
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResource'
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'

components:
  schemas:
    CreateResource:
      type: object
      required: [field1, field2]
      properties:
        field1:
          type: string
        field2:
          type: integer

    Resource:
      type: object
      properties:
        id:
          type: string
          format: uuid
        field1:
          type: string
```

### Создание GraphQL schema (для GraphQL)

```graphql
"""
Модуль для работы с ресурсами
"""
module ResourceAPI {
  """
  Запрос ресурса по ID
  """
  resource(id: ID!): Resource

  """
  Список ресурсов
  """
  resources(
    limit: Int = 10
    offset: Int = 0
  ): ResourceConnection!
}

"""
Ресурс
"""
type Resource {
  """
  Уникальный идентификатор
  """
  id: ID!

  """
  Поле 1
  """
  field1: String!

  """
  Поле 2
  """
  field2: Int!

  """
  Метаданные
  """
  metadata: Metadata!
}

"""
Метаданные ресурса
"""
type Metadata {
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### Создание HOWTO guide

```
# Integration Guide: [Название]

## Overview
[Краткое описание интеграции]

## Prerequisites
- API ключ: [как получить]
- Required permissions: [список]
- Rate limits: [описание]

## Authentication
[Детальная аутентификация]

## Usage Examples

### Create Resource
```python
from client import ApiClient

client = ApiClient(api_key="your-key")
resource = client.create_resource(
    field1="value1",
    field2=42
)
print(resource.id)
```

### Handle Errors
```python
try:
    resource = client.create_resource(...)
except RateLimitError:
    # Implement retry
    pass
except AuthenticationError:
    # Refresh token
    pass
```

## Error Handling
[Полное описание error handling]

## Best Practices
- [совет 1]
- [совет 2]
```

## Шаг 5: Ревизия и согласование

### Self-review

Проверить контракт на полноту:

- [ ] Все requirements покрыты
- [ ] Все edge cases рассмотрены
- [ ] Error handling полностью определен
- [ ] Примеры предоставлены
- [ ] Документация полная и ясная

### Request feedback

Запросить feedback от соответствующих агентов:

```
## Запрос feedback по контракту: [Название]

**Контракт**: [ссылка]
**ADR**: [ссылка]

**Feedback нужен от**:
- implementation-engineer: реализуемость
- test-engineer: тестируемость
- verification-agent: верифицируемость

**Вопросы**:
1. Все ли requirements покрыты?
2. Есть ли missing edge cases?
3. Error handling адекватен?
4. Документация ясна?

**Дедлайн**: [дата]
```

### Incorporate feedback

Внедрить полученные комментарии:

```
## Обновление контракта: [Название]

**Feedback от**: [агент]
**Обновления**:
- [ ] Изменение 1: [описание]
- [ ] Изменение 2: [описание]

**Версия контракта**: v1.1
**Дата**: [дата]
```

## Завершение

### Final checklist

Перед завершением:

- [ ] Все requirements покрыты
- [ ] Контракт детализирован
- [ ] Error handling определен
- [ ] Примеры предоставлены
- [ ] ADR создан и approved
- [ ] Документация создана
- [ ] Feedback обработан

### Handoff preparation

Подготовить передачу implementation-engineer:

```
## Handoff: Контракт интеграции [Название]

**Контракт**: [ссылка]
**ADR**: [ссылка]
**Спецификация**: [ссылка]
**Примеры**: [ссылка]

**Важно**:
- [ ] Особенности error handling
- [ ] Rate limiting политика
- [ ] Authentication flow
- [ ] Known limitations

**Следующий шаг**: Реализация контракта
```
