# Verification Agent - Handoff контракты

## Обзор

Handoff контракты определяют правила передачи результатов верификации между агентами.

## Общие принципы handoff

### Правила передачи
1. Валидация завершена полностью
2. Все findings документированы
3. Severity классифицирована
4. Approval или rejection decision сделан
5. Отчет создан и понятен

### Формат передачи
Стандартный формат handoff:

```
## Handoff: [Approval/Rejection] ADR-[номер]

**От**: verification-agent
**Кому**: build-orchestrator / implementation-engineer

**ADR**: ADR-[номер]
**Спецификация**: [ссылка если есть]

**Артефакты для верификации**:
- [ ] Код: [ссылки]
- [ ] Tests: [ссылка]
- [ ] Документация: [ссылка]

**Валидация**:
- Requirements coverage: [X/Y] (Z%)
- SPEC.md compliance: [X/Y] (Z%)
- Code quality: [X/Y] (Z%)
- Test coverage: [X%] (target: Y%)
- Documentation: [X/Y] (Z%)
- Security: [X/Y] (Z%)

**Findings**:
- Critical: [X]
- High: [Y]
- Medium: [Z]
- Low: [W]

**Решение**: [Approval/Rejection]

**Rationale**:
- [ ] Все critical критерии выполнены
- [ ] Все high критерии выполнены
- [ ] [Другие критерии]

**Важно**:
- [ ] Critical issues: [список если есть]
- [ ] High issues: [список если есть]

**Report**: [ссылка на детальный отчет]

**Next**: [следующие шаги]
**Дедлайн**: [дата если применимо]
```

## Входные handoff контракты

### От implementation-engineer

#### Входные артефакты для верификации

**Что получает verification-agent**:
- Реализованный код
- Unit tests
- Integration tests если применимо
- Документация

**Пример**:
```
## Handoff: Верификация ADR-025

**От**: implementation-engineer
**Кому**: verification-agent

**ADR**: ADR-025: Linear API Integration Contract
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

**QA Gate**:
- [ ] Код соответствует ADR-025
- [ ] Код соответствует code standards
- [ ] Error handling реализован
- [ ] Все unit tests проходят
- [ ] Test coverage > 80%
- [ ] Документация полная

**Важно**:
- OAuth2 token refresh реализован с retry
- Circuit breaker threshold: 5 consecutive failures
- Rate limit enforced with exponential backoff

**Дедлайн для верификации**: 2024-04-21
```

#### Критерии принятия артефактов

Verification agent принимает артефакты если:
- [ ] ADR понятен и approved
- [ ] Код доступен для review
- [ ] Тесты доступны для review
- [ ] Документация доступна для review
- [ ] QA Gate критерии ясны

### От integration-architect

#### Контракты для верификации

**Что получает verification-agent**:
- Контракты интеграции
- Спецификации контрактов
- Документация контрактов

**Пример**:
```
## Handoff: Валидация контракта Linear API

**От**: integration-architect
**Кому**: verification-agent

**Контракт**: Linear API Integration Contract
**ADR**: ADR-025

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

## Выходные handoff контракты

### К build-orchestrator

#### Передача результатов верификации

**Что передает verification-agent**:
- Результаты верификации
- Approval или rejection
- Детальный отчет
- Findings с severity

**Пример handoff (Approval)**:
```
## Handoff: Approval ADR-025

**От**: verification-agent
**Кому**: build-orchestrator

**ADR**: ADR-025
**Артефакты**: [список]

**Валидация**:
- Requirements coverage: 10/10 (100%) ✅
- SPEC.md compliance: 5/5 (100%) ✅
- Code quality: 8/8 (100%) ✅
- Test coverage: 85% (target: >80%) ✅
- Documentation: 10/10 (100%) ✅
- Security: 6/6 (100%) ✅

**Findings**:
- Critical: 0
- High: 0
- Medium: 0
- Low: 2

**Low issues**:
1. Variable name `x` не описателен в file.py:123
2. Docstring для function Z может быть более детальной

**Rationale**:
- Все critical критерии выполнены
- Все high критерии выполнены
- Несущественные issues могут быть отложены

**Recommendation**: Approve для merge

**Report**: docs/verification/adr-025-report.md

**Next**: Merge PR #456
```

**Пример handoff (Rejection)**:
```
## Handoff: Rejection ADR-025

**От**: verification-agent
**Кому**: build-orchestrator

**ADR**: ADR-025
**Артефакты**: [список]

**Валидация**:
- Requirements coverage: 9/10 (90%) ❌
- SPEC.md compliance: 5/5 (100%) ✅
- Code quality: 7/8 (87.5%) ❌
- Test coverage: 75% (target: >80%) ❌
- Documentation: 9/10 (90%) ❌
- Security: 6/6 (100%) ✅

**Findings**:
- Critical: 0
- High: 2
- Medium: 3
- Low: 1

**High issues** (must fix):
1. **Circuit breaker не реализован**
   - Location: src/integrations/linear/client.py
   - Requirement: ADR-025 section 4.3
   - Impact: Каскадные сбои при 5xx errors
   - Suggestion: Добавить circuit breaker с threshold=5, timeout=60

2. **Test coverage < target**
   - Location: tests/unit/integrations/linear/test_client.py
   - Coverage: 75% (target: >80%)
   - Impact: Потенциальные bugs в uncovered code
   - Suggestion: Добавить tests для error paths

**Medium issues** (should fix):
1. **Unit tests для error paths неполные**
   - Location: tests/unit/integrations/linear/test_client.py
   - Coverage: Error paths протестированы только на 60%
   - Impact: Потенциальные bugs в error handling
   - Suggestion: Добавить tests для 401, 429, 500 errors

2. **Docstrings для private methods отсутствуют**
   - Location: src/integrations/linear/client.py
   - Impact: Ухудшает поддерживаемость
   - Suggestion: Добавить docstrings

3. **README не обновлен с примерами использования**
   - Location: README.md
   - Impact: Сложность для новых пользователей
   - Suggestion: Добавить examples

**Rationale**:
- High issues найдены
- Test coverage < target
- Требуется исправление перед merge

**Recommendation**: Reject до исправления high issues и улучшения coverage

**Report**: docs/verification/adr-025-report.md

**Дедлайн для исправления**: 2024-04-22
**Next**: Feedback implementation-engineer
```

#### Критерии передачи approval

Verification agent передает approval если:
- [ ] Все critical критерии выполнены
- [ ] Все high критерии выполнены
- [ ] Test coverage >= target
- [ ] Security проверен и безопасен
- [ ] Нет critical или high issues

#### Критерии передачи rejection

Verification agent передает rejection если:
- [ ] Critical issues найдены
- [ ] High issues найдены
- [ ] Test coverage < target
- [ ] Security vulnerability найдена
- [ ] Requirements не покрыты

### К implementation-engineer

#### Передача feedback

**Что передает verification-agent**:
- Findings с severity
- Specific comments для найденных issues
- Suggestions для improvements
- Дедлайн для исправления

**Пример handoff**:
```
## Handoff: Feedback по верификации ADR-025

**От**: verification-agent
**Кому**: implementation-engineer

**ADR**: ADR-025
**PR**: #456

**Решение**: Rejection

**Findings**:
- Critical: 0
- High: 2
- Medium: 3
- Low: 1

**High issues** (must fix):

1. **Circuit breaker не реализован**
   - **Location**: src/integrations/linear/client.py
   - **Requirement**: ADR-025 section 4.3
   - **Description**: ADR требует circuit breaker для external calls, но не реализован
   - **Impact**: Каскадные сбои при 5xx errors
   - **Suggestion**:
     ```python
     from circuitbreaker import circuit

     @circuit(failure_threshold=5, recovery_timeout=60)
     def call_linear_api(self, query: str) -> dict:
         # implementation
     ```

2. **Test coverage < target**
   - **Location**: tests/unit/integrations/linear/test_client.py
   - **Coverage**: 75% (target: >80%)
   - **Description**: Coverage для error paths недостаточна
   - **Impact**: Потенциальные bugs в uncovered code
   - **Suggestion**: Добавить tests для:
     - Test authentication error handling (401)
     - Test rate limit error handling (429)
     - Test server error handling (500)

**Medium issues** (should fix):

1. **Unit tests для error paths неполные**
   - **Location**: tests/unit/integrations/linear/test_client.py
   - **Coverage**: Error paths протестированы только на 60%
   - **Impact**: Потенциальные bugs в error handling
   - **Suggestion**: Добавить tests для 401, 429, 500 errors

2. **Docstrings для private methods отсутствуют**
   - **Location**: src/integrations/linear/client.py
   - **Description**: Private methods не имеют docstrings
   - **Impact**: Ухудшает поддерживаемость
   - **Suggestion**: Добавить docstrings для private methods

3. **README не обновлен с примерами использования**
   - **Location**: README.md
   - **Description**: Нет примеров использования Linear integration
   - **Impact**: Сложность для новых пользователей
   - **Suggestion**: Добавить раздел с examples

**Дедлайн для исправления**: 2024-04-22

**Next**:
1. Исправить high issues
2. Улучшить test coverage до >80%
3. Submit updated PR
4. Request re-verification

**Report**: docs/verification/adr-025-report.md
```

### К integration-architect

#### Передача feedback по контракту

**Что передает verification-agent**:
- Findings по контракту
- Issues в контракте
- Suggestions для improvements

**Пример handoff**:
```
## Handoff: Feedback по контракту Linear API

**От**: verification-agent
**Кому**: integration-architect

**Контракт**: Linear API Integration Contract
**ADR**: ADR-025

**Решение**: Approval с suggestions

**Findings**:
- Critical: 0
- High: 0
- Medium: 1
- Low: 2

**Medium issues**:

1. **Edge case: simultaneous requests не рассмотрен**
   - **Location**: ADR-025 section 4.2
   - **Description**: Нет стратегии для одновременных запросов к Linear API
   - **Impact**: Возможны rate limit violations при concurrency
   - **Suggestion**: Добавить section 4.2.3 "Concurrency handling" с рекомендациями:
     - Use connection pooling
     - Implement request queuing
     - Respect rate limits across concurrent requests

**Low issues**:

1. **Error codes для Linear API не все перечислены**
   - **Location**: ADR-025 section 4.3
   - **Description**: Только 401, 429, 5xx перечислены
   - **Impact**: Не полная документация
   - **Suggestion**: Добавить все Linear API error codes:
     - 400: Bad Request
     - 403: Forbidden
     - 404: Not Found
     - 422: Unprocessable Entity

2. **Retry-After header parsing не описан**
   - **Location**: ADR-025 section 4.4
   - **Description**: Как парсить Retry-After header?
   - **Impact**: Неоднозначность для реализации
   - **Suggestion**: Добавить пример parsing:
     ```python
     from datetime import datetime, timedelta

     def parse_retry_after(header: str) -> timedelta:
         # Parse seconds: "120" -> 120 seconds
         try:
             seconds = int(header)
             return timedelta(seconds=seconds)
         except ValueError:
             # Parse HTTP-date: "Wed, 21 Oct 2015 07:28:00 GMT"
             dt = datetime.strptime(header, "%a, %d %b %Y %H:%M:%S %Z")
             return dt - datetime.utcnow()
     ```

**Recommendation**: Approval с suggestions для улучшения

**Next**: Consider medium issues в следующей версии контракта

**Report**: docs/verification/adr-025-contract-report.md
```

## Handoff между верификациями

### Re-verification

**Когда**: Implementation engineer исправил issues

**Процесс**:
```
## Re-verification: ADR-[номер]

**ADR**: ADR-[номер]
**Original verification**: [дата]
**Updated PR**: #[новый номер]

**Исправления**:
- [ ] Исправление 1: [описание]
- [ ] Исправление 2: [описание]

**Валидация**:
- Requirements coverage: [X/Y] (Z%)
- SPEC.md compliance: [X/Y] (Z%)
- Code quality: [X/Y] (Z%)
- Test coverage: [X%] (target: Y%)
- Documentation: [X/Y] (Z%)
- Security: [X/Y] (Z%)

**Findings**:
- Critical: [X]
- High: [Y]
- Medium: [Z]
- Low: [W]

**Решение**: [Approval/Rejection]

**Next**: [следующие шаги]
```

### Verification другого агента

**Когда**: Требуется верифицировать артефакты от другого агента

**Пример**:
```
## Handoff: Верификация контракта от integration-architect

**От**: integration-architect
**Кому**: verification-agent

**Контракт**: [название]
**ADR**: ADR-[номер]

**Что нужно проверить**:
- [ ] Контракт покрывает все бизнес-требования
- [ ] Error handling стратегия полная
- [ ] Все edge cases рассмотрены
- [ ] Примеры корректны
- [ ] Спецификация соответствует внешней API

**Ожидаемый результат**:
- Отчет о верификации с findings
- Approval если контракт валиден
```

## Специфичные handoff сценарии

### 1. Частичная approval

**Когда**: Critical и high issues исправлены, но medium/low issues остались

**Процесс**:
```
## Handoff: Частичная approval ADR-[номер]

**От**: verification-agent
**Кому**: build-orchestrator

**ADR**: ADR-[номер]
**PR**: #[номер]

**Валидация**:
- Requirements coverage: [X/Y] (Z%) ✅
- SPEC.md compliance: [X/Y] (Z%) ✅
- Code quality: [X/Y] (Z%) ✅
- Test coverage: [X%] (target: Y%) ✅
- Documentation: [X/Y] (Z%) ⚠️
- Security: [X/Y] (Z%) ✅

**Findings**:
- Critical: 0
- High: 0
- Medium: [X]
- Low: [Y]

**Medium issues** (can be deferred):
1. [Issue 1]: [описание]

**Low issues** (optional):
1. [Issue 1]: [описание]

**Rationale**:
- Все critical критерии выполнены
- Все high критерии выполнены
- Test coverage >= target
- Medium и low issues не блокируют merge

**Recommendation**: Approve с deferment of medium/low issues

**Deferred issues**: [создать task(s) в backlog]

**Next**: Merge и создать tasks для deferred issues
```

### 2. Security vulnerability найдена

**Когда**: Обнаружена security уязвимость

**Процесс**:
```
## 🚨 🚨 SECURITY VULNERABILITY FOUND 🚨 🚨

**ADR**: ADR-[номер]
**Уязвимость**: [CVE если есть или описание]
**Severity**: [Critical/High/Medium/Low]

**Влияние**:
- Data exposure: [да/нет]
- Unauthorized access: [да/нет]

**Location**: [файл:строка]
**Description**: [детальное описание]

**Mitigation**: [как защититься]
**Fix**: [предложение]

**Решение**: CRITICAL rejection

**Требуемое действие**:
- [ ] Implementation engineer: срочно исправить
- [ ] Architect: review если нужен
- [ ] Security team: notify если нужно

**Hotfix PR**: #[номер] если применимо
**Дедлайн**: [максимальное время]

**Next**: Срочная эскалация
```

### 3. Requirements change

**Когда**: Requirements изменились после начала верификации

**Процесс**:
```
## Requirements change: ADR-[номер]

**ADR**: ADR-[номер]
**Версия**: v1.1 (была v1.0)

**Изменения в requirements**:
- [ ] Изменение 1: [описание]
- [ ] Изменение 2: [описание]

**Влияние на верификацию**:
- New requirements: [список]
- Changed requirements: [список]
- Removed requirements: [список]

**Действия**:
- [ ] Пауза текущей верификации
- [ ] Обновление verification plan
- [ ] Re-verification с новыми requirements

**Дедлайн**: [дата]
**Next**: Continue верификацию с новыми requirements
```

## Обратная связь и итерации

### Запрос информации у архитектора

```
ℹ️ Требуется информация от архитектора

**ADR**: ADR-[номер]
**Раздел**: [секция]
**Вопрос**: [что неясно]

**Варианты интерпретации**:
1. [Вариант 1]
2. [Вариант 2]

**Контекст**: [описание ситуации]
**Влияние на верификацию**: [описание]
**Рекомендация**: [что предлагаем]

**Дедлайн**: [дата]
```

### Запрос информации у implementation-engineer

```
ℹ️ Требуется информация от implementation-engineer

**ADR**: ADR-[номер]
**Вопрос**: [что неясно]

**Почему**: [для чего нужна]
**Контекст**: [описание]

**Дедлайн**: [дата]
```

### Status update для build-orchestrator

```
## Status update: Верификация ADR-[номер]

**ADR**: ADR-[номер]
**Статус**: [In Progress/Completed/Blocked]

**Прогресс**:
- [ ] Code review: [X%]
- [ ] Requirements coverage: [X%]
- [ ] SPEC.md compliance: [X%]
- [ ] Code quality: [X%]
- [ ] Test coverage: [X%]
- [ ] Documentation: [X%]
- [ ] Security: [X%]

**Findings**: [количество issues found]
- Critical: [X]
- High: [Y]
- Medium: [Z]
- Low: [W]

**Прогноз завершения**: [дата/время]
**Блокеры**: [если есть]
```
