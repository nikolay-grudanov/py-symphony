# Build Orchestrator - Handoff контракты

## Обзор

Handoff контракты определяют правила передачи задач между агентами, включая входные требования, ожидаемые результаты, триггеры передачи и критерии отклонения.

## Общие принципы handoff

### Правила передачи
1. Все QA Gates должны быть пройдены
2. Все артефакты должны быть созданы
3. Контекст должен быть полно передан
4. Ссылки на все материалы должны быть предоставлены

### Формат передачи
Стандартный формат handoff:

```
## Handoff: [Краткое описание задачи]

**От**: [Имя агента]
**Кому**: [Имя агента]

**Что было сделано**:
- [ ] Этап 1: [краткое описание результата]
- [ ] Этап 2: [краткое описание результата]

**Артефакты**:
- [ ] ADR: [ссылка или "N/A"]
- [ ] Спецификации: [ссылка или "N/A"]
- [ ] Код: [ссылка или "N/A"]
- [ ] Тесты: [ссылка или "N/A"]
- [ ] Документация: [ссылка или "N/A"]
- [ ] Verification: [ссылка или "N/A"]

**Контекст**:
- Связанные задачи: [ID задач]
- Зависимости: [Описание]
- Важные решения: [Краткое описание]

**Следующие шаги**:
1. [Шаг 1]
2. [Шаг 2]

**QA Gate**: [Что нужно проверить]
**Дедлайн**: [Дата]
```

## Platform Architect → Handoff

### Входные требования для Platform Architect

**Что получает платформенный архитектор**:
- Описание задачи от build-orchestrator
- Требования к системе или компоненту
- Ограничения (performance, scalability, security)
- Связанные документы и спецификации

**Пример**:
```
## Задача для Platform Architect

**Тип**: Архитектура платформы
**Описание**: Спроектировать микросервис для обработки платежей
**Требования**:
- Обработка 1000+ платежей в секунду
- Поддержка множества payment providers
- Асинхронная обработка
- Event-driven архитектура
- Устойчивость к сбоям

**Ограничения**:
- Response time < 100ms (синхронные операции)
- Время восстановления < 1 мин при сбое
- Compliance с PCI-DSS

**Контекст**:
- Ссылки: SPEC.md раздел 4.2
- Связанные задачи: #123, #124
```

### Ожидаемые выходные данные от Platform Architect

**Что должен создать платформенный архитектор**:
- ADR (Architecture Decision Record) с:
  - Описанием архитектурного решения
  - Рассмотренными альтернативами
  - Обоснованием выбора
  - Последствиями решения
- Диаграммы архитектуры (если применимо)
- Ссылки на соответствующие разделы SPEC.md

**Пример ADR**:
```
# ADR-001: Event-driven микросервис для обработки платежей

## Статус
Accepted

## Контекст
Нужно обрабатывать 1000+ платежей/сек, поддерживать несколько providers,
обеспечивать отказоустойчивость.

## Рассмотренные альтернативы
1. Monolithic подход
2. Microservices с REST API
3. Event-driven microservices (выбрано)

## Решение
Event-driven микросервис с message queue, отдельные workers для каждого provider.

## Последствия
- + Масштабируемость
- + Отказоустойчивость
- + Асинхронная обработка
- - Сложность управления
- - Требует message queue

## Соответствие SPEC.md
Раздел 4.2: Система должна быть event-driven

## Approval
Approved by: [Имя архитектора]
Date: [Дата]
```

### Триггеры передачи от Platform Architect

Когда платформенный архитектор передает задачу:
- ADR создан и записан
- ADR approved
- Все альтернативы рассмотрены
- Соответствие SPEC.md проверено

### Критерии отклонения от Platform Architect

Build Orchestrator отклоняет результат если:
- ADR не создан
- ADR не approved
- Не все альтернативы рассмотрены
- Нет обоснования выбора
- Нет описания последствий
- Нет связи с SPEC.md

## Implementation Engineer → Handoff

### Входные требования для Implementation Engineer

**Что получает инженер по реализации**:
- ADR от архитектора
- Требования к реализации
- Code standards проекта
- Ссылки на существующий код (если есть)

**Пример**:
```
## Задача для Implementation Engineer

**Тип**: Реализация
**Описание**: Реализовать payment service согласно ADR-001

**ADR**: [Ссылка на ADR-001]

**Требования**:
- Реализовать PaymentService с методами: processPayment, getStatus, refund
- Использовать RabbitMQ как message queue
- Поддержать 3 providers: Stripe, PayPal, Adyen
- Логирование всех операций
- Unit tests для всех методов

**Code Standards**:
- PEP 8 для Python кода
- Type hints для всех функций
- Docstrings для всех публичных методов
- Coverage > 80%

**Контекст**:
- Базовый код: src/services/payment/
- Зависимости: requirements.txt
- Связанные задачи: #125 (тесты), #126 (интеграция)
```

### Ожидаемые выходные данные от Implementation Engineer

**Что должен создать инженер по реализации**:
- Код реализации
- Unit tests
- Обновление документации API (если применимо)
- Update README (если применимо)
- Pull Request с описанием изменений

**Пример**:
```
## Результат реализации

**Код**:
- src/services/payment/service.py - PaymentService implementation
- src/services/payment/providers/ - Provider implementations
- src/services/payment/models.py - Data models
- tests/services/payment/test_service.py - Unit tests

**Артефакты**:
- PR #123: [ссылка]
- Coverage: 85%
- Все тесты проходят ✅

**Documentation**:
- README.md обновлен с примерами использования
- API docs добавлены
```

### Триггеры передачи от Implementation Engineer

Когда инженер передает задачу:
- Код реализован
- Unit tests написаны и проходят
- Код соответствует code standards
- Документация обновлена
- Pull request создан

### Критерии отклонения от Implementation Engineer

Build Orchestrator отклоняет результат если:
- Код не реализован полностью
- Unit tests отсутствуют или не проходят
- Код нарушает code standards
- Нет documentation для публичного API
- Pull request не создан

## Integration Architect → Handoff

### Входные требования для Integration Architect

**Что получает архитектор по интеграции**:
- ADR от платформенного архитектора (если применимо)
- Требования к интеграции
- Спецификации внешних систем
- Контекст интеграции

**Пример**:
```
## Задача для Integration Architect

**Тип**: Интеграция
**Описание**: Определить контракт интеграции с payment providers

**ADR**: [Ссылка на ADR-001]

**Требования**:
- Определить контракт для каждого provider
- Унифицировать интерфейс
- Обработать ошибки и retries
- Логирование запросов/ответов

**Внешние системы**:
- Stripe API: [ссылка на документацию]
- PayPal API: [ссылка на документацию]
- Adyen API: [ссылка на документацию]

**Контекст**:
- PaymentService уже реализован
- Нужно интегрировать providers в существующий сервис
```

### Ожидаемые выходные данные от Integration Architect

**Что должен создать архитектор по интеграции**:
- ADR для контракта интеграции
- Определение интерфейсов
- Спецификации контрактов
- Примеры использования

**Пример**:
```
## Результат интеграции

**ADR**: ADR-002: Контракт интеграции payment providers

**Интерфейсы**:
```
interface PaymentProvider {
  processPayment(request: PaymentRequest): Promise<PaymentResponse>
  getStatus(transactionId: string): Promise<PaymentStatus>
  refund(transactionId: string, amount: number): Promise<RefundResponse>
}
```

**Контракты**:
- StripeAdapter implements PaymentProvider
- PayPalAdapter implements PaymentProvider
- AdyenAdapter implements PaymentProvider

**Спецификации**:
- API specifications: docs/api/payment-providers.md
- Error handling: docs/api/error-handling.md
- Examples: examples/payment-integration.py
```

### Триггеры передачи от Integration Architect

Когда архитектор передает задачу:
- ADR для контракта создан и approved
- Интерфейсы определены
- Спецификации созданы
- Примеры использования предоставлены

### Критерии отклонения от Integration Architect

Build Orchestrator отклоняет результат если:
- ADR не создан или не approved
- Интерфейсы не определены
- Нет спецификаций контрактов
- Нет примеров использования
- Контракт не соответствует требованиям

## Test Engineer → Handoff

### Входные требования для Test Engineer

**Что получает инженер по тестированию**:
- Реализованный код
- Требования к функциональности
- Требования к coverage
- Существующие тесты (если есть)

**Пример**:
```
## Задача для Test Engineer

**Тип**: Тестирование
**Описание**: Написать unit и integration tests для payment service

**Код**: [Ссылка на PR #123]

**Требования**:
- Unit tests для всех методов PaymentService
- Unit tests для всех provider adapters
- Integration tests с mock providers
- Coverage > 80%
- Тесты должны быть быстрыми (< 5 сек)

**Контекст**:
- Существующие тесты: tests/services/payment/test_service.py
- Mock framework: pytest-mock
```

### Ожидаемые выходные данные от Test Engineer

**Что должен создать инженер по тестированию**:
- Unit tests
- Integration tests
- Тестовые fixtures
- Update README с инструкциями по запуску тестов
- Отчет о coverage

**Пример**:
```
## Результат тестирования

**Тесты**:
- tests/services/payment/test_service.py - Unit tests
- tests/services/payment/test_providers.py - Provider tests
- tests/integration/test_payment_flow.py - Integration tests
- tests/fixtures/payment_fixtures.py - Test fixtures

**Metrics**:
- Unit tests: 45 tests
- Integration tests: 10 tests
- Coverage: 87%
- Время выполнения: 4.2 сек

**Documentation**:
- README.md обновлен: раздел "Running tests"
- pytest.ini обновлен: настроены test fixtures
```

### Триггеры передачи от Test Engineer

Когда инженер передает задачу:
- Unit tests написаны и проходят
- Integration tests написаны и проходят
- Coverage соответствует требованиям
- Documentation обновлена

### Критерии отклонения от Test Engineer

Build Orchestrator отклоняет результат если:
- Unit tests отсутствуют или не проходят
- Integration tests отсутствуют или не проходят
- Coverage ниже требуемого
- Нет documentation для запуска тестов
- Тесты слишком медленные

## Verification Agent → Handoff

### Входные требования для Verification Agent

**Что получает верификатор**:
- Все артефакты (ADR, код, тесты, документация)
- Требования для проверки
- SPEC.md для соответствия

**Пример**:
```
## Задача для Verification Agent

**Тип**: Верификация
**Описание**: Проверить соответствие payment service требованиям и SPEC.md

**Артефакты**:
- ADR-001: [ссылка]
- ADR-002: [ссылка]
- PR #123 (код): [ссылка]
- PR #124 (тесты): [ссылка]

**Требования для проверки**:
- [ ] Код соответствует ADR-001
- [ ] Код соответствует code standards
- [ ] Тесты покрывают все требования
- [ ] Documentation полная и понятная
- [ ] Соответствие SPEC.md раздел 4.2

**SPEC.md**: [ссылка]
```

### Ожидаемые выходные данные от Verification Agent

**Что должен создать верификатор**:
- Отчет о верификации
- Список найденных проблем
- Рекомендации по улучшению
- Решение: Passed / Failed / Needs Rework

**Пример**:
```
## Результат верификации

**Решение**: Passed ✅

**Проверки**:
- [x] Код соответствует ADR-001: PASSED
- [x] Код соответствует code standards: PASSED
- [x] Тесты покрывают все требования: PASSED (87% coverage)
- [x] Documentation полная: PASSED
- [x] Соответствие SPEC.md: PASSED

**Проблемы**: Нет критических проблем

**Некритические замечания**:
- Уточнить документацию error handling
- Добавить примеры в README

**Рекомендации**:
- Рассмотреть добавение e2e tests
- Добавить metrics collection

**Verification complete**: Task ready for merge
```

### Триггеры передачи от Verification Agent

Когда верификатор передает задачу:
- Все проверки выполнены
- Отчет о верификации создан
- Решение принято (Passed / Failed / Needs Rework)

### Критерии отклонения от Verification Agent

Build Orchestrator отклоняет результат если:
- Не все проверки выполнены
- Нет отчета о верификации
- Нет решения (Passed / Failed / Needs Rework)
- Критические проблемы не задокументированы

## Обработка отклоненных handoffs

### Процесс при отклонении

1. **Build Orchestrator получает отклонение**
   - Анализирует причину отклонения
   - Определяет, какой агент должен исправить

2. **Переназначение задачи**
   - Отправляет задачу обратно соответствующему агенту
   - Указывает причины отклонения
   - Устанавливает дедлайн для исправлений

3. **Мониторинг исправлений**
   - Отслеживает прогресс исправлений
   - Проверяет результат после исправлений
   - Повторяет handoff если исправления успешны

### Формат отклонения

```
## ❌ Handoff отклонен

**От**: [Имя агента]
**Кому**: [Имя агента]
**Задача**: [ID задачи]

**Причины отклонения**:
- [ ] Причина 1: [подробности]
- [ ] Причина 2: [подробности]

**Требуемые исправления**:
- [ ] Исправление 1
- [ ] Исправление 2

**Дедлайн**: [Дата]

**Переназначено**: [Имя агента]
```

## Emergency handoffs

### Срочные исправления

При критических ошибках в production:

1. **Срочная задача**
   - Пропускает некоторые QA Gates
   - Минимальная документация
   - Максимальный приоритет

2. **Post-incident review**
   - После исправления: полный review
   - Обновление документации
   - Добавление недостающих тестов

### Формат emergency handoff

```
## 🚨 EMERGENCY HANDOFF

**От**: [Имя агента]
**Кому**: [Имя агента]

**Тип**: Emergency fix
**Приоритет**: КРИТИЧЕСКИЙ
**Дедлайн**: [Дата/Время]

**Проблема**: [Описание критической ошибки]
**Влияние**: [Как влияет на production]

**Требуемое решение**:
- [ ] Быстрое исправление
- [ ] Минимальные QA Gates
- [ ] Post-incident review

**Artefacts to skip** (для этого раза):
- [ ] Full documentation
- [ ] Complete test coverage
- [ ] Full verification

**Post-incident requirements**:
- [ ] Полная documentation
- [ ] Полные тесты
- [ ] Полная верификация
- [ ] Root cause analysis
```
