---
name: architecture-review
description: Проверка архитектуры на соответствие требованиям
license: MIT
compatibility:
  opencode: ">=1.0.0"
metadata:
  author: Build Team
  version: 1.0.0
  tags: [architecture, review, quality]
allowed-tools:
  - read
  - write
---

# Architecture Review

## Описание
Навык проверки архитектуры на соответствие требованиям и качество. Включает анализ архитектурных решений, выявление проблем и предоставление рекомендаций.

## Когда использовать
- После создания архитектуры, перед реализацией
- При рефакторинге существующей системы
- При аудите архитектуры
- При передаче проекта другой команде

## Когда НЕ использовать
- Для проверки качества кода
- Для ревью отдельных pull requests
- Для написания кода

## Входные данные
- Архитектурные документы (SDD, ADR)
- Требования к системе
- Схемы и диаграммы
- Предыдущие ревью (если есть)

## Выходные данные
- Review report
- Выявленные проблемы
- Рекомендации по улучшению
- Оценка соответствия требованиям

## Зависимости
- architecture-design - для понимания архитектуры

## Режимы отказа
- Пропущенные проблемы
- Неясные рекомендации
- Субъективная оценка
- Недостаточная детализация

## Шаблоны и чек-листы

### Шаблон Architecture Review Report
```markdown
# Architecture Review Report
## Project: {Название проекта}
## Date: {Дата}

## Executive Summary
Краткое резюме обзора

## Findings

### Critical
- Issue: description
- Recommendation: fix

### Major
- Issue: description
- Recommendation: fix

### Minor
- Issue: description
- Recommendation: fix

## Requirements Compliance
| Requirement | Status | Notes |
|-------------|--------|-------|
| Req 1 | Met | |
| Req 2 | Partial | Notes |

## Tradeoffs Analysis
- Tradeoff: description
  - Decision: решение
  - Rationale: обоснование

## Recommendations
1. Recommendation 1
2. Recommendation 2
```

### Чек-лист
- [ ] Требования выполнены
- [ ] Компромиссы оценены
- [ ] Противоречия отсутствуют
- [ ] Масштабируемость учтена
- [ ] Безопасность проверена
- [ ] Производительность оценена
- [ ] Рекомендации конкретны

## Usage
```json
{
  "tool": "skill",
  "name": "architecture-review"
}
```