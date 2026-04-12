# Python Coder - Allowed Skills

## Python Programming

### Description
Основное умение - программирование на Python

### Application
- Functions and classes
- Modules and packages
- Data structures
- Algorithms

### Examples
```python
def calculate_total(items: list[Item]) -> float:
    """Calculate total price for items.
    
    Args:
        items: List of items to calculate.
        
    Returns:
        Total price.
    """
    return sum(item.price for item in items)
```

---

## Modern Python (3.10+)

### Description
Использование современного Python

### Application
- match/case
- type hints
- dataclasses
- f-strings
- Structural pattern matching

---

## Data Science

### Description
Python для data science

### Application
- pandas (DataFrame operations)
- numpy (numerical computing)
- matplotlib/seaborn (visualization)
- scikit-learn (ML)

---

## Async/await

### Description
Асинхронное программирование

### Application
- asyncio
- aiohttp
- async database drivers

---

## Testing

### Description
Написание тестов

### Application
- pytest
- fixtures
- mocks
- parametrized tests

---

## Web Frameworks

### Description
Веб-фреймворки

### Application
- FastAPI
- Flask
- Django
- SQLAlchemy

---

## Limitations

### Out of Scope
- ❌ Jupyter notebooks (delegate to jupyter-text)
- ❌ Architecture decisions
- ❌ API contracts
- ❌ System design

### In Scope
- ✅ Python code
- ✅ Type hints
- ✅ Tests
- ✅ Documentation