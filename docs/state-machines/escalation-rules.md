# Escalation Rules

## Overview

Правила и условия эскалации для платформы оркестрации. Определяет, когда и как эскалировать проблемы Build Orchestrator → Human.

## Escalation Conditions

### 1. Блокировка задачи более 30 минут

**Description**: Задача заблокирована более 30 минут без прогресса.

**Detection**:
- Timer started при переходе в состояние Blocked
- Timer checked каждые 5 минут
- Escalation triggered при 30+ минутах

**Examples**:
- Неустранимая техническая ошибка
- Отсутствие необходимых ресурсов
- Недоступная зависимость

**Required Data**:
- Task ID
- Block start time
- Current time
- Block reason
- Agent responsible
- Context and logs

**Escalation Path**: Build Orchestrator → Human Expert

---

### 2. Конфликт между архитекторами

**Description**: Неразрешимый конфликт между архитекторами по архитектурным решениям.

**Detection**:
- Platform Architect и Workflow Architect не согласны
- Конфликт длится более 15 минут
- Разные решения для одной проблемы

**Examples**:
- Разные архитектурные паттерны
- Конфликтующие требования безопасности
- Несовместимые технологии

**Required Data**:
- Architect IDs (conflicting parties)
- Nature of conflict
- Proposed solutions from each side
- Impact analysis
- Dependencies affected

**Escalation Path**: Build Orchestrator → Senior Architect → Human Expert

---

### 3. Критический баг в основном компоненте

**Description**: Критический баг обнаружен в основном компоненте платформы.

**Detection**:
- Bug severity: Critical
- Component: Core platform component
- Impact: Blocks development or production
- Cannot be resolved by current agent

**Examples**:
- Memory leak в core runtime
- Security vulnerability в authentication
- Data corruption в state management
- Infinite loop в orchestration engine

**Required Data**:
- Bug ID
- Severity level
- Component affected
- Reproduction steps
- Impact analysis
- Attempted solutions
- Logs and stack traces

**Escalation Path**: Implementation Engineer → Verification Agent → Build Orchestrator → Human Expert

---

### 4. Нарушение сроков выполнения

**Description**: Задача превышает установленные временные рамки.

**Detection**:
- Task deadline exceeded
- No progress in last 30 minutes
- Expected completion time passed
- SLA violation imminent

**Examples**:
- Feature implementation delayed
- Bug fix not completed in time
- Documentation not ready for release
- Testing not completed

**Required Data**:
- Task ID
- Original deadline
- Current time
- Progress status
- Remaining work estimate
- Impact on dependent tasks
- Mitigation plan

**Escalation Path**: Assigned Agent → Build Orchestrator → Project Manager → Human Expert

---

## Escalation Paths

### Path 1: Standard Escalation

```
Build Orchestrator → Human Expert
```

**Use Cases**:
- Блокировка задачи (>30 минут)
- Недостаточно информации для решения
- Requires domain expertise beyond agents

**Timeline**:
- Initial escalation: Immediate
- Human response expected: Within 2 hours
- Resolution expected: Within 24 hours

**TODO**: Add escalation SLAs

---

### Path 2: Architect Conflict Escalation

```
Platform Architect + Workflow Architect → Build Orchestrator → Senior Architect → Human Expert
```

**Use Cases**:
- Конфликт между архитекторами
- Неразрешимые архитектурные противоречия
- Requires senior architectural decision

**Timeline**:
- Initial escalation: Immediate after 15 minutes
- Senior Architect response: Within 1 hour
- Human Expert response: Within 4 hours
- Resolution expected: Within 48 hours

**TODO**: Add escalation SLAs

---

### Path 3: Critical Bug Escalation

```
Implementation Engineer → Verification Agent → Build Orchestrator → Human Expert
```

**Use Cases**:
- Критический баг в основном компоненте
- Production issue
- Security vulnerability

**Timeline**:
- Initial escalation: Immediate
- Human Expert response: Within 30 minutes
- Resolution expected: Within 4 hours (production) or 24 hours (development)

**TODO**: Add escalation SLAs

---

### Path 4: Deadline Escalation

```
Assigned Agent → Build Orchestrator → Project Manager → Human Expert
```

**Use Cases**:
- Нарушение сроков выполнения
- SLA violation
- Critical milestone missed

**Timeline**:
- Initial escalation: Immediate
- Project Manager response: Within 30 minutes
- Human Expert response: Within 2 hours
- Resolution expected: Within 8 hours

**TODO**: Add escalation SLAs

---

## Escalation Data Requirements

### Standard Escalation Package

```json
{
  "escalation_id": "unique_id",
  "escalation_type": "block_timeout | architect_conflict | critical_bug | deadline_miss",
  "escalation_severity": "low | medium | high | critical",
  "timestamp": "ISO_8601_timestamp",
  "source_state": "current_state",
  "escalation_path": ["agent1", "agent2", "..."],
  
  "task_context": {
    "task_id": "task_id",
    "task_type": "architecture | implementation | verification | testing",
    "task_priority": "low | medium | high | critical",
    "deadline": "ISO_8601_timestamp",
    "assignee": "agent_id",
    "status": "blocked | in_progress | etc."
  },
  
  "escalation_trigger": {
    "trigger_type": "timer | manual | event",
    "trigger_value": "specific_value",
    "trigger_timestamp": "ISO_8601_timestamp"
  },
  
  "problem_description": {
    "summary": "Brief summary",
    "detailed_description": "Full description",
    "impact_analysis": "Impact on system",
    "affected_components": ["component1", "component2"],
    "blocking_dependencies": ["dep1", "dep2"]
  },
  
  "attempted_solutions": [
    {
      "solution": "Description",
      "timestamp": "ISO_8601_timestamp",
      "result": "success | failure | partial",
      "error": "Error message if any"
    }
  ],
  
  "required_information": [
    "Additional info needed"
  ],
  
  "attachments": [
    {
      "type": "log | screenshot | document",
      "url": "attachment_url",
      "description": "Attachment description"
    }
  ],
  
  "metadata": {
    "escalation_source": "agent_id",
    "escalation_history": [],
    "custom_fields": {}
  }
}
```

### Architect Conflict Package

```json
{
  "escalation_id": "unique_id",
  "escalation_type": "architect_conflict",
  "timestamp": "ISO_8601_timestamp",
  
  "conflicting_parties": {
    "party_a": {
      "agent_id": "platform_architect",
      "proposed_solution": "Solution A",
      "rationale": "Rationale for A",
      "impact_analysis": "Impact of A"
    },
    "party_b": {
      "agent_id": "workflow_architect",
      "proposed_solution": "Solution B",
      "rationale": "Rationale for B",
      "impact_analysis": "Impact of B"
    }
  },
  
  "conflict_analysis": {
    "conflict_type": "architectural_pattern | technology | security | integration",
    "conflict_severity": "low | medium | high | critical",
    "conflict_duration_minutes": 15,
    "resolution_attempts": 3
  },
  
  "recommendation": {
    "recommended_approach": "senior_architect | human_expert | vote",
    "recommended_decision": "Suggested decision",
    "reasoning": "Reasoning for recommendation"
  }
}
```

### Critical Bug Package

```json
{
  "escalation_id": "unique_id",
  "escalation_type": "critical_bug",
  "escalation_severity": "critical",
  "timestamp": "ISO_8601_timestamp",
  
  "bug_information": {
    "bug_id": "BUG-001",
    "severity": "critical",
    "component": "core_runtime",
    "environment": "production | development | staging",
    "reproduction_steps": [
      "Step 1",
      "Step 2"
    ],
    "expected_behavior": "Expected behavior",
    "actual_behavior": "Actual behavior",
    "error_message": "Error message",
    "stack_trace": "Stack trace"
  },
  
  "impact_analysis": {
    "affected_users": "number_of_users",
    "affected_services": ["service1", "service2"],
    "business_impact": "Description",
    "workaround_available": true | false,
    "workaround_description": "Workaround steps"
  },
  
  "attempted_fixes": [
    {
      "fix_description": "Fix attempt",
      "timestamp": "ISO_8601_timestamp",
      "result": "success | failure | partial",
      "regression_test": "pass | fail | not_run"
    }
  ]
}
```

## De-escalation Process

### Process Overview

1. **Resolution**: Human Expert or Senior Architect resolves the issue
2. **Solution Implementation**: Solution is implemented by appropriate agent
3. **Verification**: Verification Agent verifies the solution
4. **Documentation**: Solution is documented
5. **De-escalation**: System returns to normal operation

### Step 1: Resolution

**Responsibility**: Human Expert / Senior Architect

**Actions**:
- Analyze the problem
- Provide solution or decision
- Document reasoning
- Assign implementation task

**Timeline**: According to escalation path timeline

**Outputs**:
- Solution description
- Implementation instructions
- Updated requirements if needed

---

### Step 2: Solution Implementation

**Responsibility**: Assigned Agent

**Actions**:
- Implement the solution
- Update code/architecture
- Update documentation
- Test the solution

**Timeline**: Dependent on solution complexity

**Outputs**:
- Implemented solution
- Updated code/architecture
- Updated documentation
- Test results

---

### Step 3: Verification

**Responsibility**: Verification Agent

**Actions**:
- Verify the solution
- Test for regressions
- Validate requirements
- Approve or reject

**Timeline**: 1-4 hours depending on complexity

**Outputs**:
- Verification report
- Test results
- Approval/rejection

---

### Step 4: Documentation

**Responsibility**: Build Orchestrator

**Actions**:
- Document the escalation
- Update knowledge base
- Create ADR if needed
- Share lessons learned

**Timeline**: 1-2 hours

**Outputs**:
- Escalation record
- Updated documentation
- ADR if applicable

---

### Step 5: De-escalation

**Responsibility**: Build Orchestrator

**Actions**:
- Remove escalation flag
- Update state machine state
- Resume normal operation
- Notify stakeholders

**Timeline**: Immediate

**Outputs**:
- System in normal state
- Stakeholders notified
- Task resumed

---

## Escalation Timeline Matrix

| Escalation Type | Initial Response | Human Expert | Resolution | SLA |
|----------------|-----------------|--------------|------------|-----|
| Block Timeout | Immediate | 2 hours | 24 hours | 24 hours |
| Architect Conflict | Immediate | 4 hours | 48 hours | 48 hours |
| Critical Bug (Production) | Immediate | 30 min | 4 hours | 4 hours |
| Critical Bug (Dev) | Immediate | 2 hours | 24 hours | 24 hours |
| Deadline Miss | Immediate | 2 hours | 8 hours | 8 hours |

**TODO**: Add escalation SLAs

## Escalation Notifications

### Notification Types

1. **Escalation Initiated**: Уведомление о начале эскалации
2. **Escalation Acknowledged**: Подтверждение получения эскалации
3. **Escalation In Progress**: Прогресс решения
4. **Escalation Resolved**: Решение предоставлено
5. **Escalation Completed**: Эскалация завершена

### Notification Channels

1. **Agent Channel**: Direct channel между агентами
2. **Email Channel**: Email уведомления для людей
3. **Slack Channel**: Slack уведомления для команды
4. **System Log**: System-wide logging

### Notification Recipients

| Escalation Type | Build Orchestrator | Architect | Implementation | Human Expert |
|-----------------|-------------------|-----------|----------------|--------------|
| Block Timeout | ✅ | - | ✅ | ✅ |
| Architect Conflict | ✅ | ✅ | - | ✅ |
| Critical Bug | ✅ | - | ✅ | ✅ |
| Deadline Miss | ✅ | - | ✅ | ✅ |

## Escalation Metrics

### Key Metrics

1. **Escalation Count**: Total number of escalations
2. **Escalation Rate**: Escalations per day/week/month
3. **Escalation by Type**: Breakdown by escalation type
4. **Escalation by Severity**: Breakdown by severity
5. **Average Resolution Time**: Time from escalation to resolution
6. **Escalation Success Rate**: Percentage of escalations resolved

### Metrics Dashboard

```
Escalation Metrics Dashboard (Last 30 Days)

Total Escalations: 45
Escalation Rate: 1.5/day
Success Rate: 95.6%
Average Resolution Time: 6.2 hours

By Type:
- Block Timeout: 20 (44.4%)
- Architect Conflict: 5 (11.1%)
- Critical Bug: 15 (33.3%)
- Deadline Miss: 5 (11.1%)

By Severity:
- Low: 10 (22.2%)
- Medium: 20 (44.4%)
- High: 10 (22.2%)
- Critical: 5 (11.1%)

Resolution Time by Type:
- Block Timeout: 8.5 hours
- Architect Conflict: 24.0 hours
- Critical Bug: 3.2 hours
- Deadline Miss: 6.0 hours
```

## Escalation Prevention

### Prevention Strategies

1. **Proactive Monitoring**: Мониторинг задач для раннего обнаружения проблем
2. **Clear Requirements**: Четкие требования и спецификации
3. **Resource Planning**: Правильное планирование ресурсов
4. **Knowledge Base**: База знаний для повторяющихся проблем
5. **Agent Training**: Обучение агентов для самостоятельного решения

### Best Practices

1. **Early Detection**: Выявлять проблемы до эскалации
2. **Clear Communication**: Четкая коммуникация между агентами
3. **Document Everything**: Документировать все решения
4. **Learn from Escalations**: Учиться на эскалациях
5. **Continuous Improvement**: Непрерывное улучшение процессов

## Related Documentation

- [Platform State Machine](./platform-state-machine.md)
- [Build Process State Machine](./build-process-state-machine.md)
- [Transition Rules](./transition-rules.md)
- [Approval Gates](./approval-gates.md)
- [State Machines Overview](../state-machines.md)
- [Build Orchestrator](../.opencode/agents/build-orchestrator.md)
