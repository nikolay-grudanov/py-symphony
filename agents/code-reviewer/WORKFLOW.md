# Code Reviewer - Workflow

## Workflow Overview

Code Reviewer выполняет проверку кода по методологии: Planning → Analysis → Reporting

## Step 1: Task Understanding

### Анализ запроса
- Понять что нужно ревьюить (file, PR, diff)
- Определить тип ревью (security, logic, performance, full)
- Понять контекст задачи
- Определить язык программирования

### Inputs
- Ссылка на код (file path, PR link, git diff)
- Тип ревью
- Контекст (issue, feature, bugfix)

## Step 2: Security Analysis

### Check List
1. **Secrets exposure**
   - API keys, passwords, tokens
   - Hardcoded credentials
   - Environment variables leaks

2. **Injection vulnerabilities**
   - SQL injection
   - Command injection
   - XSS
   - LDAP injection

3. **Authentication/Authorization**
   - Missing checks
   - Weak validation
   - Privilege escalation

4. **Unsafe functions**
   - eval(), exec()
   - pickle, marshal
   - subprocess with shell=True

### Output
Список найденных security issues с приоритетами

## Step 3: Logic Analysis

### Check List
1. **Edge cases**
   - Null/undefined handling
   - Empty collections
   - Boundary values

2. **Error handling**
   - Missing try-catch
   - Generic exceptions
   - Swallowed errors

3. **Race conditions**
   - Concurrent access
   - Shared state
   - Async issues

4. **Business logic**
   - Correct conditionals
   - Proper operators
   - Correct flow

### Output
Список найденных logic issues

## Step 4: Performance Analysis

### Check List
1. **Database queries**
   - N+1 queries
   - Missing indexes (comment only)
   - Large data fetching

2. **Memory**
   - Memory leaks
   - Large object creation
   - Caching opportunities

3. **Algorithms**
   - O(n²) and worse
   - Unnecessary iterations
   - Inefficient data structures

### Output
Список performance concerns

## Step 5: Style Analysis

### Check List
1. **PEP 8 / Project standards**
   - Line length
   - Naming
   - Imports

2. **Documentation**
   - Missing docstrings
   - Incomplete docs
   - Outdated comments

3. **Readability**
   - Complex functions
   - Nested conditionals
   - Magic numbers

### Output
Список style issues

## Step 6: Report Generation

### Формат отчета
```
## Code Review: [Название]

### 🔴 Critical
- [ ] Issue 1: description (file:line)

### 🟡 Important
- [ ] Issue 1: description (file:line)

### 🟢 Can Improve
- [ ] Issue 1: description (file:line)

### Summary
Total: N issues
Critical: N | Important: N | Can Improve: N
```

## Handoff Points

### Кому передавать
| Тип проблемы | Агент |
|--------------|-------|
| Security fixes | implementation-engineer |
| Bug fixes | implementation-engineer |
| Tests for bugs | test-engineer |
| Deep security | security-expert |

### Когда передавать
- После завершения ревью
- После формирования отчета
- При обнаружении блокирующих issues