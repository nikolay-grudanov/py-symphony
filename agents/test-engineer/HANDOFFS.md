# Test Engineer - Handoff контракты

## Обзор

Handoff контракты определяют правила передачи задач между test-engineer и другими агентами.

## Handoff от Implementation Engineer → Test Engineer

### Входные требования

**Что получает test-engineer**:
- Реализованный код
- Требования к функциональности
- Requirements к coverage
- Code standards проекта
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
- Тесты должны быть быстрыми (< 5 сек для unit, < 30 сек для integration)

**Code Standards**:
- PEP 8 для Python кода
- pytest framework
- pytest-mock для mocking
- pytest-cov для coverage

**Контекст**:
- Существующие тесты: tests/services/payment/test_service.py
- Mock framework: pytest-mock
```

### Ожидаемые выходные данные

**Что должен создать test-engineer**:
- Unit tests
- Integration tests
- Test fixtures
- Coverage report
- Update README с инструкциями по запуску тестов

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
- Execution time: 4.2 сек

**Documentation**:
- README.md обновлен: раздел "Running tests"
- tests/CONVENTIONS.md создан: test conventions
- pytest.ini обновлен: настроены test fixtures
```

### Триггеры передачи от Test Engineer

Когда test-engineer передает задачу:
- Unit tests написаны и проходят
- Integration tests написаны и проходят
- Coverage соответствует требованиям
- Documentation обновлена
- Coverage report создан

### Критерии отклонения от Test Engineer

Build Orchestrator или verification-agent отклоняет результат если:
- Unit tests отсутствуют или не проходят
- Integration tests отсутствуют или не проходят
- Coverage ниже требуемого
- Нет documentation для запуска тестов
- Тесты слишком медленные
- Flaky tests присутствуют

## Handoff от Test Engineer → Verification Agent

### Входные требования

**Что получает verification-agent** от test-engineer:
- Unit tests
- Integration tests
- Test fixtures
- Coverage report
- Test documentation

**Пример**:
```
## Handoff: Тесты для PaymentService

**От**: test-engineer
**Кому**: verification-agent

**Что было сделано**:
- [ ] Unit tests написаны: 45 тестов
- [ ] Integration tests написаны: 10 тестов
- [ ] Test fixtures созданы
- [ ] Coverage: 87%

**Артефакты**:
- Unit tests: tests/services/payment/test_service.py
- Integration tests: tests/integration/test_payment_flow.py
- Test fixtures: tests/fixtures/payment_fixtures.py
- Coverage report: htmlcov/index.html

**Test results**:
- All tests pass ✅
- No flaky tests ✅
- Execution time: 4.2 сек

**Документация**:
- README.md обновлен: раздел "Running tests"
- tests/CONVENTIONS.md создан

**QA Gate**: Coverage > 80%, все тесты проходят
```

### Ожидаемые выходные данные от Verification Agent

**Что должен создать verification-agent**:
- Отчет о верификации тестов
- Список найденных проблем
- Рекомендации по улучшению
- Решение: Passed / Failed / Needs Rework

## Handoff от Verification Agent → Test Engineer (Feedback)

### Входные требования при feedback

**Что получает test-engineer** от verification-agent:
- Проблемы с тестами
- Отсутствующие test cases
- Низкий coverage
- Flaky tests
- Медленные тесты

**Пример**:
```
## ❌ Тестирование отклонено

**От**: verification-agent
**Кому**: test-engineer

**Проблемы**:
- [ ] Coverage недостаточный: 75% (требуется > 80%)
- [ ] Отсутствует test case: refund с отрицательной суммой
- [ ] Flaky test: test_retry_with_timeout (иногда fails)
- [ ] Медленный integration test: 45 сек (требуется < 30 сек)

**Требуемые исправления**:
- [ ] Добавить test для refund с отрицательной суммой
- [ ] Стабилизировать test_retry_with_timeout
- [ ] Оптимизировать integration test или разбить на части
- [ ] Увеличить coverage до > 80%

**Дедлайн**: 2024-04-16 14:00
```

### Ожидаемые выходные данные после исправлений

**Что должен предоставить test-engineer**:
- Исправленные тесты
- Обновленный coverage report
- Обновленная документация
- Повторный handoff

## Общие принципы handoff

### Правила передачи

1. Все QA Gates должны быть пройдены
2. Все артефакты должны быть созданы
3. Контекст должен быть полно передан
4. Ссылки на все материалы должны быть предоставлены

### Формат передачи

Стандартный формат handoff от test-engineer:

```
## Handoff: Тесты для [Название модуля]

**От**: test-engineer
**Кому**: [Имя агента]

**Что было сделано**:
- [ ] Unit tests написаны: [количество] тестов
- [ ] Integration tests написаны: [количество] тестов
- [ ] Test fixtures созданы
- [ ] Coverage: [X]%

**Артефакты**:
- [ ] Unit tests: [ссылка]
- [ ] Integration tests: [ссылка]
- [ ] Test fixtures: [ссылка]
- [ ] Coverage report: [ссылка]

**Test results**:
- All tests pass ✅
- No flaky tests ✅
- Execution time: [X] сек

**Документация**:
- [ ] README обновлен
- [ ] Test conventions задокументированы

**QA Gate**: Coverage > [X]%, все тесты проходят
**Дедлайн**: [Дата]
```

## Примеры полных сценариев handoff

### Пример 1: Успешный handoff

```
## Handoff: Тесты для PaymentService

**От**: test-engineer
**Кому**: verification-agent

**Что было сделано**:
- [x] Unit tests написаны: 45 тестов
- [x] Integration tests написаны: 10 тестов
- [x] Test fixtures созданы
- [x] Coverage: 87%

**Артефакты**:
- tests/services/payment/test_service.py
- tests/integration/test_payment_flow.py
- tests/fixtures/payment_fixtures.py
- htmlcov/index.html

**Test results**:
- All tests pass ✅
- No flaky tests ✅
- Execution time: 4.2 сек ✅

**Документация**:
- README.md обновлен
- tests/CONVENTIONS.md создан

**QA Gate**: Coverage > 80%, все тесты проходят ✅

**Статус**: READY FOR VERIFICATION
```

### Пример 2: Handoff с feedback

```
## ❌ Handoff отклонен

**От**: verification-agent
**Кому**: test-engineer

**Проблемы**:
- [ ] Coverage 75% (требуется > 80%)
- [ ] Отсутствует test case для refund с отрицательной суммой

**Требуемые исправления**:
- [ ] Добавить test_refund_negative_amount
- [ ] Увеличить coverage до > 80%

**Дедлайн**: 2024-04-16 14:00

**Переназначено**: test-engineer
```

### Пример 3: Повторный handoff после исправлений

```
## Handoff: Тесты для PaymentService (исправленные)

**От**: test-engineer
**Кому**: verification-agent

**Исправления**:
- [x] Добавлен test_refund_negative_amount
- [x] Coverage увеличен до 87%

**Обновленные артефакты**:
- tests/services/payment/test_service.py (updated)
- htmlcov/index.html (updated)

**Test results**:
- All tests pass ✅
- No flaky tests ✅
- Execution time: 4.5 сек ✅
- Coverage: 87% ✅

**QA Gate**: Coverage > 80%, все тесты проходят ✅

**Статус**: READY FOR VERIFICATION
```

## Emergency handoffs

### Срочные исправления

При критических ошибках в production:

1. **Минимальные тесты**
   - Только критические path tests
   - Skip edge cases
   - Минимальный coverage

2. **Post-incident testing**
   - После исправления: полный test suite
   - Добавление недостающих тестов
   - Полный coverage

### Формат emergency handoff

```
## 🚨 EMERGENCY HANDOFF

**От**: test-engineer
**Кому**: verification-agent

**Тип**: Emergency testing
**Приоритет**: КРИТИЧЕСКИЙ
**Дедлайн**: [Дата/Время]

**Проблема**: [Описание критической ошибки]

**Минимальные тесты**:
- [ ] Критический path 1
- [ ] Критический path 2

**Artefacts to skip** (для этого раза):
- [ ] Full edge case coverage
- [ ] Complete test fixtures
- [ ] Documentation updates

**Post-incident requirements**:
- [ ] Полный test suite
- [ ] Полный coverage
- [ ] Complete documentation
- [ ] Regression tests
```
