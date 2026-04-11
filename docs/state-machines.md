# State Machines

**Версия:** 1.0.0
**Дата:** 2026-04-11
**Статус:** Draft

---

## A. Platform State Machine

### Overview

State Machine для задач orchestration platform обеспечивает управление жизненным циклом задач от приёма до завершения, включая обработку ошибок, повторные попытки и процессы одобрения.

### Состояния

#### 1. Task Intake

- **Meaning**: Начальное состояние приёма новой задачи в систему
- **Owner**: Build Orchestrator
- **Entry conditions**: Новая задача создана через API, вебхук или вручную
- **Exit events**: Задача классифицирована и принята для обработки
- **Allowed transitions**:
  - → Classification (успешная валидация и парсинг)
  - → Failed (критическая ошибка валидации)
- **Forbidden transitions**:
  - → Planning (без предварительной классификации)
  - → Execution (непосредственно из intake)
  - → Waiting for approval (на этом этапе нет артефактов для проверки)
- **Timeout/stall handling**:
  - Тайм-аут: 5 минут для парсинга и валидации
  - При тайм-ауте: переход в Failed с логированием причины
- **Artifacts produced**:
  - Task metadata (ID, тип, приоритет, источник)
  - Initial context (описание задачи, требования)
  - Validation report (результаты валидации)

#### 2. Classification

- **Meaning**: Определение типа задачи и подходящего агента для выполнения
- **Owner**: Build Orchestrator
- **Entry conditions**: Задача успешно прошла валидацию в Task Intake
- **Exit events**: Тип задачи определён, агент назначен
- **Allowed transitions**:
  - → Planning (классификация завершена, агент назначен)
  - → Blocked (недостаточно информации для классификации)
  - → Failed (ошибка классификации)
- **Forbidden transitions**:
  - → Execution (без планирования)
  - → Waiting for approval (ещё нет артефактов)
  - → Completed (слишком рано)
- **Timeout/stall handling**:
  - Тайм-аут: 3 минуты для классификации
  - При тайм-ауте: эскалация к Platform Architect
- **Artifacts produced**:
  - Classification result (тип задачи: архитектура, реализация, интеграция, верификация)
  - Assigned agent (Platform Architect, Workflow Architect, Implementation Engineer, etc.)
  - Task priority score
  - Required skills для агента

#### 3. Planning

- **Meaning**: Подготовка плана выполнения задачи, распределение ресурсов
- **Owner**: Workflow Architect
- **Entry conditions**: Задача классифицирована, агент назначен
- **Exit events**: План утверждён и готов к выполнению
- **Allowed transitions**:
  - → Stage assignment (план готов, стадия определена)
  - → Waiting for approval (требуется утверждение плана)
  - → Blocked (недостаточно ресурсов или зависимостей)
  - → Failed (ошибка планирования)
- **Forbidden transitions**:
  - → Execution (без назначения стадии)
  - → Retrying (не было выполнения)
- **Timeout/stall handling**:
  - Тайм-аут: 10 минут для планирования
  - При тайм-ауте: эскалация к Build Orchestrator
- **Artifacts produced**:
  - Execution plan (последовательность шагов)
  - Stage assignment (определение SDLC стадии: BA, SA, DEV, QA)
  - Resource allocation (агенты, инструменты)
  - Dependencies (зависимости от других задач/артефактов)
  - Risk assessment (оценка рисков)

#### 4. Stage Assignment

- **Meaning**: Назначение задачи на конкретную стадию SDLC и создание соответствующей Jira задачи
- **Owner**: Build Orchestrator
- **Entry conditions**: План выполнен, стадия определена
- **Exit events**: Задача назначена на стадию, Jira задача создана
- **Allowed transitions**:
  - → Execution (назначение завершено, задача готова к выполнению)
  - → Waiting for approval (требуется утверждение назначения)
  - → Blocked (стадия недоступна или заблокирована)
  - → Failed (ошибка назначения)
- **Forbidden transitions**:
  - → Planning (этап уже пройден)
  - → Completed (не было выполнения)
- **Timeout/stall handling**:
  - Тайм-аут: 5 минут для создания Jira задачи
  - При тайм-ауте: повторная попытка или эскалация
- **Artifacts produced**:
  - Stage assignment record (SDLC стадия)
  - Jira task reference (ключ Jira задачи)
  - Agent assignment (конкретный исполнитель)
  - Stage metadata (тайм-аут стадии, approval gate)

#### 5. Execution

- **Meaning**: Активное выполнение задачи назначенным агентом
- **Owner**: Assigned Agent (Platform Architect, Implementation Engineer, Test Engineer, etc.)
- **Entry conditions**: Задача назначена на стадию, агент готов
- **Exit events**: Задача выполнена или возникла ошибка
- **Allowed transitions**:
  - → Waiting for approval (задача выполнена, требуется review)
  - → Failed (ошибка выполнения)
  - → Blocked (задача заблокирована внешними факторами)
  - → Completed (задача выполнена и не требует approval)
- **Forbidden transitions**:
  - → Classification (возврат к началу не разрешён)
  - → Planning (возврат назад только через rework)
- **Timeout/stall handling**:
  - Тайм-аут: определяется на основе сложности задачи (30 мин - 24 часа)
  - При тайм-ауте: переход в Retrying с backoff
  - Максимальное время выполнения: 24 часа (конфигурируемо)
- **Artifacts produced**:
  - Implementation artifacts (код, документы, спецификации)
  - Execution log (лог выполнения)
  - Output artifacts (продукты выполнения)
  - Test results (результаты тестирования, если применимо)

#### 6. Waiting for Approval

- **Meaning**: Задача выполнена и ожидает проверки/утверждения
- **Owner**: Verification Agent / Build Orchestrator
- **Entry conditions**: Задача выполнена, артефакты готовы
- **Exit events**: Approval получен или отклонён
- **Allowed transitions**:
  - → Completed (одобрено)
  - → Rework (требуется доработка)
  - → Failed (критическая ошибка в артефактах)
  - → Cancelled (задача отменена)
- **Forbidden transitions**:
  - → Execution (возврат к выполнению без изменений)
  - → Classification (полный возврат)
- **Timeout/stall handling**:
  - Тайм-аут: 24 часа для approval
  - При тайм-ауте: эскалация к Build Orchestrator или автоматическое отклонение
  - Напоминания: через 12 часов, 18 часов
- **Artifacts produced**:
  - Approval request (запрос на review)
  - Review report (отчёт верификатора)
  - Approval decision (approve/reject с комментариями)
  - Feedback for rework (комментарии для доработки)

#### 7. Blocked

- **Meaning**: Задача заблокирована и не может продолжаться
- **Owner**: Build Orchestrator
- **Entry conditions**:
  - Недостаток информации
  - Зависимость от другой задачи
  - Недоступность ресурсов
  - Внешняя блокировка
- **Exit events**: Блокировка устранена
- **Allowed transitions**:
  - → Previous state (зависит от состояния до блокировки)
  - → Failed (блокировка не может быть устранена)
  - → Cancelled (задача отменена)
- **Forbidden transitions**:
  - → Completed (нельзя завершить заблокированную задачу)
  - → Execution (пока заблокирована)
- **Timeout/stall handling**:
  - Тайм-аут: 48 часов для устранения блокировки
  - При тайм-ауте: эскалация или автоматическая отмена
  - Мониторинг: проверка статуса каждые 6 часов
- **Artifacts produced**:
  - Blockage record (причина блокировки)
  - Blocking dependencies (зависимые задачи)
  - Unblocking plan (план разблокировки)
  - Escalation history (история эскалаций)

#### 8. Failed

- **Meaning**: Задача завершилась с ошибкой
- **Owner**: Build Orchestrator
- **Entry conditions**:
  - Критическая ошибка на любом этапе
  - Превышение максимального количества retries
  - Блокировка не может быть устранена
- **Exit events**: Анализ причины, решение о повторной попытке или отмене
- **Allowed transitions**:
  - → Retrying (ошибка исправима, есть retry logic)
  - → Cancelled (задача отменена)
- **Forbidden transitions**:
  - → Execution (без повторного планирования)
  - → Waiting for approval (нельзя одобрить неудачную задачу)
- **Timeout/stall handling**:
  - Тайм-аут: 1 час для анализа и принятия решения
  - При тайм-ауте: автоматическая отмена задачи
- **Artifacts produced**:
  - Error report (детальный отчёт об ошибке)
  - Failure analysis (анализ причины)
  - Retry recommendation (рекомендация по retry)
  - Impact assessment (оценка воздействия)

#### 9. Retrying

- **Meaning**: Повторная попытка выполнения задачи после ошибки
- **Owner**: Build Orchestrator
- **Entry conditions**: Задача перешла в Failed, ошибка исправима
- **Exit events**: Retry выполнен (успешно или нет)
- **Allowed transitions**:
  - → Previous state (успешный retry, возврат в состояние до ошибки)
  - → Failed (retry не удался, превышен лимит)
- **Forbidden transitions**:
  - → Completed (нельзя завершить после failed без повторения выполнения)
  - → Waiting for approval (нет артефактов)
- **Timeout/stall handling**:
  - Тайм-аут: зависит от retry policy
  - Backoff strategy: exponential backoff (1s, 2s, 4s, 8s, 16s, 32s, 64s)
  - Jitter: ±20% для предотвращения thundering herd
  - Максимальное количество retries: 5 (конфигурируемо)
- **Artifacts produced**:
  - Retry attempt record (номер попытки, время)
  - Retry context (контекст retry)
  - Backoff application (применённый backoff)
  - Retry result (результат попытки)

#### 10. Completed

- **Meaning**: Задача успешно завершена
- **Owner**: Build Orchestrator
- **Entry conditions**: Задача выполнена, все approval gates пройдены
- **Exit events**: Архивирование задачи
- **Allowed transitions**:
  - → None (терминальное состояние)
- **Forbidden transitions**:
  - Любые переходы из Completed запрещены
- **Timeout/stall handling**:
  - Нет тайм-аута (терминальное состояние)
  - Архивирование через 30 дней
- **Artifacts produced**:
  - Completion report (отчёт о завершении)
  - Final artifacts (финальные артефакты)
  - Metrics (метрики выполнения: время, ресурсы)
  - Lessons learned (уроки и выводы)

#### 11. Cancelled

- **Meaning**: Задача отменена
- **Owner**: Build Orchestrator
- **Entry conditions**:
  - Пользователь отменил задачу
  - Блокировка не может быть устранена
  - Превышены все лимиты retries
  - Изменение требований
- **Exit events**: Архивирование задачи
- **Allowed transitions**:
  - → None (терминальное состояние)
- **Forbidden transitions**:
  - Любые переходы из Cancelled запрещены
- **Timeout/stall handling**:
  - Нет тайм-аута (терминальное состояние)
  - Архивирование через 30 дней
- **Artifacts produced**:
  - Cancellation record (запись об отмене)
  - Reason for cancellation (причина отмены)
  - Cleanup record (запись о очистке ресурсов)
  - Impact analysis (анализ воздействия отмены)

### Переходы

| From | To | Event | Guard |
|------|-----|-------|-------|
| Task Intake | Classification | Валидация успешна | Task metadata корректен |
| Task Intake | Failed | Ошибка валидации | Критическая ошибка |
| Classification | Planning | Классификация завершена | Тип задачи определён |
| Classification | Blocked | Недостаточно информации | Требуется дополнительный контекст |
| Classification | Failed | Ошибка классификации | Не удалось определить тип |
| Planning | Stage Assignment | План готов | Стадия определена |
| Planning | Waiting for Approval | Требуется review | Plan complexity > medium |
| Planning | Blocked | Недостаток ресурсов | Недоступны агенты |
| Planning | Failed | Ошибка планирования | Не удалось создать план |
| Stage Assignment | Execution | Назначение завершено | Jira задача создана |
| Stage Assignment | Waiting for Approval | Требуется review | Критическая задача |
| Stage Assignment | Blocked | Стадия недоступна | Стадия заблокирована |
| Stage Assignment | Failed | Ошибка назначения | Не удалось создать Jira |
| Execution | Waiting for Approval | Выполнение завершено | Артефакты готовы |
| Execution | Failed | Ошибка выполнения | Критическая ошибка |
| Execution | Blocked | Внешняя блокировка | Зависимость заблокирована |
| Execution | Completed | Выполнение завершено | Не требуется approval |
| Waiting for Approval | Completed | Одобрено | Review passed |
| Waiting for Approval | Rework | Требуется доработка | Review failed with issues |
| Waiting for Approval | Failed | Критическая ошибка | Review failed critical |
| Waiting for Approval | Cancelled | Отменено | Пользователь отменил |
| Blocked | Execution | Блокировка устранена | Из состояния Execution |
| Blocked | Planning | Блокировка устранена | Из состояния Planning |
| Blocked | Failed | Блокировка не устранима | Превышен тайм-аут |
| Blocked | Cancelled | Отменено | Пользователь отменил |
| Failed | Retrying | Ошибка исправима | Retry count < max |
| Failed | Cancelled | Ошибка не исправима | Retry count >= max |
| Retrying | Execution | Retry успешен | Было в Execution |
| Retrying | Planning | Retry успешен | Было в Planning |
| Retrying | Failed | Retry не удался | Превышен лимит retries |

### Диаграмма

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PLATFORM STATE MACHINE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────┐                                                                 │
│   │  START  │                                                                 │
│   └────┬────┘                                                                 │
│        │                                                                       │
│        ▼                                                                       │
│   ┌─────────────┐                                                             │
│   │ Task Intake │────────────────────┐                                        │
│   └──────┬──────┘                    │                                        │
│          │                           │                                        │
│          │ [validation success]      │ [validation failed]                    │
│          ▼                           ▼                                        │
│   ┌─────────────┐               ┌─────────┐                                   │
│   │Classification│───────────────▶│ Failed  │◀───────────────┐                │
│   └──────┬──────┘               └────┬────┘               │                │
│          │                            │                   │                │
│          │ [classified]                │                   │                │
│          ▼                            │                   │                │
│   ┌─────────────┐                     │                   │                │
│   │  Planning   │───────────┐         │                   │                │
│   └──────┬──────┘           │         │                   │                │
│          │                  │         │                   │                │
│          │ [plan ready]     │ [requires review]         │                │
│          ▼                  ▼         │                   │                │
│   ┌─────────────┐   ┌───────────────────┐                │                │
│   │Stage Assign.│   │ Waiting for       │                │                │
│   └──────┬──────┘   │ Approval          │                │                │
│          │          └───────┬───────────┘                │                │
│          │                  │                           │                │
│          │ [assigned]       │ [approved] [rejected]     │                │
│          ▼                  ▼                ▼            │                │
│   ┌─────────────┐   ┌─────────┐    ┌─────────────┐      │                │
│   │  Execution  │───▶│Completed│    │   Rework    │──────┘                │
│   └──────┬──────┘   └────┬────┘    └──────┬──────┘                       │
│          │               │                │                              │
│          │ [blocked]      │                │                              │
│          │                │                │                              │
│          ▼                │                │                              │
│   ┌─────────────┐         │                │                              │
│   │  Blocked    │─────────┴────────────────┘                              │
│   └──────┬──────┘                                                          │
│          │                                                                   │
│          │ [failed]                                                          │
│          ▼                                                                   │
│   ┌─────────┐                                                                │
│   │ Failed  │◀───┐                                                          │
│   └────┬────┘    │                                                          │
│        │         │                                                          │
│        │ [retry]  │ [timeout]                                                │
│        ▼         │                                                          │
│   ┌─────────┐    │                                                          │
│   │Retrying │────┘                                                          │
│   └─────────┘                                                               │
│            │                                                                 │
│            │ [cancelled]                                                       │
│            ▼                                                                 │
│      ┌───────────┐                                                          │
│      │ Cancelled │                                                          │
│      └───────────┘                                                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Retry Logic

**Exponential Backoff Strategy:**
```
Attempt 1: immediate (no backoff)
Attempt 2: 1s ±20%
Attempt 3: 2s ±20%
Attempt 4: 4s ±20%
Attempt 5: 8s ±20%
Attempt 6: 16s ±20%
Attempt 7: 32s ±20%
Attempt 8: 64s ±20%
Max retries: 5 (configurable)
```

**Retry Conditions:**
- Transient failures (network timeouts, temporary unavailability)
- Recoverable errors (missing dependencies that can be resolved)
- Agent restart required
- Partial completion (can resume)

**No Retry Conditions:**
- Permanent failures (invalid input, logical errors)
- Validation failures (cannot be resolved by retry)
- User cancellation
- Security violations

### Approval Gates

**Stage-Based Approval:**
- **BA Stage**: Manual approval by Business Analyst
- **SA Stage**: Manual approval by System Architect
- **DEV Stage**: Automated (CI/CD) + Manual code review
- **QA Stage**: Manual approval by QA Lead
- **DONE Stage**: Manual approval by Product Owner

**Approval Timeout:**
- Default: 24 hours
- Critical tasks: 8 hours
- Urgent tasks: 4 hours
- Escalation after timeout

---

## B. Build-Process State Machine

### Overview

State Machine для процесса разработки самой orchestration platform. Отражает цикл разработки от исследования до принятия, с чётким порядком прохождения через 8 build-агентов.

### Состояния

#### 1. Discovery

- **Owner build-agent**: Build Orchestrator
- **Input artifacts**:
  - Business requirements
  - User stories / Use cases
  - Problem statement
  - Constraints and assumptions
- **Exit criteria**:
  - Требования полностью собраны и документированы
  - Scope чётко определён
  - Non-goles идентифицированы
  - Stakeholders идентифицированы
- **Review gate**:
  - Review with Product Owner
  - Validation of requirements completeness
- **Escalation path**:
  - Build Orchestrator → Product Owner (за 4 часа)
  - Product Owner → Technical Lead (за 8 часов)

**Description**: Исследование бизнес-требований, сбор информации, определение scope и non-goals для разработки платформы.

#### 2. Design in Progress

- **Owner build-agent**: Platform Architect
- **Input artifacts**:
  - Documented requirements (из Discovery)
  - Technical constraints
  - Architecture guidelines
  - Technology stack preferences
- **Exit criteria**:
  - High-level architecture определена
  - Component boundaries установлены
  - Основные технологии выбраны
  - Interface contracts определены
- **Review gate**:
  - Architecture review with Workflow Architect
  - Technology stack validation
  - Security model review
- **Escalation path**:
  - Platform Architect → Build Orchestrator (за 2 часа)
  - Build Orchestrator → Technical Lead (за 4 часа)

**Description**: Разработка архитектуры платформы, определение компонентов, границ, технологий и интерфейсов.

#### 3. Architecture Review

- **Owner build-agent**: Workflow Architect
- **Input artifacts**:
  - Architecture design (из Design in Progress)
  - ADR документы (Architecture Decision Records)
  - Component specifications
  - Security model
- **Exit criteria**:
  - Architecture утверждена
  - Все ADR созданы и утверждены
  - State machine определён
  - Workflow спецификации готовы
- **Review gate**:
  - Review with Agent Runtime Architect
  - Integration boundary validation
  - Workflow logic verification
- **Escalation path**:
  - Workflow Architect → Platform Architect (за 2 часа)
  - Platform Architect → Build Orchestrator (за 4 часа)
  - Build Orchestrator → Technical Lead (за 8 часов)

**Description**: Review архитектуры, определение state machine, validation workflow спецификаций.

#### 4. Implementation Ready

- **Owner build-agent**: Integration Architect
- **Input artifacts**:
  - Approved architecture
  - State machine specification
  - Workflow definitions
  - Integration requirements
- **Exit criteria**:
  - All integrations defined
  - Integration contracts documented
  - Data synchronization model ready
  - Error handling for integrations specified
- **Review gate**:
  - Review with Agent Runtime Architect
  - Integration contract validation
  - MCP integration review
- **Escalation path**:
  - Integration Architect → Workflow Architect (за 2 часа)
  - Workflow Architect → Build Orchestrator (за 4 часа)
  - Build Orchestrator → Technical Lead (за 8 часов)

**Description**: Определение интеграций с внешними системами (Jira, Git, CI/CD, MCP), подготовка контрактов и моделей синхронизации.

#### 5. Implementation in Progress

- **Owner build-agent**: Implementation Engineer
- **Input artifacts**:
  - Complete architecture
  - Integration contracts
  - Workflow specifications
  - Test requirements
- **Exit criteria**:
  - All components implemented
  - Unit tests written
  - Code follows standards
  - Integration points ready
- **Review gate**:
  - Code review with Test Engineer
  - Implementation validation
  - Standards compliance check
- **Escalation path**:
  - Implementation Engineer → Integration Architect (за 1 час)
  - Integration Architect → Build Orchestrator (за 2 часа)
  - Build Orchestrator → Technical Lead (за 4 часа)

**Description**: Реализация компонентов платформы, написание кода, unit тестов, интеграция компонентов.

#### 6. Verification

- **Owner build-agent**: Verification Agent
- **Input artifacts**:
  - Implemented components
  - Unit tests
  - Integration code
  - Documentation
- **Exit criteria**:
  - All components verified
  - Architecture compliance confirmed
  - Standards compliance validated
  - No critical issues
- **Review gate**:
  - Review with Implementation Engineer
  - Test Engineer review
  - Build Orchestrator final validation
- **Escalation path**:
  - Verification Agent → Build Orchestrator (за 1 час)
  - Build Orchestrator → Technical Lead (за 2 часа)
  - Technical Lead → Product Owner (за 4 часа)

**Description**: Верификация артефактов, проверка архитектуры, кода, соответствия стандартам, выявление проблем.

#### 7. Rework

- **Owner build-agent**: Implementation Engineer
- **Input artifacts**:
  - Verification report
  - Issues list
  - Feedback from Verification Agent
  - Recommendations for fixes
- **Exit criteria**:
  - All critical issues resolved
  - All major issues resolved
  - Minor issues documented
  - Changes verified
- **Review gate**:
  - Re-verification with Verification Agent
  - Test Engineer re-validation
- **Escalation path**:
  - Implementation Engineer → Build Orchestrator (за 1 час)
  - Build Orchestrator → Technical Lead (за 2 часа)
  - Technical Lead → Product Owner (за 4 часа)

**Description**: Исправление проблем, выявленных при верификации. Состояние может циклически возвращаться к Verification после каждого rework цикла.

#### 8. Accepted

- **Owner build-agent**: Test Engineer
- **Input artifacts**:
  - Verified components
  - Verification report (PASS)
  - Test results
  - Final documentation
- **Exit criteria**:
  - All tests pass
  - Coverage > 80%
  - No flaky tests
  - Documentation complete
- **Review gate**:
  - Final review with Build Orchestrator
  - Product Owner acceptance
  - Stakeholder sign-off
- **Escalation path**:
  - Test Engineer → Build Orchestrator (за 1 час)
  - Build Orchestrator → Product Owner (за 2 часа)
  - Product Owner → Technical Lead (за 4 часа)

**Description**: Финальное тестирование, принятие компонентов, подготовка к deployment, sign-off от всех stakeholders.

### Переходы

| From | To | Event | Guard |
|------|-----|-------|-------|
| Discovery | Design in Progress | Requirements documented | Scope clear, non-goles defined |
| Discovery | Discovery | Requirements incomplete | More information needed |
| Design in Progress | Architecture Review | Architecture ready | High-level design complete |
| Design in Progress | Design in Progress | Design issues found | Rerquire clarifications |
| Architecture Review | Implementation Ready | Architecture approved | All ADR approved |
| Architecture Review | Design in Progress | Architecture rejected | Major issues found |
| Architecture Review | Architecture Review | Review in progress | Waiting for feedback |
| Implementation Ready | Implementation in Progress | Integrations defined | All contracts ready |
| Implementation Ready | Architecture Review | Integration issues | Need architecture changes |
| Implementation in Progress | Verification | Implementation complete | All code written, unit tests done |
| Implementation in Progress | Implementation in Progress | Implementation issues | Need more time/resources |
| Verification | Accepted | Verification passed | No critical issues |
| Verification | Rework | Issues found | Critical/major issues detected |
| Verification | Implementation in Progress | Implementation issues | Need code changes |
| Rework | Verification | Rework complete | Issues resolved |
| Rework | Rework | More issues found | Additional rework needed |
| Rework | Implementation in Progress | Major rework needed | Back to implementation |
| Accepted | Discovery | New iteration | Next development cycle |

### Диаграмма

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   BUILD-PROCESS STATE MACHINE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────┐                                                                 │
│   │  START  │                                                                 │
│   └────┬────┘                                                                 │
│        │                                                                       │
│        ▼                                                                       │
│   ┌───────────────────┐                                                        │
│   │    Discovery      │                                                        │
│   │   (Build Orchest.)│                                                        │
│   └─────────┬─────────┘                                                        │
│             │                                                                  │
│             │ [requirements documented]                                       │
│             ▼                                                                  │
│   ┌───────────────────┐                                                        │
│   │  Design in Prog.  │                                                        │
│   │  (Platform Arch.) │                                                        │
│   └─────────┬─────────┘                                                        │
│             │                                                                  │
│             │ [architecture ready]                                             │
│             ▼                                                                  │
│   ┌───────────────────┐                                                        │
│   │ Architecture Rev. │                                                        │
│   │ (Workflow Arch.)  │                                                        │
│   └─────────┬─────────┘                                                        │
│             │                                                                  │
│             │ [approved]                     [rejected]                        │
│             │                                 ▼                                │
│             │                      ┌───────────────────┐                       │
│             │                      │  Design in Prog.  │────────────────┐      │
│             │                      └───────────────────┘                │      │
│             ▼                                                            │      │
│   ┌───────────────────┐                                            ▼      │
│   │Implementation Ready│────────────────────────────────────────┐   Design │
│   │  (Integ. Architect)│                                        │ in Prog.│
│   └─────────┬─────────┘                                        └─────────┘
│             │                                                              │
│             │ [integrations defined]                                       │
│             ▼                                                              │
│   ┌───────────────────┐                                                    │
│   │Implementation in   │                                                    │
│   │     Progress       │                                                    │
│   │ (Impl. Engineer)  │                                                    │
│   └─────────┬─────────┘                                                    │
│             │                                                              │
│             │ [implementation complete]                                     │
│             ▼                                                              │
│   ┌───────────────────┐                                                    │
│   │   Verification     │◀─────────────────────────────────────────────────┤
│   │   (Verif. Agent)   │                                            [need  │
│   └─────────┬─────────┘                                            changes]│
│             │                                                              │
│             │                    ┌───────────────┐                         │
│             │ [passed]           │    Rework     │                         │
│             ▼                    │               │                         │
│   ┌───────────────────┐         └───────┬───────┘                         │
│   │     Accepted      │◀────────────────│                                 │
│   │   (Test Engineer) │                 │                                 │
│   └─────────┬─────────┘                 │                                 │
│             │                           │                                 │
│             │                           ▼                                 │
│             │                    ┌───────────────────┐                     │
│             │                    │   Verification     │────────────────────┘
│             │                    │   (Verif. Agent)   │    [rework complete]
│             │                    └───────────────────┘
│             │                                 │
│             │                                 │ [more issues]
│             │                                 ▼
│             │                          ┌───────────────┐
│             └──────────────────────────│    Rework     │
│                                        └───────────────┘
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Build Agent Mapping

| Состояние | Build Agent | Primary Responsibility |
|-----------|-------------|------------------------|
| Discovery | Build Orchestrator | Сбор требований, определение scope |
| Design in Progress | Platform Architect | Архитектура платформы, компоненты |
| Architecture Review | Workflow Architect | Review, state machine, workflows |
| Implementation Ready | Integration Architect | Интеграции, контракты |
| Implementation in Progress | Implementation Engineer | Реализация кода, unit тесты |
| Verification | Verification Agent | Верификация артефактов, review |
| Rework | Implementation Engineer | Исправление проблем |
| Accepted | Test Engineer | Финальное тестирование, acceptance |

### Escalation Matrix

| Состояние | Level 1 (1-2h) | Level 2 (4h) | Level 3 (8h+) |
|-----------|----------------|--------------|---------------|
| Discovery | Build Orchestrator → Product Owner | Product Owner → Technical Lead | Technical Lead → Management |
| Design in Progress | Platform Architect → Build Orchestrator | Build Orchestrator → Technical Lead | Technical Lead → Architecture Review Board |
| Architecture Review | Workflow Architect → Platform Architect | Platform Architect → Build Orchestrator | Build Orchestrator → Architecture Review Board |
| Implementation Ready | Integration Architect → Workflow Architect | Workflow Architect → Build Orchestrator | Build Orchestrator → Technical Lead |
| Implementation in Progress | Implementation Engineer → Integration Architect | Integration Architect → Build Orchestrator | Build Orchestrator → Technical Lead |
| Verification | Verification Agent → Build Orchestrator | Build Orchestrator → Technical Lead | Technical Lead → Product Owner |
| Rework | Implementation Engineer → Build Orchestrator | Build Orchestrator → Technical Lead | Technical Lead → Product Owner |
| Accepted | Test Engineer → Build Orchestrator | Build Orchestrator → Product Owner | Product Owner → Stakeholders |

### Cycle Logic

**Verification → Rework → Verification Loop:**
```
Максимальное количество итераций: 3
Критические issues: должны быть исправлены (блокируют переход)
Major issues: должны быть исправлены (блокируют переход)
Minor issues: могут быть задокументированы и отложены

После 3-х неудачных попыток:
- Эскалация на Level 2
- Пересмотр требований
- Возможный return в Design in Progress
```

**Quality Gates:**
- Design in Progress → Architecture Review: ADR creation mandatory
- Architecture Review → Implementation Ready: All workflows defined
- Implementation in Progress → Verification: Code review passed
- Verification → Accepted: No critical issues, <5 major issues

---

## Приложение: State Machine Interactions

### Handoff Between State Machines

**Build-Process → Platform State Machine:**
```
Когда Build-Process State Machine достигает "Accepted":
1. Создаётся новый task в Platform State Machine
2. Начальное состояние: Task Intake
3. Классификация: task type = "deployment"
4. Planning: deployment plan на основе Accepted artifacts
5. Execution: deployment агента
6. Waiting for Approval: acceptance testing
7. Completed: production deployment
```

### Monitoring and Observability

**Metrics для Platform State Machine:**
- Task completion rate (by type, stage)
- Average time in each state
- Retry success rate
- Approval gate success rate
- Blocked task rate
- MTTR (Mean Time To Recovery)

**Metrics для Build-Process State Machine:**
- Development cycle time
- Verification pass rate
- Rework iterations (avg, max)
- Escalation rate
- Quality gate pass rate
- Stakeholder satisfaction

---

**Версия документа:** 1.0.0
**Последнее обновление:** 2026-04-11
**Ответственные:** Build Orchestrator, Workflow Architect
