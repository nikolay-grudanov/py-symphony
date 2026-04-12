# Implementation Engineer - Handoff контракты

## Обзор

Handoff контракты определяют правила передачи реализации кода между агентами.

## Общие принципы handoff

### Правила передачи
1. Код соответствует ADR и спецификациям
2. Все unit tests проходят
3. Code coverage достиг target (> 80%)
4. Документация создана (docstrings, README)
5. Pull Request создан и готов к review

### Формат передачи
Стандартный формат handoff:

```
## Handoff: Реализация ADR-[номер]

**От**: implementation-engineer
**Кому**: verification-agent / test-engineer

**ADR**: ADR-[номер]
**Спецификация**: [ссылка]

**Реализовано**:
- [ ] Функциональность 1
- [ ] Функциональность 2

**Артефакты**:
- [ ] Код: [ссылки на файлы]
- [ ] Unit tests: [ссылка]
- [ ] Integration tests: [ссылка если есть]
- [ ] Документация: [ссылка]

**Тесты**:
- Unit tests: [coverage %]
- Integration tests: [количество сценариев]
- All passing: ✅

**Документация**:
- Docstrings: да ✅
- README: обновлен ✅

**Pull Request**: #[номер]
**CI/CD**: passing ✅

**Важно**:
- [ ] Особенности реализации
- [ ] Known limitations
- [ ] Performance considerations

**Следующие шаги**:
1. [Шаг 1]
2. [Шаг 2]

**QA Gate**: [Что нужно проверить]
**Дедлайн**: [Дата]
```

## Входные handoff контракты

### От build-orchestrator

#### Входные требования для реализации

**Что получает implementation-engineer**:
- ADR с архитектурным решением
- Спецификации (контракты интеграции, API specs)
- Требования к функциональности
- Non-functional требования
- QA Gate критерии

**Пример**:
```
## Задача для Implementation Engineer

**Тип**: Реализация
**ADR**: ADR-025: Linear API Integration Contract
**Спецификация**: docs/integrations/linear/openapi.yaml

**Требования**:
- Реализовать OAuth2 authentication flow
- Реализовать GraphQL client
- Внедрить error handling (retry, circuit breaker)
- Внедрить rate limiting enforcement
- Реализовать webhook handler

**Non-functional**:
- Code quality: PEP 8, type hints, docstrings
- Test coverage: > 80%
- Performance: < 200ms latency
- Error handling: полный

**Контекст**:
- SPEC.md раздел 5.3
- Связанные задачи: #123, #124

**QA Gate**:
- Код соответствует ADR
- Код соответствует code standards
- Все unit tests проходят
- Test coverage > 80%
- Документация создана

**Дедлайн**: 2024-04-20
```

#### Критерии принятия задачи

Implementation engineer принимает задачу если:
- [ ] ADR понятен и approved
- [ ] Спецификации ясны и полные
- [ ] Requirements понятны
- [ ] Дедлайн достижим

### От platform-architect / agent-runtime-architect

#### Архитектурный контекст

**Что получает implementation-engineer**:
- ADR с архитектурным решением
- Диаграммы архитектуры
- Runtime спецификации
- Технические требования

**Пример**:
```
## Архитектурный контекст для реализации

**ADR**: ADR-010: Микросервисная архитектура
**Архитектура**:
- Слои: API, Business Logic, Data Access
- Patterns: Repository, Service, Factory
- Database: PostgreSQL
- Cache: Redis

**Runtime спецификация**: docs/runtime/api-layer.md
**Требования**:
- All integrations through dedicated layer
- Circuit breaker for external calls
- Observability: metrics, logging, tracing
```

### От integration-architect

#### Контракты интеграции

**Что получает implementation-engineer**:
- Контракты интеграции (OpenAPI, GraphQL schema, Protobuf)
- HOWTO guides
- Error handling стратегии
- Примеры использования

**Пример**:
```
## Контракт интеграции Linear API

**ADR**: ADR-025: Linear API Integration Contract
**Спецификация**: docs/integrations/linear/openapi.yaml

**Authentication**:
- Method: OAuth2
- Token endpoint: https://api.linear.app/oauth/token
- Scopes: read, write, admin

**Endpoints**:
- POST /graphql: GraphQL endpoint
- Webhooks для issue events

**Error handling**:
- 401: Refresh token
- 429: Exponential backoff (max 5 attempts)
- 5xx: Circuit breaker (threshold: 5 failures)

**Rate limiting**:
- 100 requests per 60 seconds
- Respect X-RateLimit-Reset header

**Примеры**: examples/integrations/linear/
```

## Выходные handoff контракты

### К verification-agent

#### Передача кода для верификации

**Что передает implementation-engineer**:
- Реализованный код
- Unit tests
- Integration tests если применимо
- Документацию

**Пример handoff**:
```
## Handoff: Верификация ADR-025

**От**: implementation-engineer
**Кому**: verification-agent

**ADR**: ADR-025
**Спецификация**: docs/integrations/linear/openapi.yaml

**Реализовано**:
- [ ] OAuth2 authentication flow
- [ ] GraphQL client
- [ ] Error handling (retry, circuit breaker)
- [ ] Rate limiting enforcement
- [ ] Webhook handler

**Артефакты**:
- [ ] Код: src/integrations/linear/
- [ ] Unit tests: tests/unit/integrations/linear/
- [ ] Integration tests: tests/integration/linear/
- [ ] Документация: docs/integrations/linear/

**Тесты**:
- Unit tests: 85% coverage
- Integration tests: 5 scenarios
- All passing: ✅

**Документация**:
- Docstrings: Complete
- README: Updated
- HOWTO: docs/integrations/linear/howto.md

**Pull Request**: #456
**CI/CD**: Passing ✅

**Важно**:
- OAuth2 token refresh реализован с retry
- Circuit breaker threshold: 5 consecutive failures
- Rate limit enforced with exponential backoff

**QA Gate**:
- [ ] Код соответствует ADR-025
- [ ] Код соответствует code standards (PEP 8, type hints)
- [ ] Error handling реализован согласно спецификации
- [ ] Все unit tests проходят
- [ ] Test coverage > 80%
- [ ] Документация полная

**Дедлайн для верификации**: 2024-04-21
```

#### Критерии отклонения верификации

Verification-agent отклоняет если:
- [ ] Код не соответствует ADR
- [ ] Код не соответствует code standards
- [ ] Error handling недостаточный
- [ ] Test coverage < target
- [ ] Документация неполная

### К test-engineer

#### Передача кода для интеграционных тестов

**Что передает implementation-engineer**:
- Реализованный код
- Unit tests
- Mock API specs если применимо
- Требования к integration testing

**Пример handoff**:
```
## Handoff: Интеграционные тесты ADR-025

**От**: implementation-engineer
**Кому**: test-engineer

**ADR**: ADR-025
**Код**: src/integrations/linear/

**Что нужно протестировать**:
- [ ] Authentication flow (token acquisition, refresh)
- [ ] CRUD operations с Linear API
- [ ] Error handling (retry logic, circuit breaker)
- [ ] Rate limiting enforcement
- [ ] Webhook handling

**Unit tests (уже написаны)**:
- 85% coverage
- All passing ✅

**Требования к integration tests**:
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
- [ ] Код: src/integrations/linear/
- [ ] Unit tests: tests/unit/integrations/linear/
- [ ] Mock specs: tests/mocks/linear/

**Ожидаемый результат**:
- Integration tests с real Linear API (staging)
- Performance tests (rate limiting)
- Load tests (concurrent requests)
- Test coverage для integration scenarios

**QA Gate**:
- [ ] Integration tests проходят
- [ ] Performance benchmarks met
- [ ] Error handling verified
- [ ] All scenarios covered

**Дедлайн**: 2024-04-22
```

## Handoff между разработчиками

### Обработка feedback от verification-agent

**Когда**: Verification-agent нашел проблемы в коде

**Процесс**:
```
## Feedback от verification-agent

**ADR**: ADR-025
**PR**: #456
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

**Решение**:
- [ ] Принято: [действие]
- [ ] Отклонено: [обоснование]

**Обновление PR**: [ссылка на updated PR]
**Версия**: v1.1
**Дедлайн**: [дата]
```

### Обработка feedback от code reviewers

**Когда**: Code review нашел проблемы

**Процесс**:
```
## Feedback от code review

**PR**: #456
**Reviewer**: [имя]

**Комментарии**:
- [ ] Комментарий 1: [что изменить]
- [ ] Комментарий 2: [что изменить]

**Решение**:
- [ ] Принято: [действие]
- [ ] Отклонено: [обоснование]

**Изменения**:
- [ ] Файл 1: [изменения]
- [ ] Файл 2: [изменения]

**Updated PR**: [ссылка]
**Request re-review**: да
```

## Специфичные handoff сценарии

### 1. Изменение ADR

**Когда**: ADR обновлен после начала реализации

**Процесс**:
```
## Обновление реализации: ADR-[номер]

**ADR**: ADR-[номер]
**Версия**: v1.1 (была v1.0)

**Изменения в ADR**:
- [ ] Изменение 1: [описание]
- [ ] Изменение 2: [описание]

**Влияние на реализацию**:
- Breaking changes: [да/нет]
- Новая функциональность: [список]
- Deprecated функциональность: [список]

**Действия**:
- [ ] Обновить код для соответствия ADR v1.1
- [ ] Обновить тесты
- [ ] Обновить документацию
- [ ] Request re-review

**Дедлайн**: [дата]
```

### 2. Баг найден после верификации

**Когда**: Баг найден после successful верификации

**Процесс**:
```
## Исправление бага: [Название]

**ADR**: ADR-[номер]
**PR**: #[номер]
**Баг**: [описание]

**Влияние**:
- Critical: [да/нет]
- Пользовательское влияние: [описание]

**Исправление**:
- [ ] Файл 1: [изменение]
- [ ] Файл 2: [изменение]

**Тесты**:
- [ ] Тест для бага добавлен
- [ ] Связанные tests обновлены

**New PR**: #[номер]
**Request re-verification**: да

**Дедлайн**: [дата]
```

### 3. Performance optimization

**Когда**: Требуется улучшить performance

**Процесс**:
```
## Performance optimization: [Название]

**ADR**: ADR-[номер]
**Current performance**: [метрики]
**Target performance**: [метрики]

**Оптимизации**:
- [ ] Оптимизация 1: [описание]
- [ ] Оптимизация 2: [описание]

**Бенчмарки**:
- До: [метрики]
- После: [метрики]

**Тесты**:
- [ ] Performance tests добавлены
- [ ] Unit tests обновлены

**New PR**: #[номер]
**Дедлайн**: [дата]
```

## Handoff формат для критических ситуаций

### 1. Критический баг в production

```
## 🚨 🚨 PRODUCTION BUG 🚨 🚨

**ADR**: ADR-[номер]
**Приоритет**: CRITICAL
**Баг**: [описание]

**Влияние**:
- Production: [как влияет]
- Users: [какое количество]

**Hotfix**:
- [ ] Исправление: [описание]
- [ ] Тест: [добавлен]

**Hotfix PR**: #[номер]
**Деплой**: [дата/время]
**Rollback plan**: [план]
```

### 2. Security vulnerability

```
## 🚨 🚨 SECURITY VULNERABILITY 🚨 🚨

**ADR**: ADR-[номер]
**Уязвимость**: [CVE если есть]
**Severity**: [Critical/High/Medium/Low]

**Влияние**:
- Data exposure: [да/нет]
- Unauthorized access: [да/нет]

**Fix**:
- [ ] Исправление: [описание]
- [ ] Mitigation: [если есть]

**Security PR**: #[номер]
**Деплой**: [дата/время]
**Advisory**: [ссылка если есть]
```

## Обратная связь и итерации

### Запрос информации у архитектора

```
ℹ️ Требуется информация от архитектора

**ADR**: ADR-[номер]
**Вопрос**: [что неясно]

**Раздел ADR**: [секция]
**Варианты интерпретации**:
1. [Вариант 1]
2. [Вариант 2]

**Рекомендация**: [что предлагаем]
**Дедлайн**: [дата]
```

### Запрос информации у integration-architect

```
ℹ️ Требуется информация от integration-architect

**Контракт**: [название]
**Вопрос**: [что неясно]

**Влияние**: [как влияет на реализацию]
**Предлагаемое решение**: [что предлагаем]
**Дедлайн**: [дата]
```

### Status update для build-orchestrator

```
## Status update: [Название задачи]

**ADR**: ADR-[номер]
**Статус**: [In Progress/Completed/Blocked]

**Прогресс**:
- [ ] Этап 1: завершен
- [ ] Этап 2: в процессе (50%)
- [ ] Этап 3: еще не начат

**Оценка завершения**: [дата/время]
**Блокеры**: [если есть]

**Вопросы**: [если есть]
```
