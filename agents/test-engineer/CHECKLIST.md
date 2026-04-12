# Test Engineer - Чеклист завершения

## Обзор

Чеклист определяет критерии завершения задач тестирования. Test Engineer не может считать задачу завершенной, пока все пункты чеклиста не выполнены.

## Чеклист для задач написания тестов

### Unit Tests

- [ ] **Unit tests написаны**
  - [ ] Тесты для всех публичных методов
  - [ ] Тесты для private методов если критичны
  - [ ] Тесты для всех классов/модулей
  - [ ] Тесты соответствуют code standards

- [ ] **Сценарии покрыты**
  - [ ] Happy path tests
  - [ ] Error path tests
  - [ ] Edge case tests
  - [ ] Invalid input tests

- [ ] **Test structure**
  - [ ] Использован Given-When-Then паттерн
  - [ ] Ясные и описательные имена тестов
  - [ ] Docstrings для сложных тестов
  - [ ] Proper assertions

- [ ] **Isolation**
  - [ ] Тесты изолированы друг от друга
  - [ ] Нет dependencies между тестами
  - [ ] External dependencies mocked
  - [ ] No hardcoded values (использованы fixtures)

### Integration Tests

- [ ] **Integration tests написаны**
  - [ ] Тесты для основных workflows
  - [ ] Тесты для multi-step сценариев
  - [ ] Тесты для error scenarios
  - [ ] Тесты для retry/fallback логики

- [ ] **External systems**
  - [ ] External API mocked
  - [ ] Database mocked или используется test database
  - [ ] Message queues mocked
  - [ ] File system mocked

- [ ] **Setup и teardown**
  - [ ] Proper setup перед тестом
  - [ ] Cleanup после теста
  - [ ] Fixtures для reuse
  - [ ] Isolation между тестами

- [ ] **Test stability**
  - [ ] Нет timing dependencies
  - [ ] Нет race conditions
  - [ ] Tests идемпотентны
  - [ ] Нет flaky tests

### Test Fixtures

- [ ] **Fixtures созданы**
  - [ ] Data fixtures для common test data
  - [ ] Mock fixtures для external dependencies
  - [ ] Environment fixtures (database, env vars)
  - [ ] Fixtures имеют proper scope

- [ ] **Fixtures reusable**
  - [ ] Fixtures используются в multiple tests
  - [ ] Fixtures имеют описательные имена
  - [ ] Fixtures документированы
  - [ ] Fixtures maintainable

### Test Execution

- [ ] **Все тесты проходят**
  - [ ] Все unit tests проходят
  - [ ] Все integration tests проходят
  - [ ] Нет skipped tests без причины
  - [ ] Нет failed tests

- [ ] **Test performance**
  - [ ] Unit tests выполняются < 5 сек
  - [ ] Integration tests выполняются < 30 сек
  - [ ] Нет слишком медленных тестов
  - [ ] Оптимизированы slow tests

- [ ] **No flaky tests**
  - [ ] Все тесты стабильны
  - [ ] Тесты проходят при повторном запуске
  - [ ] Нет intermittent failures

### Coverage

- [ ] **Coverage соответствует требованиям**
  - [ ] Line coverage >= [X]%
  - [ ] Branch coverage >= [Y]%
  - [ ] Critical код покрыт на 100%
  - [ ] Coverage report создан

- [ ] **Uncovered code проанализирован**
  - [ ] Uncovered lines идентифицированы
  - [ ] Uncovered код либо протестирован, либо обоснован
  - [ ] Dead code удален если есть

### Documentation

- [ ] **README обновлен**
  - [ ] Раздел "Running tests" создан
  - [ ] Инструкции по запуску unit tests
  - [ ] Инструкции по запуску integration tests
  - [ ] Инструкции по генерации coverage report

- [ ] **Test conventions задокументированы**
  - [ ] Файл tests/CONVENTIONS.md создан
  - [ ] Соглашения по именованию тестов
  - [ ] Структура тестовых файлов
  - [ ] Использование fixtures
  - [ ] Mock стратегии

- [ ] **Test documentation**
  - [ ] Сложные тесты задокументированы
  - [ ] Edge cases задокументированы
  - [ ] Mock стратегии задокументированы

## Чеклист для задач улучшения тестов

### Refactoring Tests

- [ ] **Тесты рефакторены**
  - [ ] Удалены дубликаты кода
  - [ ] Extracted fixtures
  - [ ] Упрощены сложные тесты
  - [ ] Улучшена читаемость

- [ ] **Tests maintainable**
  - [ ] Тесты легко обновлять
  - [ ] Тесты легко понимать
  - [ ] Тесты следуют best practices

### Performance Optimization

- [ ] **Медленные тесты оптимизированы**
  - [ ] Identified slow tests
  - [ ] Optimized setup с fixtures
  - [ ] Использованы parallel tests если нужно
  - [ ] Убраны unnecessary operations

### Stabilizing Flaky Tests

- [ ] **Flaky tests стабилизированы**
  - [ ] Причина flakiness идентифицирована
  - [ ] Test исправлен или переписан
  - [ ] Test теперь стабилен
  - [ ] Verified через multiple runs

## Чеклист для полной задачи тестирования

### Все артефакты созданы

- [ ] **Unit tests**
  - [ ] Файлы тестов созданы: tests/unit/[module]/test_*.py
  - [ ] Все тесты написаны
  - [ ] Все тесты проходят

- [ ] **Integration tests**
  - [ ] Файлы тестов созданы: tests/integration/[module]/test_*.py
  - [ ] Все тесты написаны
  - [ ] Все тесты проходят

- [ ] **Test fixtures**
  - [ ] Fixtures созданы: tests/fixtures/[module]/
  - [ ] Fixtures документированы

- [ ] **Coverage**
  - [ ] Coverage report создан: htmlcov/index.html
  - [ ] Coverage соответствует требованиям

- [ ] **Documentation**
  - [ ] README.md обновлен
  - [ ] tests/CONVENTIONS.md создан

### QA Gates пройдены

- [ ] **Все unit tests проходят**
- [ ] **Все integration tests проходят**
- [ ] **Coverage >= требований**
- [ ] **Нет flaky tests**
- [ ] **Test performance в пределах нормы**

## Правила завершения

### Условия для завершения задачи

Задача тестирования может быть завершена только если:

1. **Все пункты соответствующего чеклиста выполнены**
2. **Все тесты проходят**
3. **Coverage соответствует требованиям**
4. **Нет flaky tests**
5. **Documentation полная и актуальная**
6. **Coverage report создан**

### Условия для отклонения задачи

Задача тестирования отклоняется если:

1. **Unit tests отсутствуют или не проходят**
2. **Integration tests отсутствуют или не проходят**
3. **Coverage ниже требуемого**
4. **Flaky tests присутствуют**
5. **Тесты слишком медленные**
6. **Документация отсутствует или неполная**

## Примеры использования чеклиста

### Пример 1: Успешное завершение

```
## Задача: Тесты для PaymentService

### Unit Tests
- [x] Unit tests написаны: 45 тестов
- [x] Сценарии покрыты (happy, error, edge cases)
- [x] Test structure (Given-When-Then)
- [x] Isolation (все изолированы)

### Integration Tests
- [x] Integration tests написаны: 10 тестов
- [x] External systems mocked
- [x] Setup и teardown
- [x] Test stability (no flaky tests)

### Test Fixtures
- [x] Fixtures созданы (data, mock, environment)
- [x] Fixtures reusable

### Test Execution
- [x] Все тесты проходят
- [x] Execution time: 4.2 сек (< 5 сек)
- [x] No flaky tests

### Coverage
- [x] Coverage: 87% (> 80%)
- [x] Uncovered code проанализирован

### Documentation
- [x] README.md обновлен
- [x] tests/CONVENTIONS.md создан

### Результат: Задача завершена ✅
```

### Пример 2: Задача отклонена

```
## Задача: Тесты для PaymentService

### Unit Tests
- [x] Unit tests написаны
- [x] Сценарии покрыты
- [x] Test structure
- [x] Isolation

### Integration Tests
- [x] Integration tests написаны
- [x] External systems mocked
- [ ] Setup и teardown ❌ (не cleanup после тестов)
- [ ] Test stability ❌ (flaky test обнаружен)

### Test Execution
- [x] Все тесты проходят
- [x] Execution time в норме
- [ ] No flaky tests ❌ (есть flaky test)

### Coverage
- [x] Coverage: 82% (> 80%)
- [x] Uncovered code проанализирован

### Result: Задача отклонена
Причины:
- Flaky test: test_retry_with_timeout
- Missing cleanup в integration tests

Action: Исправить flaky test, добавить cleanup
```

### Пример 3: Повторное завершение после исправлений

```
## Задача: Тесты для PaymentService (исправленные)

### Unit Tests
- [x] Unit tests написаны
- [x] Сценарии покрыты
- [x] Test structure
- [x] Isolation

### Integration Tests
- [x] Integration tests написаны
- [x] External systems mocked
- [x] Setup и teardown ✅ (добавлен cleanup)
- [x] Test stability ✅ (flaky test исправлен)

### Test Execution
- [x] Все тесты проходят
- [x] Execution time: 4.5 сек
- [x] No flaky tests ✅

### Coverage
- [x] Coverage: 87%
- [x] Uncovered code проанализирован

### Result: Задача завершена ✅
```

## Метрики качества

Для оценки качества выполнения чеклиста используются следующие метрики:

1. **Процент выполнения чеклиста**
   - 100%: Все пункты выполнены ✅
   - 80-99%: Почти все пункты выполнены, могут быть некритические пропуски
   - <80%: Значительные пропуски, требуется доработка

2. **Coverage**
   - >= 80%: Отлично ✅
   - 70-79%: Хорошо, но можно лучше ⚠️
   - < 70%: Недостаточно ❌

3. **Test execution time**
   - Unit < 5 сек: Отлично ✅
   - Integration < 30 сек: Отлично ✅
   - Медленные тесты: Требует оптимизации ⚠️

4. **Flaky test rate**
   - 0%: Отлично ✅
   - > 0%: Требует исправления ❌

5. **Количество итераций**
   - 1: Идеально ✅
   - 2-3: Хорошо ⚠️
   - > 3: Требует улучшения процесса ❌
