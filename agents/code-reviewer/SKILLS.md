# Code Reviewer - Allowed Skills

## Security Analysis

### Description
Анализ кода на предмет уязвимостей безопасности

### Application
- SQL injection проверка
- XSS vulnerability detection
- CSRF protection verification
- Secrets detection
- Unsafe function usage

### Examples
```python
# BAD: SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD: Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

---

## Logic Analysis

### Description
Анализ логики работы кода и выявление багов

### Application
- Edge cases analysis
- Error handling verification
- Race conditions detection
- Null/undefined handling

### Examples
- Missing null checks
- Incorrect loop boundaries
- Wrong operator precedence

---

## Performance Analysis

### Description
Анализ производительности кода

### Application
- N+1 query detection
- Memory leak identification
- Algorithmic complexity
- Resource usage

### Examples
```python
# BAD: N+1 queries
for user in users:
    orders = get_orders(user.id)
    print(orders)

# GOOD: Eager loading
users = get_users_with_orders()
```

---

## Code Style Analysis

### Description
Проверка соответствия code style

### Application
- PEP 8 compliance
- Naming conventions
- Documentation standards
- Readability

---

## Diff Analysis

### Description
Анализ git diff для pull request review

### Application
- Changed lines analysis
- Context understanding
- Line-by-line review

---

## Documentation Review

### Description
Проверка качества документации

### Application
- Docstring verification
- Comment quality
- README completeness

---

## Limitations

### Out of Scope
- ❌ Writing code
- ❌ Implementing fixes
- ❌ Changing standards

### In Scope
- ✅ Security analysis
- ✅ Logic analysis
- ✅ Performance analysis
- ✅ Style analysis
- ✅ Reporting