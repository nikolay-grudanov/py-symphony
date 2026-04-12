# Python Coder - Behavioral Style

## Clean Code

Приоритет чистоте кода:
- Читаемость важнее краткости
- Explicit over implicit
- DRY (Don't Repeat Yourself)
- Single Responsibility Principle
- Small, focused functions

## Modern Python

Использование современных возможностей Python 3.10+:
- match/case (structural pattern matching)
- type hints everywhere
- dataclasses
- walrus operator (:=) where appropriate
- f-strings

## PEP 8 Compliance

Строгое следование PEP 8:
- 88 символов max line length
- snake_case для functions/variables
- PascalCase для Classes
- UPPER_CASE для constants
- Proper spacing

## Type-First Thinking

Типизация как инструмент дизайна:
- Type hints для всех функций
- Type hints для всех переменных
- Custom types где нужно
- mypy compatibility

## Error Handling

Правильная обработка ошибок:
- Specific exceptions
- No bare except
- Proper logging
- Error messages in Russian for user-facing

## Documentation First

Документация в коде:
- Google-style docstrings
- Examples в docstrings
- Args, Returns, Raises sections

## Quality Criteria

- ✅ PEP 8 compliance
- ✅ Type hints everywhere
- ✅ Error handling
- ✅ Logging
- ✅ Tests
- ✅ Docstrings