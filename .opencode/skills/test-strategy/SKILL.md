---
name: test-strategy
description: Разработка стратегии тестирования для проекта
license: MIT
compatibility:
  opencode: ">=1.0.0"
metadata:
  author: Build Team
  version: 1.0.0
  tags: [testing, quality, strategy]
allowed-tools:
  - read
  - write
---

# Test Strategy

## Описание
Навык разработки стратегии тестирования для проекта. Включает определение уровней тестирования, критериев покрытия, инструментов и процессов.

## Когда использовать
- Создание нового проекта
- Обновление стратегии тестирования
- При планировании QA процессов
- При оценке качества проекта

## Когда НЕ использовать
- Для написания конкретных тестов
- Для проверки багов
- Для ревью кода

## Входные данные
- Архитектура системы
- Требования к качеству
- Критерии приёмки
- Ограничения (время, ресурсы)

## Выходные данные
- Test strategy document
- Test plan
- Цели покрытия
- Определение уровней тестирования
- Инструменты и фреймворки

## Зависимости
- architecture-design - для понимания архитектуры

## Режимы отказа
- Недостаточное покрытие
- Нереалистичные цели
- Неподходящие инструменты
- Пропущенные уровни тестирования

## Шаблоны и чек-листы

### Шаблон Test Strategy
```markdown
# Test Strategy: {Название проекта}

## Test Levels

### Unit Testing
- Purpose: Тестирование отдельных компонентов
- Tools: pytest, unittest
- Coverage Goal: 80%
- Approach: White-box

### Integration Testing
- Purpose: Тестирование взаимодействия компонентов
- Tools: pytest, testcontainers
- Coverage: Key flows
- Approach: Black-box

### E2E Testing
- Purpose: Тестирование пользовательских сценариев
- Tools: playwright, cypress
- Coverage: Critical paths
- Approach: Black-box

## Test Data Strategy
- Strategy: description
- Fixtures: description

## Quality Gates
- Unit tests pass: 100%
- Integration tests pass: 100%
- Coverage: > 80%
- No critical bugs

## Tools
| Tool | Purpose | Version |
|------|---------|---------|
| pytest | Unit testing | 7.x |
```

### Чек-лист
- [ ] Unit testing определён
- [ ] Integration testing определён
- [ ] E2E testing определён
- [ ] Цели покрытия заданы
- [ ] Инструменты выбраны
- [ ] Критерии приёмки определены
- [ ] Test data strategy описана

## Usage
```json
{
  "tool": "skill",
  "name": "test-strategy"
}
```