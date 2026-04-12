# Python Coder - Workflow

## Workflow Overview

Python Coder следует workflow: Planning → Implementation → Testing → Documentation

## Step 1: Task Analysis

### Понимание требований
- Прочитать SPEC.md
- Понять требования к реализации
- Определить зависимости
- Оценить сложность

### Планирование
```
## Analysis
- Что нужно реализовать: [description]
- Требования: [list]
- Зависимости: [list]
- Оценка времени: [estimation]
```

## Step 2: Implementation

### Code Structure
1. **Создать файл(ы)**
   - Определить структуру модуля
   - Создать необходимые файлы

2. **Type-First Design**
   - Определить типы входных данных
   - Определить типы выходных данных
   - Определить исключения

3. **Implementation**
```python
# template.py
"""Module description."""

from typing import TypeAlias

class Error(Exception):
    """Base error."""
    pass

class ValidationError(Error):
    """Validation error."""
    pass

type Result: TypeAlias = dict[str, Any]

def process(data: dict[str, Any]) -> Result:
    """Process data.
    
    Args:
        data: Input data.
        
    Returns:
        Processed result.
        
    Raises:
        ValidationError: If validation fails.
    """
    # Implementation
```

### Standards
- 88 char line length
- Type hints everywhere
- Google docstrings
- PEP 8

## Step 3: Testing

### Unit Tests
```python
# test_module.py
import pytest
from module import process, ValidationError

def test_process_valid():
    """Test valid input."""
    result = process({"key": "value"})
    assert result == {"key": "value"}

def test_process_invalid():
    """Test invalid input."""
    with pytest.raises(ValidationError):
        process({})
```

### Test Coverage
- Happy path
- Edge cases
- Error cases

## Step 4: Documentation

### Docstrings
- Module-level docstring
- Class docstrings
- Function docstrings
- Examples

## Handoff Points

### Test Engineer
Передача для дополнительных тестов

### Verification Agent
Передача для верификации реализации

### Jupyter Text
Для создания ноутбуков