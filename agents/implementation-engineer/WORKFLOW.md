# Implementation Engineer - Рабочий процесс

## Обзор процесса

Implementation Engineer следует workflow: изучение спецификаций → проектирование кода → написание кода → написание тестов → документация → code review.

## Шаг 1: Изучение спецификаций

### Анализ ADR

Изучить Architecture Decision Record:

```
## Анализ ADR: [Номер и название]

**Статус**: Accepted
**Approved by**: [архитектор]

**Контекст**:
- [ ] Проблема: [описание]
- [ ] Требования: [список]

**Решение**:
- [ ] Архитектурный подход: [описание]
- [ ] Паттерны: [список]
- [ ] Технологии: [список]

**Последствия**:
- Положительные: [список]
- Отрицательные: [список]

**Соответствие SPEC.md**:
- Разделы: [ссылки]
```

### Изучение спецификаций

Изучить технические спецификации:

- Контракты интеграции (OpenAPI, GraphQL schema)
- API спецификации если есть
- Диаграммы архитектуры
- Database schemas если применимо

### Изучение существующего кода

Изучить существующую codebase:

- Связанный код (dependencies)
- Code standards проекта
- Существующие patterns
- Библиотеки в use

## Шаг 2: Проектирование кода

### Декомпозиция

Разбить функциональность на модули/функции:

```
## Декомпозиция: [Название]

**Модули**:
- [ ] module1.py: [функциональность]
- [ ] module2.py: [функциональность]

**Функции**:
- [ ] function1(args): [описание]
- [ ] function2(args): [описание]

**Классы**:
- [ ] Class1: [описание]
- [ ] Class2: [описание]
```

### Проектирование интерфейсов

Определить public APIs:

```
## Public API: [Название]

**Functions**:
```python
def public_function(arg1: str, arg2: int) -> Result:
    """
    Description of function.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Result object

    Raises:
        ErrorType: When condition
    """
```

**Classes**:
```python
class PublicClass:
    """
    Description of class.
    """

    def method1(self, arg: str) -> Result:
        """
        Description of method.
        """
```
```

### Проектирование структуры данных

Определить data structures:

```
## Data Structures

**Models**:
```python
@dataclass
class Model:
    """Description of model."""
    field1: str
    field2: int
```

**DTOs**:
```python
@dataclass
class DTO:
    """Description of DTO."""
    field: str
```
```

### Проверка feasibility

Проверить что все requirements реализуемы:

- [ ] Все функциональные требования покрыты
- [ ] Non-functional требования достижимы (performance, security)
- [ ] Все dependencies доступны
- [ ] Выбранный стек поддерживает требования

## Шаг 3: Написание кода

### Подготовка окружения

Настроить development окружение:

```bash
# Create feature branch
git checkout -b feature/adr-XXX-feature

# Install dependencies
pip install -r requirements.txt

# Run tests (baseline)
pytest
```

### Написание кода

Следовать принципам:

**Clean code**:
- Имена переменные и функции должны быть описательными
- Functions должны быть короткими и focused
- DRY (Don't Repeat Yourself)
- SOLID principles где применимо

**Code standards**:
- PEP 8 compliance
- Type hints для всех функций
- Docstrings для всех public functions/classes
- Error handling

### Пример кода

```python
"""
Модуль для работы с Linear API.
"""

from dataclasses import dataclass
from typing import Optional
import httpx


@dataclass
class LinearIssue:
    """Модель issue из Linear."""
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: int


class LinearClient:
    """
    Клиент для работы с Linear API.

    Examples:
        >>> client = LinearClient(api_key="your-key")
        >>> issue = client.create_issue(
        ...     title="Example",
        ...     description="Example description"
        ... )
        >>> print(issue.id)
    """

    def __init__(self, api_key: str) -> None:
        """
        Инициализация клиента.

        Args:
            api_key: Linear API key

        Raises:
            ValueError: Если api_key пустой
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        self.api_key = api_key
        self.base_url = "https://api.linear.app/graphql"
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

    def create_issue(
        self,
        title: str,
        description: Optional[str] = None
    ) -> LinearIssue:
        """
        Создание issue в Linear.

        Args:
            title: Заголовок issue
            description: Описание issue (опционально)

        Returns:
            LinearIssue объект

        Raises:
            httpx.HTTPError: При ошибке HTTP запроса
            LinearError: При ошибке API
        """
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    title
                    description
                    state {
                        name
                    }
                    priority
                }
            }
        }
        """

        try:
            response = self.client.post(
                self.base_url,
                json={
                    "query": mutation,
                    "variables": {
                        "input": {
                            "title": title,
                            "description": description
                        }
                    }
                }
            )
            response.raise_for_status()

            data = response.json()
            if not data["data"]["issueCreate"]["success"]:
                raise LinearError("Failed to create issue")

            issue_data = data["data"]["issueCreate"]["issue"]
            return LinearIssue(
                id=issue_data["id"],
                title=issue_data["title"],
                description=issue_data["description"],
                status=issue_data["state"]["name"],
                priority=issue_data["priority"]
            )

        except httpx.HTTPError as e:
            raise LinearError(f"HTTP error: {e}") from e
```

### Error handling

Внедрить error handling:

```python
class LinearError(Exception):
    """Base exception for Linear errors."""
    pass


class LinearAuthenticationError(LinearError):
    """Authentication error."""
    pass


class LinearRateLimitError(LinearError):
    """Rate limit error."""
    pass


def handle_linear_error(response: httpx.Response) -> None:
    """
    Обработка ошибок Linear API.

    Args:
        response: HTTP response от Linear API

    Raises:
        LinearAuthenticationError: При 401
        LinearRateLimitError: При 429
        LinearError: При других ошибках
    """
    status_code = response.status_code

    if status_code == 401:
        raise LinearAuthenticationError("Invalid API key")
    elif status_code == 429:
        raise LinearRateLimitError("Rate limit exceeded")
    elif status_code >= 400:
        raise LinearError(f"Linear API error: {status_code}")
```

## Шаг 4: Написание тестов

### Unit tests

Написать unit tests для всех методов:

```python
import pytest
from unittest.mock import Mock, patch
from linear import LinearClient, LinearIssue


class TestLinearClient:
    """Тесты для LinearClient."""

    def test_init_with_valid_key(self) -> None:
        """Тест инициализации с валидным ключом."""
        client = LinearClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.linear.app/graphql"

    def test_init_with_empty_key_raises_error(self) -> None:
        """Тест что пустой ключ вызывает ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            LinearClient(api_key="")

    @patch("linear.httpx.Client")
    def test_create_issue_success(self, mock_client_class: Mock) -> None:
        """Тест успешного создания issue."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-id",
                        "title": "Test Issue",
                        "description": "Test description",
                        "state": {"name": "Backlog"},
                        "priority": 0
                    }
                }
            }
        }
        mock_client_class.return_value.post.return_value = mock_response

        client = LinearClient(api_key="test-key")
        issue = client.create_issue(
            title="Test Issue",
            description="Test description"
        )

        assert issue.id == "issue-id"
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.status == "Backlog"
        assert issue.priority == 0

    @patch("linear.httpx.Client")
    def test_create_issue_with_rate_limit(self, mock_client_class: Mock) -> None:
        """Тест что rate limit вызывает ошибку."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit",
            request=Mock(),
            response=mock_response
        )
        mock_client_class.return_value.post.return_value = mock_response

        client = LinearClient(api_key="test-key")

        with pytest.raises(LinearRateLimitError):
            client.create_issue(title="Test Issue")
```

### Integration tests

Написать integration tests (для интеграций):

```python
import pytest
from linear import LinearClient


@pytest.mark.integration
class TestLinearClientIntegration:
    """Интеграционные тесты для LinearClient.

    These tests require:
    - Valid Linear API key
    - Linear test account
    """

    @pytest.fixture
    def client(self) -> LinearClient:
        """Fixture для создания клиента."""
        api_key = pytest.config.getoption("--linear-api-key")
        if not api_key:
            pytest.skip("Linear API key not provided")
        return LinearClient(api_key=api_key)

    def test_create_and_get_issue(self, client: LinearClient) -> None:
        """Тест создания и получения issue."""
        # Create issue
        issue = client.create_issue(
            title="Integration Test Issue",
            description="This is an integration test"
        )

        assert issue.id is not None
        assert issue.title == "Integration Test Issue"

        # Get issue
        fetched_issue = client.get_issue(issue.id)
        assert fetched_issue.id == issue.id
```

### Test coverage

Достичь target coverage:

```bash
# Run tests with coverage
pytest --cov=linear --cov-report=html

# Check coverage
# Target: > 80%
```

## Шаг 5: Документация

### Docstrings

Добавить docstrings для всех public functions/classes:

- Description функции/класса
- Args для каждого аргумента
- Returns описание возвращаемого значения
- Raises для всех возможных exceptions
- Examples где применимо

### README

Обновить README если API изменился:

```markdown
## Usage

```python
from linear import LinearClient

client = LinearClient(api_key="your-key")

# Create issue
issue = client.create_issue(
    title="Example",
    description="Example description"
)

print(f"Issue ID: {issue.id}")
```

### API documentation

Создать API documentation если применимо:

- Использовать Sphinx
- Autogenerate из docstrings
- Примеры использования

## Шаг 6: Code review

### Создание Pull Request

Создать PR с описанием:

```markdown
## Description

Implement Linear API integration according to ADR-025.

### Changes
- Add LinearClient class
- Implement OAuth2 authentication
- Implement create_issue method
- Add error handling

### ADR
- ADR-025: Linear API Integration Contract

### Tests
- Unit tests: 85% coverage
- Integration tests: 3 scenarios

### Documentation
- Docstrings: Complete
- README: Updated

### Checklist
- [ ] Code follows ADR-025
- [ ] Code follows PEP 8
- [ ] All tests pass
- [ ] Docstrings complete
- [ ] README updated
```

### Обработка feedback

Обработать комментарии от reviewers:

- Принять constructive feedback
- Объяснить если не согласны
- Внести изменения

### Обновление PR

Обновить PR после внесения изменений:

- Push изменения в branch
- Request re-review
- Цитировать какие изменения внесены

## Завершение

### Final checklist

Перед завершением:

- [ ] Код соответствует ADR
- [ ] Код соответствует code standards
- [ ] Все unit tests проходят
- [ ] Интеграционные тесты проходят
- [ ] Test coverage > 80%
- [ ] Docstrings для всех public functions
- [ ] README обновлен если нужно
- [ ] PR создан и готов к review
- [ ] CI/CD passes

### Подготовка к передаче verification-agent

Подготовить передачу:

```
## Handoff: Реализация ADR-025

**ADR**: ADR-025
**Спецификация**: docs/integrations/linear/openapi.yaml

**Реализация**:
- [ ] LinearClient class
- [ ] OAuth2 authentication
- [ ] create_issue method
- [ ] Error handling

**Тесты**:
- Unit tests: 85% coverage
- Integration tests: 3 scenarios
- All passing: ✅

**Документация**:
- Docstrings: Complete
- README: Updated

**Pull Request**: #456
**CI/CD**: Passing ✅

**Next**: Verification by verification-agent
```
