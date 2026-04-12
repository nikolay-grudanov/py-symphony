# Transition Rules

## Overview

Правила переходов для всех state machines в платформе оркестрации. Определяет допустимые переходы, precondition, postcondition и уведомления.

## Platform State Machine Transitions

### Bootstrap → ArchitectureDesign

**Valid Transition**: ✅ Yes

**Preconditions**:
- Repository инициализирован
- Базовая директория структура создана
- CI/CD пайплайн настроен
- Build Orchestrator активирован
- Все зависимости установлены

**Postconditions**:
- Platform Architect назначен
- Требования собраны и документированы
- Переход к проектированию архитектуры

**Invalid If**:
- CI/CD не настроен
- Repository недоступен
- Базовая структура не создана

**State Change Notifications**:
- Build Orchestrator → Platform Architect
- Update backlog status
- Notify development team

---

### ArchitectureDesign → Implementation

**Valid Transition**: ✅ Yes

**Preconditions**:
- SDD (Software Design Description) завершен и утвержден
- Все ADR (Architecture Decision Records) созданы
- Модель безопасности определена
- Компоненты специфицированы
- Интеграционные контракты определены
- Технологический стек утвержден

**Postconditions**:
- Implementation Engineer назначен
- Технический стек определен
- Начало реализации компонентов
- Architecture blueprint доступен

**Invalid If**:
- SDD не завершен
- ADR отсутствуют
- Модель безопасности не определена
- Компоненты не специфицированы

**State Change Notifications**:
- Build Orchestrator → Implementation Engineer
- Update task status
- Notify development team
- Create implementation backlog

---

### Implementation → Verification

**Valid Transition**: ✅ Yes

**Preconditions**:
- Все компоненты реализованы
- Unit tests написаны и пройдены
- API документация создана
- Code review пройден
- Все зависимости интегрированы
- Code quality checks пройдены

**Postconditions**:
- Verification Agent назначен
- Test Engineer назначен
- Начало верификации
- Release candidate подготовлен

**Invalid If**:
- Компоненты не реализованы полностью
- Unit tests не пройдены
- Code review не пройден
- API документация отсутствует

**State Change Notifications**:
- Build Orchestrator → Verification Agent
- Build Orchestrator → Test Engineer
- Update task status
- Notify development team
- Trigger verification pipeline

---

### Verification → Release

**Valid Transition**: ✅ Yes

**Preconditions**:
- Integration tests пройдены
- Security tests пройдены
- Performance tests пройдены
- Все артефакты верифицированы
- Quality gates пройдены
- Documentation complete
- Release candidate готов

**Postconditions**:
- Release candidate утвержден
- Build Orchestrator одобрил релиз
- Release notes подготовлены
- Подготовка к выпуску

**Invalid If**:
- Integration tests не пройдены
- Security tests не пройдены
- Performance tests не пройдены
- Quality gates не пройдены
- Критические баги обнаружены

**State Change Notifications**:
- Build Orchestrator → Development Team
- Build Orchestrator → Stakeholders
- Update release status
- Prepare deployment

---

### Release → [*]

**Valid Transition**: ✅ Yes

**Preconditions**:
- Релиз выпущен в production
- Release notes опубликованы
- Мониторинг настроен
- Post-release review проведен
- All stakeholders notified

**Postconditions**:
- Цикл разработки завершен
- Архитектура заморожена
- Подготовка к следующему циклу

**Invalid If**:
- Релиз не выпущен в production
- Release notes не опубликованы
- Мониторинг не настроен
- Критические проблемы после релиза

**State Change Notifications**:
- Build Orchestrator → All Agents
- Notify stakeholders
- Archive release artifacts
- Update version history

---

## Build Process State Machine Transitions

### RequestReceived → Classifying

**Valid Transition**: ✅ Yes

**Preconditions**:
- Запрос зарегистрирован в системе
- Первичная информация собрана
- Приоритет назначен
- Build Orchestrator активен

**Postconditions**:
- Запрос классифицирован
- Тип запроса определен
- Необходимые агенты идентифицированы

**Invalid If**:
- Запрос не зарегистрирован
- Информация неполная
- Приоритет не назначен

**State Change Notifications**:
- Build Orchestrator → Internal
- Update request status
- Notify requester

---

### Classifying → Assigning

**Valid Transition**: ✅ Yes

**Preconditions**:
- Тип задачи определен
- Необходимые агенты идентифицированы
- Оценка сложности завершена
- Контекст собран

**Postconditions**:
- Агент выбран для назначения
- Контекст подготовлен
- Временные рамки установлены

**Invalid If**:
- Тип задачи не определен
- Агенты не идентифицированы
- Сложность не оценена

**State Change Notifications**:
- Build Orchestrator → Target Agent
- Update task status
- Prepare handoff

---

### Assigning → InProgress

**Valid Transition**: ✅ Yes

**Preconditions**:
- Агент назначен
- Контекст передан
- Временные рамки установлены
- Агент принял задачу

**Postconditions**:
- Агент начал работу
- Статус обновлен
- Таймер запущен

**Invalid If**:
- Агент не назначен
- Контекст не передан
- Агент отклонил задачу
- Нет доступных ресурсов

**State Change Notifications**:
- Build Orchestrator → Assigned Agent
- Start task timer
- Update task status

---

### InProgress → Verification

**Valid Transition**: ✅ Yes

**Preconditions**:
- Работа над задачей завершена
- Результаты подготовлены
- Требуется проверка
- Статус обновлен
- All deliverables ready

**Postconditions**:
- Проверка инициирована
- Результаты переданы Verification Agent
- Test Engineer notified

**Invalid If**:
- Работа не завершена
- Результаты не подготовлены
- Deliverables incomplete

**State Change Notifications**:
- Implementation Agent → Verification Agent
- Build Orchestrator → Test Engineer
- Update task status
- Trigger verification

---

### Verification → Complete

**Valid Transition**: ✅ Yes

**Preconditions**:
- Все проверки пройдены
- Результаты одобрены
- Feedback предоставлен
- No critical issues found
- Documentation updated

**Postconditions**:
- Задача закрыта
- Документация обновлена
- Заинтересованные стороны уведомлены

**Invalid If**:
- Проверки не пройдены
- Результаты не одобрены
- Критические проблемы обнаружены
- Documentation incomplete

**State Change Notifications**:
- Build Orchestrator → Requester
- Build Orchestrator → Stakeholders
- Close task
- Archive results

---

### Blocked → InProgress

**Valid Transition**: ✅ Yes

**Preconditions**:
- Причина блокировки решена
- Ресурсы доступны
- Дополнительная информация получена
- Build Orchestrator одобрил разблокировку

**Postconditions**:
- Работа возобновлена
- Статус обновлен
- Таймер перезапущен

**Invalid If**:
- Блокировка не решена
- Ресурсы недоступны
- Build Orchestrator не одобрил

**State Change Notifications**:
- Build Orchestrator → Assigned Agent
- Update task status
- Resume task timer

---

### Escalated → InProgress

**Valid Transition**: ✅ Yes

**Preconditions**:
- Эскалация завершена
- Решение реализовано
- Контекст обновлен
- Проблема решена

**Postconditions**:
- Работа возобновлена
- Статус обновлен
- Таймер перезапущен

**Invalid If**:
- Эскалация не завершена
- Решение не реализовано
- Проблема не решена

**State Change Notifications**:
- Build Orchestrator → Assigned Agent
- Human Expert → Build Orchestrator
- Update task status
- Resume task timer

---

## Invalid Transitions

### Platform State Machine

| From | To | Why Invalid |
|------|----|-------------|
| Bootstrap | Implementation | Architecture not designed |
| ArchitectureDesign | Verification | Components not implemented |
| Implementation | Release | Not verified |
| Verification | Bootstrap | Cannot go back to start |

### Build Process State Machine

| From | To | Why Invalid |
|------|----|-------------|
| RequestReceived | InProgress | Not classified |
| Classifying | Verification | Not assigned |
| Assigning | Complete | Not in progress |
| InProgress | Complete | Not verified |
| Verification | RequestReceived | Cannot skip to start |
| Blocked | Complete | Block must be resolved |

## Transition Triggers

### Automatic Triggers

1. **Timer Expiration**: Автоматический переход при истечении тайм-аута
2. **Dependency Satisfied**: Переход при выполнении зависимостей
3. **Quality Gate Passed**: Переход при прохождении quality gate
4. **All Deliverables Ready**: Переход при готовности всех deliverables

### Manual Triggers

1. **Agent Approval**: Переход при одобрении агента
2. **Build Orchestrator Decision**: Переход при решении Build Orchestrator
3. **Human Approval**: Переход при одобрении человека
4. **Override**: Ручной переход в исключительных случаях

### Event-Driven Triggers

1. **Block Resolved**: Переход при разблокировке
2. **Escalation Complete**: Переход при завершении эскалации
3. **Critical Bug Fixed**: Переход при исправлении критического бага
4. **External Change**: Переход при внешних изменениях

## State Change Notifications

### Notification Types

1. **Internal Notifications**: Внутренние уведомления между агентами
2. **External Notifications**: Уведомления внешним заинтересованным сторонам
3. **System Notifications**: Системные уведомления и логи
4. **Audit Notifications**: Уведомления для аудита и compliance

### Notification Channels

1. **Agent Channel**: Direct channel между агентами
2. **Build Orchestrator Channel**: Channel через Build Orchestrator
3. **Event Bus**: System-wide event bus
4. **External Channel**: Channel для внешних уведомлений

### Notification Format

```json
{
  "notification_id": "unique_id",
  "from_state": "current_state",
  "to_state": "next_state",
  "timestamp": "ISO_8601_timestamp",
  "trigger": "trigger_type",
  "preconditions": [],
  "postconditions": [],
  "metadata": {}
}
```

## Transition Validation

### Validation Rules

1. **State Existence**: Проверка, что состояние существует
2. **Transition Validity**: Проверка, что переход допустим
3. **Precondition Check**: Проверка всех preconditions
4. **Postcondition Guarantee**: Гарантирование всех postconditions
5. **Notification Delivery**: Проверка доставки уведомлений

### Validation Process

1. Check state machine configuration
2. Verify transition exists in valid transitions
3. Validate all preconditions
4. Execute transition
5. Verify all postconditions
6. Send notifications
7. Update state machine status

### Validation Errors

1. **InvalidStateError**: Состояние не существует
2. **InvalidTransitionError**: Переход недопустим
3. **PreconditionError**: Precondition не выполнен
4. **PostconditionError**: Postcondition не гарантируется
5. **NotificationError**: Уведомление не доставлено

## Related Documentation

- [Platform State Machine](./platform-state-machine.md)
- [Build Process State Machine](./build-process-state-machine.md)
- [Escalation Rules](./escalation-rules.md)
- [Approval Gates](./approval-gates.md)
- [State Machines Overview](../state-machines.md)
