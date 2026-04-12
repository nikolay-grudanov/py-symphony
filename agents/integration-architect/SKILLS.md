# Integration Architect - Навыки (Skills)

## Обзор

Integration Architect использует следующие навыки для эффективного проектирования контрактов интеграции.

## Навык: API Design

### Описание
Способность проектировать ясные, полные и поддерживаемые API контракты для интеграций с внешними системами.

### Компоненты навыка

#### 1. RESTful API design
- Ресурс-oriented подход
- Правильное использование HTTP методов (GET, POST, PUT, DELETE, PATCH)
- Status codes (2xx success, 4xx client error, 5xx server error)
- Versioning стратегия (URL versioning, header versioning)
- Pagination, filtering, sorting

#### 2. GraphQL schema design
- Типизация и типы (scalar, object, enum, interface, union)
- Queries, mutations, subscriptions
- Arguments и input types
- Directives для авторизации и кэширования
- Schema stitching для объединения схем

#### 3. gRPC protobuf design
- Message definition (syntax 3)
- Service definition
- Field rules (required, optional, repeated)
- Enum types и oneof
- Field numbering для backwards compatibility

#### 4. API documentation
- OpenAPI/Swagger спецификация
- GraphQL schema documentation
- Примеры запросов и ответов
- Error codes и handling

### Примеры использования

**RESTful API**:
```yaml
# OpenAPI specification
paths:
  /resources:
    get:
      summary: List resources
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
```

**GraphQL**:
```graphql
type Query {
  resources(limit: Int = 10, offset: Int = 0): ResourceConnection!
}

type ResourceConnection {
  nodes: [Resource!]!
  totalCount: Int!
  pageInfo: PageInfo!
}
```

### Best Practices

- [ ] Использовать существующие стандарты (OpenAPI, GraphQL)
- [ ] Документировать все endpoints и types
- [ ] Предоставлять примеры запросов/ответов
- [ ] Определять error handling стратегию
- [ ] Backwards compatibility для versioned APIs

## Навык: Data Transformation

### Описание
Способность определять правила маппинга и трансформации данных между внешними и внутренними системами.

### Компоненты навыка

#### 1. Field mapping
- Direct mapping (field1 → field1)
- Transformation mapping (externalField → internalField)
- Aggregation mapping (multiple external fields → single internal)
- Split mapping (single external field → multiple internal)

#### 2. Type conversion
- String → Int/Float
- String → DateTime (ISO8601, RFC2822)
- Enum mapping (string values → enum constants)
- Boolean mapping (true/false, yes/no, 1/0)

#### 3. Data normalization
- DateTime нормализация (timezone conversion)
- Number нормализация (precision, rounding)
- String нормализация (trimming, case folding)
- Null handling (null, empty string, default values)

#### 4. Validation
- Required fields
- Field constraints (min/max, regex)
- Business rules validation
- Cross-field validation

### Примеры использования

**Field mapping**:
```yaml
mapping:
  external.id: -> internal.resource_id
  external.name: -> internal.display_name
  external.created_at: -> internal.created_utc (convert to UTC)
  external.status:
    OPEN -> internal.Status.OPEN
    CLOSED -> internal.Status.CLOSED
    IN_PROGRESS -> internal.Status.IN_PROGRESS
```

**Type conversion**:
```python
def convert_external_to_internal(external: ExternalData) -> InternalData:
    return InternalData(
        resource_id=UUID(external.id),
        display_name=external.name.strip(),
        created_utc=parse_iso8601(external.created_at),
        status=map_status(external.status)
    )
```

### Best Practices

- [ ] Документировать все маппинги
- [ ] Обрабатывать null/empty values
- [ ] Валидировать входные данные
- [ ] Логировать transformation errors
- [ ] Предоставлять roundtrip возможности

## Навык: Error Handling Design

### Описание
Способность проектировать комплексные стратегии обработки ошибок для интеграций с внешними системами.

### Компоненты навыка

#### 1. Error classification
- Retryable errors (429, 500, 502, 503, 504)
- Non-retryable errors (400, 401, 403, 404)
- Transient errors (timeout, connection refused)
- Permanent errors (invalid data, permission denied)

#### 2. Retry strategies
- Exponential backoff: delay = base * 2^attempt
- Linear backoff: delay = base * attempt
- Fixed delay: delay = constant
- Jitter: delay = backoff * random(0.5, 1.5)

#### 3. Circuit breaker
- Threshold: количество consecutive failures
- Timeout: время до попытки восстановления
- States: closed, open, half-open
- Reset: логика возвращения в closed state

#### 4. Fallback mechanisms
- Alternative endpoints
- Cached data
- Default values
- Graceful degradation

### Примеры использования

**Retry with exponential backoff**:
```python
def retry_request():
    max_attempts = 5
    base_delay = 1  # seconds

    for attempt in range(max_attempts):
        try:
            return make_request()
        except RateLimitError:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt)
            sleep(delay)
```

**Circuit breaker**:
```python
class CircuitBreaker:
    def __init__(self, threshold=5, timeout=60):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.state = 'closed'  # closed, open, half-open

    def call(self, func):
        if self.state == 'open':
            if time() - self.last_failure > self.timeout:
                self.state = 'half-open'
            else:
                raise CircuitBreakerOpenError()

        try:
            result = func()
            if self.state == 'half-open':
                self.state = 'closed'
                self.failures = 0
            return result
        except Exception:
            self.failures += 1
            self.last_failure = time()
            if self.failures >= self.threshold:
                self.state = 'open'
            raise
```

### Best Practices

- [ ] Классифицировать ошибки (retryable/non-retryable)
- [ ] Использовать exponential backoff с jitter
- [ ] Настраивать circuit breaker thresholds
- [ ] Логировать все ошибки с контекстом
- [ ] Предоставлять fallback механизмы

## Навык: Rate Limiting Design

### Описание
Способность проектировать стратегии для управления request rate и избежания rate limiting от внешних систем.

### Компоненты навыка

#### 1. Rate limit types
- Per-window limits (X requests per Y time)
- Burst limits (max concurrent requests)
- Sliding window limits
- Token bucket algorithm

#### 2. Enforcement strategies
- In-memory counters
- Distributed counters (Redis)
- Rate limiting middleware
- Backpressure

#### 3. Rate limit detection
- HTTP 429 (Too Many Requests)
- Retry-After header parsing
- X-RateLimit-* headers
- Custom rate limit headers

#### 4. Adaptive throttling
- Reduce request rate on 429
- Respect Retry-After header
- Queue requests instead of failing
- Prioritize important requests

### Примеры использования

**Rate limiting middleware**:
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=60)
def rate_limited_request():
    return make_external_request()
```

**Adaptive throttling**:
```python
def adaptive_request():
    backoff = 1  # seconds
    max_backoff = 60

    while True:
        try:
            return make_request()
        except RateLimitError as e:
            retry_after = e.retry_after or backoff
            sleep(min(retry_after, max_backoff))
            backoff *= 2
```

### Best Practices

- [ ] Уважать rate limits внешних систем
- [ ] Использовать очереди для burst requests
- [ ] Логировать rate limit violations
- [ ] Реализовать adaptive throttling
- [ ] Monitor rate limit usage

## Навык: Integration Contract Documentation

### Описание
Способность создавать исчерпывающую документацию для интеграционных контрактов.

### Компоненты навыка

#### 1. ADR (Architecture Decision Record)
- Context и problem statement
- Рассмотренные альтернативы
- Решение и обоснование
- Последствия (плюсы/минусы)
- Соответствие SPEC.md

#### 2. API specification
- OpenAPI/Swagger для REST
- GraphQL schema для GraphQL
- Protobuf definition для gRPC
- AsyncAPI для async/messaging

#### 3. HOWTO guide
- Prerequisites (API keys, permissions)
- Authentication flow
- Usage examples
- Error handling
- Best practices

#### 4. Test examples
- Happy path examples
- Error path examples
- Edge case examples
- Mock API specs

### Примеры использования

**ADR template**:
```markdown
# ADR-XXX: Integration with External API

## Status
Accepted

## Context
We need to integrate with External API for X, Y, Z.

## Considered Alternatives
1. REST API: pros/cons
2. GraphQL: pros/cons
3. gRPC: pros/cons

## Decision
Use REST API because...

## Consequences
Positive: X, Y
Negative: A, B

## References
- External API docs: [URL]
- SPEC.md section X.Y
```

**HOWTO guide**:
```markdown
# Integration Guide: External API

## Prerequisites
- API key from https://external.api/keys
- Scope: read, write

## Authentication
```python
client = ExternalClient(api_key="your-key")
client.authenticate()
```

## Usage
```python
# Create resource
resource = client.create_resource(
    name="Example",
    type="example_type"
)
```

## Error Handling
```python
try:
    client.create_resource(...)
except RateLimitError:
    # Implement retry
    pass
```
```

### Best Practices

- [ ] Создавать ADR для всех контрактов
- [ ] Использовать стандартные форматы спецификаций
- [ ] Предоставлять кодовые примеры
- [ ] Документировать error handling
- [ ] Версионировать документацию

## Навык: External API Analysis

### Описание
Способность анализировать документацию внешних API и выявлять проблемы/ограничения.

### Компоненты навыка

#### 1. API review
- Проверка completeness (все ли endpoints задокументированы)
- Проверка consistency (формат, naming)
- Проверка accuracy (примеры работают)
- Проверка clarity (описания понятны)

#### 2. Limitations identification
- Rate limits
- Feature limitations
- Data constraints
- Deprecated features

#### 3. Security review
- Authentication mechanisms
- Authorization requirements
- Data encryption
- Compliance requirements

#### 4. Compliance review
- GDPR (data protection)
- PCI-DSS (payment data)
- SOC 2 (security practices)
- HIPAA (healthcare data)

### Примеры использования

**API review checklist**:
```markdown
## External API Review: [Name]

### Completeness
- [ ] All endpoints documented
- [ ] Request/response formats provided
- [ ] Error codes documented
- [ ] Rate limits specified

### Consistency
- [ ] Naming conventions consistent
- [ ] Status codes used correctly
- [ ] Date formats consistent
- [ ] Pagination consistent

### Limitations
- Rate limit: 100 req/min
- Max payload: 1MB
- Concurrent requests: 10

### Security
- Auth: OAuth2 with scopes
- TLS required: yes
- IP allowlist: no

### Risks
- Rate limit: high
- Deprecated endpoints: none
- Downtime: 99.9% SLA
```

### Best Practices

- [ ] Тщательно изучить документацию
- [ ] Тестировать внешнюю API если возможно
- [ ] Документировать выявленные ограничения
- [ ] Предлагать workarounds для ограничений
- [ ] Эскалировать критические проблемы

## Навык: Integration Testing Strategy

### Описание
Способность определять стратегии тестирования для интеграционных контрактов.

### Компоненты навыка

#### 1. Test types
- Unit tests (client methods, data transformation)
- Integration tests (with external API)
- Contract tests (against specification)
- End-to-end tests (full workflow)

#### 2. Test scenarios
- Happy path (successful operations)
- Error path (error handling)
- Edge cases (boundary conditions)
- Stress tests (rate limiting, load)

#### 3. Mocking strategies
- Mock external API for unit tests
- Mock responses for error scenarios
- Mock rate limiting
- Mock network failures

#### 4. Test data
- Valid data
- Invalid data
- Boundary data
- Malicious data (security testing)

### Примеры использования

**Test scenarios**:
```python
def test_create_resource_happy_path():
    client = ExternalClient(api_key="test-key")
    response = client.create_resource(name="Test")
    assert response.success
    assert response.id is not None

def test_create_resource_rate_limit():
    client = ExternalClient(api_key="test-key")
    with pytest.raises(RateLimitError):
        for _ in range(200):  # Over rate limit
            client.create_resource(name="Test")

def test_create_resource_unauthorized():
    client = ExternalClient(api_key="invalid-key")
    with pytest.raises(AuthenticationError):
        client.create_resource(name="Test")
```

**Mock API**:
```python
@pytest.fixture
def mock_external_api():
    with patch('external.Client') as mock:
        mock.return_value.create_resource.return_value = MockResponse(
            id="test-id",
            success=True
        )
        yield mock
```

### Best Practices

- [ ] Тестировать happy path
- [ ] Тестировать error handling
- [ ] Mock external API для unit tests
- [ ] Интеграционные тесты с real API (staging)
- [ ] Test coverage > 80%
