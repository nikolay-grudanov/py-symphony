---
name: observability-design
description: Проектирование observability для системы
license: MIT
compatibility:
  opencode: ">=1.0.0"
metadata:
  author: Build Team
  version: 1.0.0
  tags: [observability, monitoring, logging]
allowed-tools:
  - read
  - write
---

# Observability Design

## Описание
Навык проектирования observability для системы. Включает проектирование логирования, метрик, трейсинга и алертинга для обеспечения видимости работы системы.

## Когда использовать
- Создание новой системы
- Обновление observability в существующей системе
- При настройке мониторинга
- При расследовании инцидентов

## Когда НЕ использовать
- Для настройки конкретных метрик
- Для написания кода логирования
- Для настройки конкретных алертов

## Входные данные
- Архитектура системы
- Требования к мониторингу
- SLA/SLO требования
- Доступные инструменты

## Выходные данные
- Observability strategy
- Logging plan
- Metrics plan
- Tracing plan
- Alerting strategy

## Зависимости
- architecture-design - для понимания архитектуры
- security-access-model - для обеспечения безопасности данных мониторинга

## Режимы отказа
- Недостаточная видимость
- Проблемы с производительностью
- Слишком много данных
- Неправильные threshold

## Шаблоны и чек-листы

### Шаблон Observability Strategy
```markdown
# Observability Strategy: {Название системы}

## Logging
### Strategy
- Format: JSON
- Level: DEBUG, INFO, WARNING, ERROR
- Retention: 30 days

### Components
| Component | Log Level | Fields |
|-----------|-----------|--------|
| API | INFO | request_id, user_id |
| Service | DEBUG | trace_id, duration |

## Metrics
### Key Metrics
- request_duration_seconds (histogram)
- requests_total (counter)
- errors_total (counter)

### SLI
- Availability: > 99.9%
- Latency: p99 < 200ms

## Tracing
- Protocol: OpenTelemetry
- Sample Rate: 10%
- Context Propagation: W3C

## Alerting
| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | error_rate > 5% | critical |
| High Latency | p99 > 1s | warning |
```

### Чек-лист
- [ ] Логирование определено
- [ ] Метрики определены
- [ ] Трейсинг определён
- [ ] Алертинг настроен
- [ ] SLI/SLO определены
- [ ] Инструменты выбраны
- [ ] Retention policy определена
- [ ] Данные защищены

## Usage
```json
{
  "tool": "skill",
  "name": "observability-design"
}
```