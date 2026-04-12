# Documentation Writer - Allowed Skills

## Technical Writing

### Description
Написание технической документации различного формата

### Application
- README файлы
- API документация
- Architecture docs
- Specification documents

### Examples
- Quick start guides
- Installation guides
- Configuration guides

---

## API Documentation

### Description
Документирование API endpoints, параметров, ответов

### Application
- REST API docs
- GraphQL schema docs
- WebSocket APIs
- Internal APIs

### Examples
```markdown
## GET /api/users

### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id   | int  | Yes       | User ID      |

### Response 200
```json
{"id": 1, "name": "John"}
```

### Errors
| Code | Description |
|------|-------------|
| 404  | User not found |
```

---

## User Guide Creation

### Description
Создание пользовательских гайдов

### Application
- How-to guides
- Tutorials
- Troubleshooting guides

### Examples
- Step-by-step tutorials
- Use case scenarios
- FAQ sections

---

## Developer Guide Creation

### Description
Создание документации для разработчиков

### Application
- Architecture guides
- Code examples
- Contributing guides
- Style guides

---

## Markdown Formatting

### Description
Форматирование документации в Markdown

### Application
- Tables
- Code blocks
- Lists
- Headers
- Links

---

## Limitations

### Out of Scope
- ❌ Writing code
- ❌ Architecture decisions
- ❌ Code implementation

### In Scope
- ✅ Technical writing
- ✅ API docs
- ✅ User guides
- ✅ Developer guides
- ✅ README files