# Implementation Engineer - Навыки (Skills)

## Обзор

Implementation Engineer использует следующие навыки для эффективной реализации кода.

## Навык: Clean Code Writing

### Описание
Способность писать чистый, читаемый и поддерживаемый код следуя best practices.

### Компоненты навыка

#### 1. Naming conventions
- Описательные имена переменных, функций, классов
- Согласованный стиль naming
- Избегание сокращений (если не standard)
- Context-aware naming

#### 2. Function design
- Функции должны быть короткими (< 20 строк)
- Single responsibility principle
- Минимум аргументов (максимум 3-4)
- Pure functions где применимо

#### 3. Code organization
- Logical grouping related code
- Разделение на модули и пакеты
- Proper file structure
- Import organization

#### 4. DRY (Don't Repeat Yourself)
- Избегание дублирования
- Использование helper functions
- Абстракция для повторяющихся patterns
- Template methods если применимо

### Примеры использования

**Хороший код**:
```python
def create_user(username: str, email: str) -> User:
    """
    Create a new user.

    Args:
        username: Unique username
        email: User email address

    Returns:
        Created user object
    """
    user = User(username=username, email=email)
    user.save()
    return user
```

**Плохой код**:
```python
def crt_usr(un: str, em: str):
    u = User(un=un, em=em)
    u.sv()
    return u
```

**Избегание дублирования**:
```python
# Bad: Duplicated code
def create_user(username: str, email: str) -> User:
    user = User(username=username, email=email)
    user.save()
    send_welcome_email(email)
    log_user_creation(user)
    return user

def create_admin(username: str, email: str) -> User:
    user = User(username=username, email=email, is_admin=True)
    user.save()
    send_welcome_email(email)
    log_user_creation(user)
    return user

# Good: Extracted common logic
def _create_user_and_notify(user: User) -> User:
    user.save()
    send_welcome_email(user.email)
    log_user_creation(user)
    return user

def create_user(username: str, email: str) -> User:
    user = User(username=username, email=email)
    return _create_user_and_notify(user)

def create_admin(username: str, email: str) -> User:
    user = User(username=username, email=email, is_admin=True)
    return _create_user_and_notify(user)
```

### Best Practices

- [ ] Использовать описательные имена
- [ ] Держать функции короткими
- [ ] Следовать SRP (Single Responsibility Principle)
- [ ] Избегать дублирования
- [ ] Организовывать код логически

## Навык: Testing

### Описание
Способность писать исчерпывающие тесты для обеспечения качества кода.

### Компоненты навыка

#### 1. Unit testing
- Тесты для всех public methods
- Тесты для edge cases
- Тесты для error paths
- Mocking dependencies

#### 2. Integration testing
- Тесты интеграций с внешними системами
- Database integration tests
- API integration tests
- Test fixtures

#### 3. Test organization
- Test classes и grouping
- Setup/teardown fixtures
- Parameterized tests
- Test naming conventions

#### 4. Coverage
- Target coverage (> 80%)
- Coverage для critical paths 100%
- Coverage reports
- Uncovered code review

### Примеры использования

**Unit tests**:
```python
import pytest
from unittest.mock import Mock, patch
from user_service import UserService, User

class TestUserService:
    """Tests for UserService."""

    def test_create_user_success(self) -> None:
        """Test successful user creation."""
        service = UserService()
        user = service.create_user(
            username="testuser",
            email="test@example.com"
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.id is not None

    def test_create_user_duplicate_username(self) -> None:
        """Test creating user with duplicate username."""
        service = UserService()
        service.create_user(
            username="testuser",
            email="test1@example.com"
        )

        with pytest.raises(DuplicateUsernameError):
            service.create_user(
                username="testuser",
                email="test2@example.com"
            )

    @patch("user_service.send_email")
    def test_welcome_email_sent(
        self,
        mock_send_email: Mock
    ) -> None:
        """Test that welcome email is sent."""
        service = UserService()
        user = service.create_user(
            username="testuser",
            email="test@example.com"
        )

        mock_send_email.assert_called_once_with(
            to="test@example.com",
            subject="Welcome!",
            body="Welcome to our service"
        )
```

**Integration tests**:
```python
import pytest
from user_service import UserService
from database import Database


@pytest.mark.integration
class TestUserServiceIntegration:
    """Integration tests for UserService.

    These tests require:
    - Database connection
    - Test database setup
    """

    @pytest.fixture
    def database(self) -> Database:
        """Create test database."""
        db = Database(test=True)
        db.setup()
        yield db
        db.teardown()

    def test_create_and_retrieve_user(
        self,
        database: Database
    ) -> None:
        """Test creating and retrieving user."""
        service = UserService(database=database)

        # Create user
        user = service.create_user(
            username="testuser",
            email="test@example.com"
        )

        # Retrieve user
        retrieved_user = service.get_user(user.id)

        assert retrieved_user.id == user.id
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
```

### Best Practices

- [ ] Тестировать все public methods
- [ ] Тестировать edge cases
- [ ] Mock external dependencies
- [ ] Достигать target coverage
- [ ] Держать tests быстрыми

## Навык: Error Handling

### Описание
Способность проектировать и реализовывать надежное error handling.

### Компоненты навыка

#### 1. Error types
- Custom exceptions
- Exception hierarchy
- Error codes
- Error messages

#### 2. Error handling patterns
- Try-except blocks
- Context managers
- Decorators для error handling
- Error logging

#### 3. Error propagation
- Raise exceptions appropriately
- Chain exceptions (raise ... from ...)
- Don't swallow exceptions
- Provide context

#### 4. Graceful degradation
- Fallback mechanisms
- Default values
- Retry logic
- Circuit breakers

### Примеры использования

**Custom exceptions**:
```python
class UserServiceError(Exception):
    """Base exception for user service errors."""
    pass


class DuplicateUsernameError(UserServiceError):
    """Raised when username already exists."""
    pass


class UserNotFoundError(UserServiceError):
    """Raised when user is not found."""
    pass


class InvalidEmailError(UserServiceError):
    """Raised when email is invalid."""
    pass
```

**Error handling**:
```python
def create_user(username: str, email: str) -> User:
    """
    Create a new user.

    Args:
        username: Unique username
        email: Valid email address

    Returns:
        Created user

    Raises:
        InvalidEmailError: If email is invalid
        DuplicateUsernameError: If username exists
        UserServiceError: If database error occurs
    """
    try:
        # Validate email
        if not is_valid_email(email):
            raise InvalidEmailError(f"Invalid email: {email}")

        # Check if username exists
        if user_exists(username):
            raise DuplicateUsernameError(
                f"Username '{username}' already exists"
            )

        # Create user
        user = User(username=username, email=email)
        user.save()
        return user

    except DatabaseError as e:
        logger.error(f"Database error creating user: {e}")
        raise UserServiceError("Failed to create user") from e
```

**Graceful degradation**:
```python
def get_user_preference(
    user_id: str,
    preference_key: str
) -> Optional[Any]:
    """
    Get user preference with fallback.

    Returns None if preference not found or on error.
    """
    try:
        return PreferenceService.get(user_id, preference_key)
    except PreferenceServiceError as e:
        logger.warning(
            f"Failed to get preference {preference_key} "
            f"for user {user_id}: {e}"
        )
        return None
```

### Best Practices

- [ ] Создавать custom exceptions
- [ ] Логировать ошибки с контекстом
- [ ] Не глотать exceptions
- [ ] Предоставлять fallback механизмы
- [ ] Использовать context managers

## Навык: Code Documentation

### Описание
Способность создавать исчерпывающую документацию для кода.

### Компоненты навыка

#### 1. Docstrings
- Google style docstrings
- Args documentation
- Returns documentation
- Raises documentation
- Examples

#### 2. Type hints
- Type annotations для всех функций
- Type aliases для сложных типов
- Generic types
- Optional types

#### 3. README documentation
- Installation instructions
- Usage examples
- API documentation links
- Contributing guidelines

#### 4. API documentation
- Autogenerated docs (Sphinx, MkDocs)
- Examples for all methods
- Tutorial documentation
- Migration guides

### Примеры использования

**Docstrings**:
```python
def create_user(
    username: str,
    email: str,
    is_admin: bool = False
) -> User:
    """
    Create a new user in the system.

    This method creates a new user with the specified username and email.
    The username must be unique. The email must be valid.

    Args:
        username: Unique username for the user (min 3 characters)
        email: Valid email address for the user
        is_admin: Whether the user has admin privileges (default False)

    Returns:
        The created User object with generated ID

    Raises:
        InvalidUsernameError: If username is invalid
        InvalidEmailError: If email is invalid
        DuplicateUsernameError: If username already exists
        DatabaseError: If database operation fails

    Examples:
        >>> user = create_user("john_doe", "john@example.com")
        >>> print(user.id)
        '123e4567-e89b-12d3-a456-426614174000'

        >>> admin = create_user(
        ...     "admin",
        ...     "admin@example.com",
        ...     is_admin=True
        ... )
        >>> admin.is_admin
        True
    """
    # Implementation here
```

**Type hints**:
```python
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """User data model."""
    id: str
    username: str
    email: str
    is_admin: bool = False


def get_users(
    limit: int = 10,
    offset: int = 0,
    is_admin: Optional[bool] = None
) -> List[User]:
    """
    Get list of users with pagination.

    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        is_admin: Filter by admin status (None = all)

    Returns:
        List of User objects
    """
    pass


def get_user_preferences(
    user_id: str
) -> Dict[str, Any]:
    """
    Get all preferences for a user.

    Args:
        user_id: User ID

    Returns:
        Dictionary of preference key-value pairs
    """
    pass
```

### Best Practices

- [ ] Docstrings для всех public functions
- [ ] Type hints для всех функций
- [ ] Examples в docstrings
- [ ] Обновлять README при изменениях
- [ ] Использовать Sphinx/MkDocs

## Навык: Code Review Participation

### Описание
Способность участвовать в code review конструктивно и эффективно.

### Компоненты навыка

#### 1. Reviewing code
- Проверка на bugs
- Проверка на security issues
- Проверка на performance problems
- Проверка на style violations

#### 2. Providing feedback
- Конструктивные комментарии
- Предложение improvements
- Обоснование каждого комментария
- Recognizing good work

#### 3. Receiving feedback
- Принимать constructive criticism
- Объяснять если не согласны
- Вносить изменения
- Request re-review

#### 4. Communication
- Respectful tone
- Focus on code, not on person
- Ask clarifying questions
- Provide context

### Примеры использования

**Good code review comment**:
```
## Suggestion

**Location**: user_service.py:123

**Issue**: The username validation logic is duplicated.

**Suggestion**: Extract to a helper function `_validate_username()`.

**Reasoning**: This will make the code DRY and easier to maintain.

**Example**:
```python
# Before
def create_user(username: str, email: str) -> User:
    if len(username) < 3:
        raise InvalidUsernameError(...)
    if not username.isalnum():
        raise InvalidUsernameError(...)
    # ...

def update_user(user_id: str, username: str) -> User:
    if len(username) < 3:
        raise InvalidUsernameError(...)
    if not username.isalnum():
        raise InvalidUsernameError(...)
    # ...

# After
def _validate_username(username: str) -> None:
    if len(username) < 3:
        raise InvalidUsernameError(...)
    if not username.isalnum():
        raise InvalidUsernameError(...)

def create_user(username: str, email: str) -> User:
    _validate_username(username)
    # ...

def update_user(user_id: str, username: str) -> User:
    _validate_username(username)
    # ...
```
```

**Bad code review comment**:
```
Username validation is duplicated.
Fix it.
```

**Responding to feedback**:
```
## Response to feedback on #456

@reviewer_name

Thank you for the review!

### Accepted
- ✅ Extract username validation to helper function
- ✅ Add type hints for all methods
- ✅ Improve error messages

### Not accepted (with explanation)
- ❌ Add logging to every method

**Reasoning**: Adding logging to every method would be excessive
and would negatively impact performance. We follow the principle
of logging only at entry/exit points for public methods and for
error conditions. This is already implemented in the current code.

### Follow-up actions
I've made the accepted changes and pushed to the PR.
Please take another look when you have time.
```

### Best Practices

- [ ] Конструктивный feedback
- [ ] Обоснование каждого комментария
- [ ] Focus на code, не на person
- [ ] Принимать feedback
- [ ] Request re-review после изменений

## Навык: Performance Optimization

### Описание
Способность оптимизировать код для лучшей performance.

### Компоненты навыка

#### 1. Profiling
- Использование профайлеров
- Identification bottlenecks
- Memory profiling
- Performance metrics

#### 2. Optimization techniques
- Algorithm optimization
- Caching
- Database query optimization
- Asynchronous operations

#### 3. Benchmarking
- Benchmark critical paths
- Compare before/after
- Performance regression tests
- Load testing

#### 4. Trade-offs
- Memory vs CPU
- Readability vs performance
- Complexity vs performance
- Optimization vs maintainability

### Примеры использования

**Caching**:
```python
from functools import lru_cache
from datetime import datetime, timedelta


@lru_cache(maxsize=1024)
def get_user(user_id: str) -> Optional[User]:
    """
    Get user with caching.

    Cache is automatically invalidated after maxsize entries.
    """
    return User.query.filter_by(id=user_id).first()


def get_user_with_ttl_cache(user_id: str) -> Optional[User]:
    """
    Get user with TTL caching.

    Cache invalidates after 1 hour.
    """
    cache_key = f"user:{user_id}"

    # Try cache
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Load from database
    user = User.query.filter_by(id=user_id).first()

    # Cache for 1 hour
    if user:
        cache.set(
            cache_key,
            user,
            timeout=timedelta(hours=1).total_seconds()
        )

    return user
```

**Async operations**:
```python
import asyncio
from typing import List


async def fetch_users(user_ids: List[str]) -> List[User]:
    """
    Fetch multiple users concurrently.

    This is much faster than sequential fetching.
    """
    tasks = [fetch_user(user_id) for user_id in user_ids]
    return await asyncio.gather(*tasks)


async def fetch_user(user_id: str) -> User:
    """Fetch a single user."""
    # Simulate async operation
    await asyncio.sleep(0.1)  # Simulate I/O
    return User.query.filter_by(id=user_id).first()
```

**Database optimization**:
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload


# Bad: N+1 query problem
def get_users_with_posts_bad() -> List[User]:
    users = User.query.all()  # 1 query
    result = []
    for user in users:
        user.posts  # N queries (one per user)
        result.append(user)
    return result  # Total: 1 + N queries


# Good: Eager loading
def get_users_with_posts_good() -> List[User]:
    stmt = (
        select(User)
        .options(selectinload(User.posts))
    )
    return User.session.execute(stmt).scalars().all()  # 2 queries
```

### Best Practices

- [ ] Профайлинг перед оптимизацией
- [ ] Benchmark до и после
- [ ] Кэширование где применимо
- [ ] Async для I/O bound operations
- [ ] Оптимизировать database queries

## Навык: Security Best Practices

### Описание
Способность писать безопасный код и избегать common vulnerabilities.

### Компоненты навыка

#### 1. Input validation
- Validate all inputs
- Sanitize user input
- Parameterized queries
- Type checking

#### 2. Authentication & authorization
- Secure password handling
- JWT tokens
- Role-based access control
- Principle of least privilege

#### 3. Data protection
- Encryption at rest
- Encryption in transit
- Data masking
- Secure deletion

#### 4. Common vulnerabilities
- SQL injection prevention
- XSS prevention
- CSRF protection
- Dependency vulnerabilities

### Примеры использования

**Input validation**:
```python
from pydantic import BaseModel, EmailStr, ValidationError


class CreateUserRequest(BaseModel):
    """Request model for user creation."""
    username: str
    email: EmailStr
    password: str

    def validate_password(self) -> None:
        """Validate password strength."""
        if len(self.password) < 8:
            raise ValueError(
                "Password must be at least 8 characters"
            )
        if not any(c.isupper() for c in self.password):
            raise ValueError(
                "Password must contain uppercase letter"
            )


def create_user(request: CreateUserRequest) -> User:
    """Create user with validated input."""
    request.validate_password()

    # Sanitize username
    username = request.username.strip().lower()

    # Hash password
    hashed = hash_password(request.password)

    user = User(
        username=username,
        email=request.email,
        password_hash=hashed
    )
    user.save()
    return user
```

**SQL injection prevention**:
```python
from sqlalchemy import text


# Bad: SQL injection vulnerable
def get_user_by_username_bad(username: str) -> User:
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return User.session.execute(text(query)).scalar_one()


# Good: Parameterized query
def get_user_by_username_good(username: str) -> User:
    stmt = select(User).where(User.username == username)
    return User.session.execute(stmt).scalar_one()


# Or with SQLAlchemy ORM
def get_user_by_username_orm(username: str) -> User:
    return User.query.filter_by(username=username).first()
```

**Password handling**:
```python
import bcrypt
from secrets import token_hex


def hash_password(password: str) -> str:
    """
    Hash password with bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(
        password.encode('utf-8'),
        salt
    ).decode('utf-8')


def verify_password(
    password: str,
    hashed: str
) -> bool:
    """
    Verify password against hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )


def generate_api_key() -> str:
    """
    Generate secure random API key.

    Returns:
        API key string
    """
    return token_hex(32)
```

### Best Practices

- [ ] Валидировать все inputs
- [ ] Использовать parameterized queries
- [ ] Хэшировать passwords
- [ ] Использовать HTTPS/TLS
- [ ] Проверять dependencies на vulnerabilities
