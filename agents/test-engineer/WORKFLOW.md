# Test Engineer - Рабочий процесс

## Обзор процесса

Test Engineer отвечает за создание и поддержание качественного тестового покрытия: от unit tests до integration tests.

## Шаг 1: Анализ требований к тестированию

### Изучение входных данных

Получить и проанализировать:
- Реализованный код от implementation-engineer
- Требования к функциональности
- Requirements к coverage
- Существующие тесты (если есть)
- Code standards проекта

### Определение типа тестирования

#### Unit testing
**Когда требуется**:
- Тестирование отдельных функций/методов
- Тестирование классов и модулей
- Изоляция от внешних зависимостей
- Быстрое выполнение (< 5 сек)

**Примеры**:
- Тестирование PaymentService.processPayment()
- Тестирование UserValidator.validateEmail()
- Тестирование DatabaseConnection.connect()

#### Integration testing
**Когда требуется**:
- Тестирование взаимодействия компонентов
- Тестирование с внешними системами (mock/stub)
- Тестирование workflows
- Более медленное выполнение (< 30 сек)

**Примеры**:
- Тестирование PaymentService с mock providers
- Тестирование API endpoint с test database
- Тестирование email sending workflow

#### End-to-end testing
**Когда требуется**:
- Тестирование полного сценария пользователя
- Тестирование с реальными внешними системами
- Медленное выполнение (минуты)

**Примеры**:
- Полный сценарий покупки товара
- Регистрация пользователя с email verification
- Отмена заказа с возвратом

## Шаг 2: Планирование тестов

### Создание тестового плана

```
## Тестовый план: [Название модуля/функциональности]

**Scope**: Что тестируем
- [ ] Модуль 1
- [ ] Модуль 2

**Unit Tests**:
- [ ] Тест для метода X: happy path
- [ ] Тест для метода X: error path
- [ ] Тест для метода Y: edge case
- ...

**Integration Tests**:
- [ ] Workflow 1: полный сценарий
- [ ] Workflow 2: error scenario
- ...

**Test Fixtures**:
- [ ] Fixture 1: [описание]
- [ ] Fixture 2: [описание]

**Target Coverage**: [X]%
```

### Определение test fixtures

Identify and plan fixtures:
- Mock data
- Test database setup
- Mock external services
- Common test utilities

## Шаг 3: Написание Unit Tests

### Структура unit test

```python
def test_[method_name]_[scenario]():
    """
    Тестовый сценарий: [описание]
    
    Given: [начальные условия]
    When: [действие]
    Then: [ожидаемый результат]
    """
    # Arrange
    ...
    
    # Act
    ...
    
    # Assert
    ...
```

### Покрытие сценариев

Для каждого метода протестировать:
- **Happy path**: Успешное выполнение
- **Error paths**: Обработка ошибок
- **Edge cases**: Граничные условия
- **Invalid inputs**: Некорректные входные данные

### Примеры

```
## Unit Tests для PaymentService

### Happy path tests
- [x] test_process_payment_success: Успешная обработка платежа
- [x] test_get_status_success: Получение статуса транзакции
- [x] test_refund_success: Успешный возврат

### Error path tests
- [x] test_process_payment_invalid_amount: Некорректная сумма
- [x] test_process_payment_insufficient_funds: Недостаточно средств
- [x] test_get_status_not_found: Транзакция не найдена

### Edge case tests
- [x] test_process_payment_zero_amount: Нулевая сумма
- [x] test_process_payment_negative_amount: Отрицательная сумма
- [x] test_refund_full_amount: Полный возврат
- [x] test_refund_partial_amount: Частичный возврат
```

## Шаг 4: Написание Integration Tests

### Структура integration test

```python
def test_[workflow_name]_[scenario]():
    """
    Тестовый сценарий: [описание]
    
    Given: [начальные условия, setup]
    When: [действие]
    Then: [ожидаемый результат]
    """
    # Setup
    ...
    
    # Act
    ...
    
    # Assert
    ...
    
    # Cleanup
    ...
```

### Mock внешних зависимостей

Использовать mocks/stubs для:
- Внешних API
- Database
- Message queues
- File system

```python
from unittest.mock import Mock, patch

@patch('services.payment.PaymentProvider')
def test_payment_workflow_success(mock_provider):
    # Arrange
    mock_provider.process.return_value = PaymentResponse(success=True)
    
    # Act
    result = payment_service.process(request)
    
    # Assert
    assert result.success is True
    mock_provider.process.assert_called_once()
```

### Примеры

```
## Integration Tests для PaymentService

### Workflow tests
- [x] test_payment_complete_workflow: Полный сценарий оплаты
- [x] test_payment_retry_workflow: Retry при ошибке
- [x] test_payment_fallback_workflow: Fallback на другой provider

### Error scenario tests
- [x] test_payment_timeout_error: Timeout при вызове provider
- [x] test_payment_network_error: Ошибка сети
- [x] test_payment_provider_unavailable: Provider недоступен
```

## Шаг 5: Создание Test Fixtures

### Типы fixtures

#### Data fixtures
```python
@pytest.fixture
def payment_request():
    return PaymentRequest(
        amount=100.00,
        currency="USD",
        card_number="4111111111111111",
        exp_month=12,
        exp_year=2025,
        cvv="123"
    )
```

#### Mock fixtures
```python
@pytest.fixture
def mock_payment_provider():
    with patch('services.payment.PaymentProvider') as mock:
        yield mock
```

#### Database fixtures
```python
@pytest.fixture
def test_database():
    db = create_test_database()
    yield db
    db.cleanup()
```

## Шаг 6: Запуск и анализ тестов

### Запуск тестов

```bash
# Все тесты
pytest

# Unit tests только
pytest tests/unit/

# Integration tests только
pytest tests/integration/

# С coverage report
pytest --cov=src --cov-report=html

# С verbosity
pytest -v
```

### Анализ результатов

Проверить:
- Все тесты проходят
- Coverage соответствует требованиям (обычно > 80%)
- Нет flaky tests
- Тесты выполняются быстро
- Нет skipped tests без причины

### Работа с flaky tests

Если тест flaky:
1. Идентифицировать причину (race condition, timing, dependency)
2. Изолировать тест
3. Добавить waits/stabilization
4. Или переписать тест

## Шаг 7: Документирование тестов

### Обновление README

Добавить раздел "Running tests":

```markdown
## Running Tests

### Prerequisites
- Python 3.9+
- pytest installed

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Coverage
```bash
pytest --cov=src --cov-report=html
```

### Test Fixtures
Test fixtures located in `tests/fixtures/`
```

### Документация test conventions

Создать `tests/CONVENTIONS.md`:
- Соглашения по именованию тестов
- Структура тестовых файлов
- Использование fixtures
- Mock стратегии

## Шаг 8: Verification покрытия

### Проверка coverage

```
## Coverage Report

**Module**: PaymentService
**Coverage**: 87% (Required: > 80%)

**Details**:
- PaymentService.processPayment: 95% ✅
- PaymentService.getStatus: 100% ✅
- PaymentService.refund: 80% ⚠️ (edge case missing)
- PaymentService._retry: 70% ❌ (error path not tested)

**Missing coverage**:
- test_refund_partial_amount_negative: edge case
- test_retry_max_attempts_reached: error path
```

### Улучшение coverage

Если coverage ниже требуемого:
1. Идентифицировать uncovered lines
2. Добавить tests для uncovered paths
3. Проверить dead code
4. Обновить coverage requirements если нужно

## Шаг 9: Handoff к verification

### Подготовка артефактов

Собрать:
- Unit tests
- Integration tests
- Test fixtures
- Coverage report
- Test documentation

### Формат handoff

```
## Handoff: Тесты для [Название]

**От**: test-engineer
**Кому**: verification-agent

**Что было сделано**:
- [ ] Unit tests написаны: [количество] тестов
- [ ] Integration tests написаны: [количество] тестов
- [ ] Test fixtures созданы
- [ ] Coverage: [X]%

**Артефакты**:
- Unit tests: [ссылка]
- Integration tests: [ссылка]
- Test fixtures: [ссылка]
- Coverage report: [ссылка]

**Test results**:
- All tests pass ✅
- No flaky tests ✅
- Execution time: [X] сек

**Документация**:
- README обновлен
- Test conventions задокументированы

**QA Gate**: Coverage > [X]%, все тесты проходят
```

## Шаг 10: Обработка feedback от verification

### Принятие корректировок

Если verification-agent нашел проблемы:

1. **Низкий coverage**
   - Добавить tests для uncovered paths
   - Пересмотреть coverage requirements

2. **Отсутствующие test cases**
   - Добавить missing test cases
   - Обновить test plan

3. **Flaky tests**
   - Стабилизировать flaky tests
   - Добавить proper isolation

4. **Медленные тесты**
   - Оптимизировать тесты
   - Рассмотреть parallel execution

### Повторный handoff

После исправлений:
- Пересоздать coverage report
- Обновить документацию
- Повторить handoff к verification

## Завершение процесса

### Успешное завершение

Когда все критерии выполнены:

```
✅ Задача тестирования завершена

**Результаты**:
- Unit tests: [X] тестов, все проходят ✅
- Integration tests: [X] тестов, все проходят ✅
- Coverage: [X]% (> [Y]% requirement) ✅
- Execution time: [X] сек ✅

**Артефакты**:
- tests/unit/[module]/test_*.py
- tests/integration/[module]/test_*.py
- tests/fixtures/[module]/
- htmlcov/index.html

**Документация**:
- README.md обновлен
- tests/CONVENTIONS.md создан

**QA Gate**: Пройден ✅
```

### Метрики качества

Для оценки качества тестов:

1. **Coverage**: Должен соответствовать требованиям (> 80%)
2. **Test execution time**: Unit < 5 сек, Integration < 30 сек
3. **Flaky test rate**: Должен быть 0%
4. **Test maintainability**: Тесты должны быть понятны и легко обновляться
5. **Documentation**: Документация должна быть полной и актуальной
