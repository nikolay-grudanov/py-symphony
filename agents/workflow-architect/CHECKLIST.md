# Workflow Architect - Чеклист завершения

## Обзор

Чеклист определяет критерии завершения проектирования workflows. Workflow Architect не может считать workflow завершенным, пока все пункты чеклиста не выполнены.

## Чеклист для State Machine Design

### Для State Machine Diagrams

- [ ] **State machine diagram создан**
  - [ ] Mermaid diagram создана
  - [ ] Все состояния включены в diagram
  - [ ] Все переходы включены в diagram
  - [ ] Labels для переходов добавлены
  - [ ] Notes для сложных ситуаций добавлены
  - [ ] Diagram читабельна и понятна

- [ ] **Состояния определены**
  - [ ] Начальное состояние (initial state) определено
  - [ ] Конечные состояния (terminal states) определены
  - [ ] Все промежуточные состояния определены
  - [ ] Error states определены (если применимо)
  - [ ] Для каждого состояния есть описание
  - [ ] Для каждого состояния определен ответственный

- [ ] **Переходы определены**
  - [ ] Все переходы между состояниями определены
  - [ ] Триггеры переходов определены (events, timers, conditions)
  - [ ] Guard conditions для переходов определены
  - [ ] Entry/exit actions для переходов определены (если применимо)
  - [ ] Для каждого перехода есть описание

- [ ] **State machine валидирован**
  - [ ] Completeness: Все необходимые переходы определены
  - [ ] Consistency: Нет противоречий
  - [ ] Deadlock: Нет тупиковых ситуаций
  - [ ] Reachability: Из каждого состояния достижимо terminal state

## Чеклист для Workflow Design

### Для Workflow Specifications

- [ ] **Этапы workflow определены**
  - [ ] Все этапы workflow определены
  - [ ] Dependencies между этапами определены
  - [ ] Параллельные пути определены (если есть)
  - [ ] Decision points определены (если есть)

- [ ] **Handoff contracts созданы**
  - [ ] Точки передачи между участниками определены
  - [ ] Входные данные для каждого handoff определены
  - [ ] Выходные данные для каждого handoff определены
  - [ ] Триггеры передачи определены
  - [ ] Acceptance criteria определены
  - [ ] Rejection criteria определены

- [ ] **Approval gates спроектированы**
  - [ ] Точки approval определены
  - [ ] Approvers для каждого gate определены
  - [ ] Критерии approval определены
  - [ ] Критерии отклонения определены
  - [ ] Действия при отклонении определены

- [ ] **Escalation paths спроектированы**
  - [ ] Проблемные ситуации идентифицированы
  - [ ] Уровни эскалации определены
  - [ ] Триггеры эскалации определены
  - [ ] Маршруты эскалации определены
  - [ ] Fallback пути определены

## Чеклист для Process Modeling

### Для Process Models

- [ ] **Нотация выбрана**
  - [ ] State diagrams для state machines созданы
  - [ ] Sequence diagrams для handoffs созданы (если применимо)
  - [ ] Activity diagrams для сложных workflows созданы (если применимо)
  - [ ] Flowcharts для decision points созданы (если применимо)

- [ ] **Participants определены**
  - [ ] Все участники процесса определены
  - [ ] Роли участников определены
  - [ ] Ответственность участников определена

- [ ] **Процесс смоделирован**
  - [ ] Все messages между participants определены
  - [ ] Sequence действий определена
  - [ ] Conditions и loops определены (если применимо)
  - [ ] Process оптимизирован (если применимо)

- [ ] **Процесс документирован**
  - [ ] Clear и explicit описание создано
  - [ ] Примеры использования предоставлены
  - [ ] FAQ создано (если применимо)
  - [ ] Diagrams соответствуют описанию

## Чеклист для Handoff Packaging

### Для Handoff Packages

- [ ] **Информация собрана**
  - [ ] Все артефакты собраны
  - [ ] Критически важная информация определена
  - [ ] Опциональная информация определена
  - [ ] Информация структурирована

- [ ] **Контекст упакован**
  - [ ] Clear описание того, что было сделано
  - [ ] Ссылки на все артефакты предоставлены
  - [ ] Dependencies описаны
  - [ ] Важные решения описаны

- [ ] **Сообщение сформировано**
  - [ ] Стандартный шаблон использован
  - [ ] Информация структурирована
  - [ ] Ожидания указаны
  - [ ] QA Gate criteria предоставлены

## Чеклист для конкретных workflows

### Для ADR Process

- [ ] **State Machine для ADR**
  - [ ] Состояния: Proposal, Review, Approved, Rejected, ChangesRequested, Implementation, Recorded
  - [ ] Переходы: Proposal → Review → Approved/Rejected/ChangesRequested → Implementation → Recorded
  - [ ] Guard conditions: Minimum 2 reviewers, architect approval
  - [ ] Entry/exit actions: Notify reviewers, log review duration

- [ ] **Handoff Contracts для ADR**
  - [ ] Proposal → Review: ADR document, reviewers assigned
  - [ ] Review → Approved: Review summary, approval decision
  - [ ] Approved → Implementation: Approval notification, implementation requirements

- [ ] **Escalation Paths для ADR**
  - [ ] No reviews > 48h: Escalate to lead architect
  - [ ] Conflict between reviewers: Escalate to architect council
  - [ ] Implementation blocked > 72h: Escalate to architect

- [ ] **Approval Gates для ADR**
  - [ ] Gate 1 (Review): Minimum 2 reviewers assigned
  - [ ] Gate 2 (Approved): Architect approval required

### Для Integration Contract Process

- [ ] **State Machine для Integration**
  - [ ] Состояния: Proposal, ExternalReview, InternalReview, Approved, ChangesRequested, Implementation, Testing, Validated, NeedsFixes
  - [ ] Переходы: Proposal → ExternalReview → InternalReview → Approved/ChangesRequested → Implementation → Testing → Validated/NeedsFixes
  - [ ] Guard conditions: External API validation, minimum 2 reviews
  - [ ] Entry/exit actions: Validate against external API, notify reviewers

- [ ] **Handoff Contracts для Integration**
  - [ ] Proposal → ExternalReview: Contract proposal, external API docs
  - [ ] ExternalReview → InternalReview: External API validation result
  - [ ] InternalReview → Approved: Review summary, approval decision

- [ ] **Escalation Paths для Integration**
  - [ ] External API changes unexpectedly: Escalate to product manager
  - [ ] External API docs unclear: Escalate to integration architect
  - [ ] Integration tests failing > 48h: Escalate to QA lead

- [ ] **Approval Gates для Integration**
  - [ ] Gate 1 (ExternalReview): External API validation passed
  - [ ] Gate 2 (InternalReview): Minimum 2 reviews
  - [ ] Gate 3 (Approved): Integration architect approval
  - [ ] Gate 4 (Validated): Integration tests passed

### Для Build Team Workflow

- [ ] **Master State Machine для Build Process**
  - [ ] Состояния: TaskCreated, Assigned, InProgress, Blocked, Completed, QAReview, QAPassed, QAFailed, Handoff
  - [ ] Переходы: TaskCreated → Assigned → InProgress → Completed/Blocked → QAReview → QAPassed/QAFailed → Handoff
  - [ ] Guard conditions: Agent accepted task, QA gates passed
  - [ ] Entry/exit actions: Notify agent, log progress

- [ ] **Handoff Contracts для Build Process**
  - [ ] TaskCreated → Assigned: Task description, requirements
  - [ ] Assigned → InProgress: Agent acceptance
  - [ ] Completed → QAReview: Completion artifacts
  - [ ] QAPassed → Handoff: QA passed notification

- [ ] **Escalation Paths для Build Process**
  - [ ] Blocked > 30 min: Escalate to build-orchestrator
  - [ ] QA failed > 3 times: Escalate to architect
  - [ ] Task not assigned > 15 min: Escalate to build-orchestrator
  - [ ] Conflict between agents: Escalate to architect

- [ ] **Approval Gates для Build Process**
  - [ ] Gate 1 (Assigned): Agent accepted task
  - [ ] Gate 2 (Completed): Agent completed task
  - [ ] Gate 3 (QAPassed): All QA gates passed
  - [ ] Gate 4 (Handoff): Handoff accepted by next agent

## Чеклист для полного проектирования

### Workflow Architect

- [ ] **Все state machines спроектированы**
  - [ ] State machine diagrams созданы
  - [ ] Все состояния определены
  - [ ] Все переходы определены
  - [ ] State machines валидированы

- [ ] **Все workflows спроектированы**
  - [ ] Этапы workflows определены
  - [ ] Handoff contracts созданы
  - [ ] Approval gates спроектированы
  - [ ] Escalation paths спроектированы

- [ ] **Все процессы смоделированы**
  - [ ] Нотации выбраны
  - [ ] Participants определены
  - [ ] Процессы смоделированы
  - [ ] Процессы документированы

- [ ] **Все handoff packages подготовлены**
  - [ ] Информация собрана
  - [ ] Контекст упакован
  - [ ] Сообщения сформированы

- [ ] **Полная документация создана**
  - [ ] State machine diagrams включены
  - [ ] Описания состояний включены
  - [ ] Описания переходов включены
  - [ ] Handoff contracts включены
  - [ ] Escalation paths включены
  - [ ] Approval gates включены
  - [ ] Примеры использования включены

## Правила завершения

### Условия для завершения workflow проектирования

Workflow может считаться завершенным только если:

1. **Все пункты соответствующего чеклиста выполнены**
2. **Все state machines валидированы**
3. **Все handoff contracts созданы**
4. **Все escalation paths спроектированы**
5. **Все approval gates определены**
6. **Полная документация создана**
7. **Нет открытых проблем или блокировок**

### Условия для завершения полного проекта

Полный проект может считаться завершенным только если:

1. **Все workflows спроектированы**
2. **Все handoff packages подготовлены**
3. **Все чеклисты выполнены**
4. **Спецификация передана build-orchestrator**
5. **Нет блокировок для других агентов**

### Прерывание проектирования

Проектирование может быть прервано если:

1. **Требования изменились** и workflow больше не нужен
2. **Требования невозможно реализовать** в рамках workflow
3. **Решение руководства** о прекращении

При прерывании:
- [ ] Логировать причину прерывания
- [ ] Сохранить все созданные артефакты
- [ ] Создать отчет о прогрессе
- [ ] Уведомить всех вовлеченных агентов

## Примеры использования чеклиста

### Пример 1: Простой workflow (ADR Process)

```markdown
## Workflow: ADR Process

### Чеклист State Machine Design
- [x] State machine diagram создан
- [x] Состояния определены
- [x] Переходы определены
- [x] State machine валидирован

### Чеклист Workflow Design
- [x] Этапы workflow определены
- [x] Handoff contracts созданы
- [x] Approval gates спроектированы
- [x] Escalation paths спроектированы

### Чеклист Process Modeling
- [x] Нотация выбрана
- [x] Participants определены
- [x] Процесс смоделирован
- [x] Процесс документирован

### Чеклист Handoff Packaging
- [x] Информация собрана
- [x] Контекст упакован
- [x] Сообщение сформировано

### Результат: Workflow спроектирован ✅
```

### Пример 2: Сложный workflow (Build Team)

```markdown
## Workflow: Build Team Coordination

### Чеклист State Machine Design
- [x] Master state machine diagram создан
- [x] Все состояния определены
- [x] Все переходы определены
- [x] State machine валидирован

### Чеклист Workflow Design
- [x] Все этапы workflow определены
- [x] Все handoff contracts созданы
- [x] Все approval gates спроектированы
- [x] Все escalation paths спроектированы

### Чеклист Process Modeling
- [x] Все нотации выбраны
- [x] Все participants определены
- [x] Все процессы смоделированы
- [x] Все процессы документированы

### Чеклист Handoff Packaging
- [x] Все информация собрана
- [x] Все контекст упакован
- [x] Все сообщения сформированы

### Чеклист Полного проектирования
- [x] Все state machines спроектированы
- [x] Все workflows спроектированы
- [x] Все процессы смоделированы
- [x] Все handoff packages подготовлены
- [x] Полная документация создана

### Результат: Полный проект спроектирован ✅
```

### Пример 3: Workflow с отклонением

```markdown
## Workflow: Integration Contract Process

### Чеклист State Machine Design
- [x] State machine diagram создан
- [x] Состояния определены
- [x] Переходы определены
- [x] State machine валидирован

### Чеклист Workflow Design
- [x] Этапы workflow определены
- [x] Handoff contracts созданы
- [x] Approval gates спроектированы
- [ ] Escalation paths спроектированы ❌

### Результат: Workflow отклонен
Причина: Escalation paths не спроектированы
Action: Добавить escalation paths для проблем с external API
```

## Метрики качества

Для оценки качества выполнения чеклиста используются следующие метрики:

1. **Процент выполнения чеклиста**
   - 100%: Все пункты выполнены ✅
   - 80-99%: Почти все пункты выполнены, могут быть некритические пропуски
   - <80%: Значительные пропуски, требуется доработка

2. **Количество пропущенных пунктов по категориям**
   - Критические пропуски: Блокируют завершение workflow
   - Некритические пропуски: Можно исправить post-factum

3. **Время выполнения проектирования**
   - Время от получения требований до передачи спецификации
   - Сравнение с оценкой времени

4. **Количество итераций**
   - Сколько раз workflow возвращался на доработку
   - Цель: Минимум итераций (ideally 1)

5. **Количество обнаруженных проблем после интеграции**
   - Сколько проблем обнаружено после интеграции workflow
   - Цель: Минимум проблем (ideally 0)