---
name: security-access-model
description: Проектирование модели безопасности и доступа
license: MIT
compatibility:
  opencode: ">=1.0.0"
metadata:
  author: Build Team
  version: 1.0.0
  tags: [security, access-control, authentication]
allowed-tools:
  - read
  - write
---

# Security Access Model

## Описание
Навык проектирования модели безопасности и доступа. Включает определение аутентификации, авторизации, ролей и разрешений, а также модели угроз.

## Когда использовать
- Создание новой системы
- Обновление безопасности существующей системы
- При проектировании доступа
- При аудите безопасности

## Когда НЕ использовать
- Для проверки уязвимостей кода
- Для написания конкретного кода безопасности
- Для проведения пентестов

## Входные данные
- Требования безопасности
- Архитектура системы
- Регуляторные требования
- Данные для защиты

## Выходные данные
- Security model
- Access control model
- Threat model
- Спецификация аутентификации
- Спецификация авторизации

## Зависимости
- architecture-design - для понимания архитектуры

## Режимы отказа
- Уязвимости в модели
- Чрезмерные ограничения
- Недостаточная защита
- Неправильная реализация

## Шаблоны и чек-листы

### Шаблон Security Model
```markdown
# Security Model: {Название системы}

## Authentication
### Methods
- API Key: для сервисов
- JWT: для пользователей
- OAuth2: для внешних систем

### Flow
1. User provides credentials
2. System validates
3. Returns token
4. Token used for requests

## Authorization
### Model
- RBAC (Role-Based Access Control)
- ABAC (Attribute-Based) для детального контроля

### Roles
| Role | Permissions |
|------|-------------|
| admin | full access |
| user | read/write own |
| viewer | read only |

### Permissions
- resource:action
- user:read
- document:write

## Threat Model
### Assets
- User data
- API keys
- Business logic

### Threats
| Threat | Mitigation |
|--------|------------|
| SQL Injection | Parameterized queries |
| XSS | Output encoding |
| CSRF | CSRF tokens |

## Data Protection
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- Key management: HashiCorp Vault
```

### Чек-лист
- [ ] Аутентификация определена
- [ ] Авторизация определена
- [ ] Угрозы идентифицированы
- [ ] Защита данных описана
- [ ] Роли и разрешения определены
- [ ] Compliance требования учтены
- [ ] Инциденты обработаны

## Usage
```json
{
  "tool": "skill",
  "name": "security-access-model"
}
```