# Test Engineer - Навыки (Skills)

## Обзор

Test Engineer использует следующие навыки для эффективного создания и поддержания качественного тестового покрытия.

## Навык: Написание Unit Tests (Unit Testing)

### Описание
Способность создавать эффективные unit tests, которые изолированно тестируют отдельные компоненты системы.

### Компоненты навыка

#### 1. Структурирование unit test
- Использование Given-When-Then паттерна
- Ясные и описательные имена тестов
- Изоляция от внешних зависимостей
- Простая и понятная логика

#### 2. Покрытие сценариев
- Happy path testing
- Error path testing
- Edge case testing
- Invalid input testing

#### 3. Использование assertions
- Правильный выбор assertion методов
- Ясные error messages
- Множественные assertions когда нужно
- Использование custom assertions

#### 4. Mocking и stubbing
- Правильное использование mocks
- Stub внешних зависимостей
- Mock возвращаемых значений
- Mock исключений

### Примеры использования

```python
def test_process_payment_success():
    """
    Тестовый сценарий: Успешная обработка платежа
    
    Given: Валидный payment request
    When: Вызывается process_payment
    Then: Возвращается успешный response
    """
    # Arrange
    request = PaymentRequest(amount=100.00, currency="USD")
    provider = Mock()
    provider.process.return_value = PaymentResponse(success=True, transaction_id="123")
    service = PaymentService(provider)
    
    # Act
    result = service.process_payment(request)
    
    # Assert
    assert result.success is True
    assert result.transaction_id == "123"
    provider.process.assert_called_once_with(request)

def test_process_payment_invalid_amount():
    """
    Тестовый сценарий: Некорректная сумма платежа
    
    Given: Payment request с отрицательной суммой
    When: Вызывается process_payment
    Then: Возбуждается ValidationError
    """
    # Arrange
    request = PaymentRequest(amount=-50.00, currency="USD")
    provider = Mock()
    service = PaymentService(provider)
    
    # Act & Assert
    with pytest.raises(ValidationError, match="Amount must be positive"):
        service.process_payment(request)
```

## Навык: Написание Integration Tests (Integration Testing)

### Описание
Способность создавать integration tests, которые проверяют взаимодействие компонентов и систем.

### Компоненты навыка

#### 1. Определение test scope
- Выбор компонентов для интеграции
- Определение грани теста
- Изоляция от внешних систем через mocks

#### 2. Setup и teardown
- Создание test database
- Настройка test environment
- Cleanup после теста
- Использование fixtures для reuse

#### 3. Mock внешних систем
- Mock API calls
- Mock database queries
- Mock message queues
- Mock file system operations

#### 4. Тестирование workflows
- End-to-end сценарии
- Multi-step workflows
- Error scenarios в workflows
- Retry и fallback логика

### Примеры использования

```python
@pytest.fixture
def test_database():
    """Создает test database для integration tests"""
    db = create_test_database()
    db.seed_with_test_data()
    yield db
    db.cleanup()

@patch('services.payment.PaymentProvider')
def test_payment_complete_workflow(mock_provider, test_database):
    """
    Тестовый сценарий: Полный сценарий оплаты
    
    Given: Пользователь с достаточным балансом
    When: Пользователь делает платеж
    Then: Баланс уменьшается, транзакция записана, provider вызван
    """
    # Arrange
    user = test_database.get_user(user_id=1)
    mock_provider.process.return_value = PaymentResponse(success=True, transaction_id="123")
    service = PaymentService(mock_provider, test_database)
    
    # Act
    result = service.process_payment(user.id, amount=100.00)
    
    # Assert
    assert result.success is True
    assert result.transaction_id == "123"
    
    # Verify database state
    updated_user = test_database.get_user(user_id=1)
    assert updated_user.balance == user.balance - 100.00
    
    # Verify provider was called
    mock_provider.process.assert_called_once()
    
    # Verify transaction recorded
    transactions = test_database.get_transactions(user_id=1)
    assert len(transactions) == 1
    assert transactions[0].amount == 100.00
```

## Навык: Создание Test Fixtures (Test Fixture Design)

### Описание
Способность создавать reusable test fixtures для ускорения разработки тестов.

### Компоненты навыка

#### 1. Определение fixture scope
- Function scope (по умолчанию)
- Class scope
- Module scope
- Session scope

#### 2. Data fixtures
- Создание test data
- Генерация случайных данных
- Factory pattern для объектов
- Fixtures для edge cases

#### 3. Mock fixtures
- Mock внешних сервисов
- Stub database queries
- Setup default mock behaviors

#### 4. Environment fixtures
- Test database setup
- Test environment variables
- File system fixtures

### Примеры использования

```python
# Data fixtures
@pytest.fixture
def payment_request():
    """Создает валидный payment request"""
    return PaymentRequest(
        amount=100.00,
        currency="USD",
        card_number="4111111111111111",
        exp_month=12,
        exp_year=2025,
        cvv="123"
    )

@pytest.fixture
def user_with_balance(test_database):
    """Создает пользователя с балансом"""
    user = test_database.create_user(
        name="Test User",
        balance=1000.00
    )
    yield user
    test_database.delete_user(user.id)

# Mock fixtures
@pytest.fixture
def mock_payment_provider():
    """Mock для payment provider"""
    with patch('services.payment.PaymentProvider') as mock:
        mock.process.return_value = PaymentResponse(success=True, transaction_id="123")
        yield mock

# Environment fixtures
@pytest.fixture(scope="session")
def test_database():
    """Создает test database для всей сессии"""
    db = create_test_database()
    yield db
    db.cleanup()

# Использование fixtures
def test_payment_with_user_and_provider(payment_request, user_with_balance, mock_payment_provider):
    service = PaymentService(mock_payment_provider)
    result = service.process_payment(user_with_balance.id, payment_request.amount)
    assert result.success is True
```

## Навык: Анализ Coverage (Coverage Analysis)

### Описание
Способность анализировать test coverage и определять areas для улучшения.

### Компоненты навыка

#### 1. Чтение coverage reports
- Понимание coverage percentages
- Идентификация uncovered lines
- Анализ branch coverage
- Определение critical uncovered paths

#### 2. Улучшение coverage
- Добавление tests для uncovered lines
- Определение dead code
- Пересмотр coverage requirements
- Удаление unreachable code

#### 3. Анализ coverage trends
- Отслеживание coverage over time
- Идентификация decreasing coverage
- Установка coverage goals

#### 4. Balancing coverage vs. quality
- Не гонка за 100% coverage
- Фокус на critical paths
- Приоритизация business logic

### Примеры использования

```
## Coverage Report Analysis

**Module**: PaymentService
**Current Coverage**: 75% (Target: > 80%)

**Uncovered Lines**:
- Line 45: _retry_logic - error path not tested
- Line 78: refund - partial refund edge case
- Line 90: _validate - invalid currency not tested

**Action Items**:
1. Add test_retry_max_attempts_reached() for line 45
2. Add test_refund_partial_amount() for line 78
3. Add test_validate_invalid_currency() for line 90

**Estimated Coverage After Actions**: 87%
```

## Навык: Отладка Flaky Tests (Flaky Test Debugging)

### Описание
Способность идентифицировать и исправлять flaky tests.

### Компоненты навыка

#### 1. Идентификация причин flakiness
- Race conditions
- Timing dependencies
- Uninitialized state
- External dependencies

#### 2. Стабилизация tests
- Добавление explicit waits
- Isolation тестов
- Proper setup/teardown
- Deterministic test data

#### 3. Повторное выполнение тестов
- Использование pytest-rerunfailures
- Идентификация паттерна failure
- Логирование для debug

#### 4. Refactoring flaky tests
- Переписывание test logic
- Упрощение теста
- Разбиение на multiple tests

### Примеры использования

```python
# Flaky test (timing dependency)
def test_async_payment():
    service = PaymentService()
    service.process_payment_async(request)
    # Flaky: response может не быть готов
    assert service.get_status("123") == "completed"

# Fixed: добавлен явный wait
@pytest.mark.timeout(5)
def test_async_payment_fixed():
    service = PaymentService()
    future = service.process_payment_async(request)
    # Явный wait с polling
    status = wait_for_status(
        lambda: service.get_status("123"),
        expected="completed",
        timeout=5
    )
    assert status == "completed"
```

## Навык: Оптимизация Test Performance (Test Performance Optimization)

### Описание
Способность оптимизировать производительность тестов для быстрого выполнения.

### Компоненты навыка

#### 1. Идентификация медленных тестов
- Использование pytest --durations
- Профилирование тестов
- Идентификация bottlenecks

#### 2. Оптимизация test setup
- Использование fixtures для reuse
- Minimizing database operations
- Lazy loading test data

#### 3. Параллельное выполнение
- Использование pytest-xdist
- Разделение independent tests
- Использование process isolation

#### 4. Кэширование результатов
- Кэширование expensive operations
- Mock внешних API calls
- In-memory database для тестов

### Примеры использования

```bash
# Идентификация медленных тестов
pytest --durations=10

# Параллельное выполнение (4 workers)
pytest -n 4

# Профилирование
pytest --profile
```

## Комбинирование навыков

### Пример полного сценария

```
## Сценарий: Создание тестов для PaymentService

### Шаг 1: Unit Testing
- Анализ кода PaymentService
- Создание unit tests для всех методов
- Покрытие happy path, error path, edge cases
- Использование mocks для external dependencies

### Шаг 2: Integration Testing
- Определение integration points
- Создание integration tests для workflows
- Mock external providers
- Test с test database

### Шаг 3: Test Fixture Design
- Создание fixtures для common test data
- Создание mock fixtures для providers
- Создание environment fixtures для database

### Шаг 4: Coverage Analysis
- Генерация coverage report
- Анализ uncovered lines
- Добавление missing tests
- Достижение coverage > 80%

### Шаг 5: Performance Optimization
- Идентификация медленных тестов
- Оптимизация setup с fixtures
- Настройка parallel execution

### Результат:
- 45 unit tests, 10 integration tests
- Coverage: 87%
- Execution time: 4.2 сек
- No flaky tests
```

## Метрики эффективности

Для оценки эффективности Test Engineer используются следующие метрики:

1. **Coverage**: Процент покрытого кода
   - Цель: > 80%

2. **Test execution time**: Время выполнения всех тестов
   - Unit tests: < 5 сек
   - Integration tests: < 30 сек

3. **Flaky test rate**: Процент flaky tests
   - Цель: 0%

4. **Test maintainability**: Сложность поддержки тестов
   - Цель: Высокая (легко читать и обновлять)

5. **Documentation quality**: Качество тестовой документации
   - Цель: README обновлен, conventions задокументированы
