# Integration Architect - Чеклист завершения

## Обзор

Чеклист определяет критерии завершения при проектировании контрактов интеграции. Integration Architect не может считать контракт завершенным, пока все пункты не выполнены.

## Чеклист для контракта интеграции

### ADR для контракта

- [ ] **ADR создан**
  - ADR содержит все необходимые разделы:
    - [ ] Status (Accepted/Rejected/etc.)
    - [ ] Context (проблема, требования к интеграции)
    - [ ] Рассмотренные альтернативы (минимум 2)
    - [ ] Решение с обоснованием
    - [ ] Последствия (плюсы/минусы)
    - [ ] Соответствие SPEC.md (ссылки на разделы)

- [ ] **ADR approved**
  - ADR имеет approval от соответствующего архитектора
  - Дата approval указана
  - Имя архитектора указана

- [ ] **Соответствие SPEC.md**
  - Контракт соответствует требованиям SPEC.md
  - Ссылки на соответствующие разделы SPEC.md предоставлены
  - Нет противоречий с SPEC.md

### Спецификация контракта

- [ ] **Спецификация создана**
  - [ ] OpenAPI/Swagger для REST
  - [ ] GraphQL schema для GraphQL
  - [ ] Protobuf definition для gRPC
  - [ ] AsyncAPI для async/messaging

- [ ] **Endpoints/операции определены**
  - [ ] Все операции задокументированы
  - [ ] Request formats описаны
  - [ ] Response formats описаны
  - [ ] Status codes определены

- [ ] **Типы данных определены**
  - [ ] Все типы задокументированы
  - [ ] Field constraints (required, optional, default)
  - [ ] Enum values если применимо
  - [ ] Validation правила

- [ ] **Versioning стратегия**
  - [ ] Метод versioning определен
  - [ ] Backwards compatibility рассмотрена
  - [ ] Deprecation политика

### Authentication и Authorization

- [ ] **Метод аутентификации определен**
  - [ ] Метод (OAuth2, API Key, Basic Auth, etc.)
  - [ ] Token endpoint (если OAuth2)
  - [ ] Scopes/permissions
  - [ ] Token refresh логика

- [ ] **Метод авторизации определен**
  - [ ] Авторизация на endpoint уровне
  - [ ] Role-based access если применимо
  - [ ] Permission checks

- [ ] **Security considerations**
  - [ ] TLS/SSL требования
  - [ ] Data encryption если нужно
  - [ ] Secret storage (не в контракте)
  - [ ] Compliance требования (GDPR, PCI-DSS)

### Data Transformation

- [ ] **Field mapping определен**
  - [ ] Mapping между внешними и внутренними полями
  - [ ] Type conversions
  - [ ] Data нормализация
  - [ ] Null handling

- [ ] **Mapping документирован**
  - [ ] Все маппинги задокументированы
  - [ ] Примеры transformations
  - [ ] Validation правила

### Error Handling

- [ ] **Error classification**
  - [ ] Retryable errors определены (429, 5xx)
  - [ ] Non-retryable errors определены (400, 401, 403, 404)
  - [ ] Transient errors определены

- [ ] **Retry стратегия**
  - [ ] Retryable errors
  - [ ] Backoff стратегия (exponential/linear/fixed)
  - [ ] Max attempts
  - [ ] Retry conditions

- [ ] **Circuit breaker**
  - [ ] Threshold определен
  - [ ] Timeout определен
  - [ ] States (closed, open, half-open)
  - [ ] Recovery логика

- [ ] **Fallback механизмы**
  - [ ] Alternative endpoints
  - [ ] Cached data
  - [ ] Default values
  - [ ] Graceful degradation

- [ ] **Error responses задокументированы**
  - [ ] Error codes
  - [ ] Error messages
  - [ ] Error types
  - [ ] Примеры error responses

### Rate Limiting

- [ ] **Rate limits определены**
  - [ ] Per-window limits (X requests per Y time)
  - [ ] Burst limits
  - [ ] Concurrent request limits

- [ ] **Enforcement стратегия**
  - [ ] Как enforce rate limits
  - [ ] Queue или fail
  - [ ] Backpressure если нужно

- [ ] **Rate limit detection**
  - [ ] HTTP 429 handling
  - [ ] Retry-After header parsing
  - [ ] X-RateLimit-* headers
  - [ ] Custom headers если есть

- [ ] **Adaptive throttling**
  - [ ] Reduce rate на 429
  - [ ] Respect Retry-After header
  - [ ] Request queuing

### Observability

- [ ] **Logging спецификация**
  - [ ] Request logging (какой уровень)
  - [ ] Response logging (какой уровень)
  - [ ] Error logging (error level)
  - [ ] Rate limit logging (warn level)
  - [ ] PII/Sensitive data excluded

- [ ] **Metrics спецификация**
  - [ ] request_count
  - [ ] request_latency
  - [ ] error_count (by error type)
  - [ ] circuit_breaker_state
  - [ ] rate_limit_hits

- [ ] **Tracing спецификация**
  - [ ] Distributed tracing если нужно
  - [ ] Trace ID propagation
  - [ ] Spans для операций

### Документация

- [ ] **HOWTO guide создан**
  - [ ] Prerequisites (API keys, permissions)
  - [ ] Authentication flow
  - [ ] Usage examples
  - [ ] Error handling guide
  - [ ] Best practices

- [ ] **Примеры использования**
  - [ ] Happy path examples
  - [ ] Error handling examples
  - [ ] Edge case examples
  - [ ] Code examples (Python/other language)

- [ ] **API documentation**
  - [ ] Все endpoints/operations задокументированы
  - [ ] Request/response examples
  - [ ] Error code documentation
  - [ ] Authentication guide

- [ ] **Migration guide**
  - [ ] Если заменяет старую интеграцию
  - [ ] Breaking changes
  - [ ] Migration steps
  - [ ] Rollback plan

### Testing Requirements

- [ ] **Test scenarios определены**
  - [ ] Happy path scenarios
  - [ ] Error path scenarios
  - [ ] Edge case scenarios
  - [ ] Performance scenarios

- [ ] **Mock API specs**
  - [ ] Success responses
  - [ ] Error responses
  - [ ] Rate limit responses
  - [ ] Timeout responses

- [ ] **Test coverage requirements**
  - [ ] Target coverage (> 80%)
  - [ ] Critical paths 100%
  - [ ] Error handling coverage

### Критерии качества

- [ ] **Контракт ясный и полный**
  - [ ] Все requirements покрыты
  - [ ] Нет неоднозначностей
  - [ ] Все edge cases рассмотрены

- [ ] **Контракт реализуемый**
  - [ ] Выбранный стек поддерживает протокол
  - [ ] External API поддерживает требуемую функциональность
  - [ ] Performance требования достижимы

- [ ] **Контракт поддерживаемый**
  - [ ] Backwards compatibility
  - [ ] Versioning стратегия
  - [ ] Deprecation политика

- [ ] **Контракт безопасный**
  - [ ] Authentication defined
  - [ ] Authorization defined
  - [ ] Security considerations documented
  - [ ] Compliance requirements addressed

## Чеклист для handoff

### К implementation-engineer

- [ ] **ADR передан**
  - [ ] ADR документ доступен
  - [ ] ADR approved

- [ ] **Спецификация передана**
  - [ ] OpenAPI/GraphQL schema/Protobuf доступна
  - [ ] Формат понятен
  - [ ] Версия указана

- [ ] **Примеры переданы**
  - [ ] Code examples доступны
  - [ ] Request/response examples доступны
  - [ ] Error handling examples доступны

- [ ] **Документация передана**
  - [ ] HOWTO guide доступен
  - [ ] API documentation доступен
  - [ ] Migration guide если применимо

- [ ] **Важные аспекты отмечены**
  - [ ] Authentication flow
  - [ ] Error handling strategy
  - [ ] Rate limiting policy
  - [ ] Known limitations

### К verification-agent

- [ ] **Контракт для верификации передан**
  - [ ] ADR с требованиями доступен
  - [ ] Спецификация доступна
  - [ ] Requirements list доступен

- [ ] **Критерии верификации определены**
  - [ ] What to verify
  - [ ] Acceptance criteria
  - [ ] Expected results

### К test-engineer

- [ ] **Test requirements переданы**
  - [ ] Test scenarios document доступен
  - [ ] Mock API specs доступны
  - [ ] Test data examples доступны

- [ ] **Test coverage requirements**
  - [ ] Target coverage %
  - [ ] Critical paths
  - [ ] Error handling coverage

## Итоговый чеклист завершения

Перед завершением проектирования контракта:

- [ ] ADR создан и approved
- [ ] Спецификация полная и понятная
- [ ] Authentication и authorization определены
- [ ] Error handling стратегия полная
- [ ] Rate limiting стратегия определена
- [ ] Observability спецификации созданы
- [ ] Документация полная (HOWTO, examples)
- [ ] Test requirements определены
- [ ] Handoff подготовлен для implementation-engineer
- [ ] Handoff подготовлен для verification-agent
- [ ] Handoff подготовлен для test-engineer
- [ ] Все критерии качества выполнены
- [ ] Соответствие SPEC.md подтверждено

## Post-handoff checklist

После передачи контракта implementation-engineer:

- [ ] Implementation engineer принял задачу
- [ ] Вопросы implementation engineer обработаны
- [ ] Clarifications предоставлены если нужно
- [ ] Feedback от verification-agent получен
- [ ] Feedback от test-engineer получен
- [ ] Контракт готов к реализации
