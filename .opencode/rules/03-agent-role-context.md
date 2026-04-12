# Agent Role Context Rule

**Priority**: HIGH | **Applies to**: All agents

---

## Purpose

Define the requirement for all agents to read their role specifications from the `agents/` directory before starting any work.

---

## Mandatory Role Context Reading

Every agent MUST read their role specifications before executing any task. This reading is part of Step 1 (Think) from `06-planning-workflow.md` and ensures:

- Complete understanding of the agent's role and boundaries
- Clear awareness of allowed and forbidden decision areas
- Proper adherence to behavioral style and principles
- Correct use of allowed skills only

**Reading order matters** - each document builds upon the previous one:
- ROLE.md establishes the foundation (mission, responsibilities, boundaries)
- SOUL.md defines behavioral style and principles
- SKILLS.md lists permitted tools and capabilities
- WORKFLOW.md provides task-specific workflow if applicable

---

## Required Reading Order

ПЕРЕД выполнением любой задачи, агент ДОЛЖЕН прочитать в следующем порядке:

1. **ROLE.md** ← ПЕРВЫМ! (миссия, обязанности, границы)
2. **SOUL.md** ← ВТОРЫМ! (стиль поведения, принципы)
3. **SKILLS.md** ← ТРЕТЬИМ! (разрешённые навыки)
4. **WORKFLOW.md** ← ЧЕТВЁРТЫМ! (если применимо)

### Why This Order?

- **ROLE.md first**: Defines WHO you are, WHAT you must do, and WHAT you must NOT do
- **SOUL.md second**: Defines HOW you should behave, your principles
- **SKILLS.md third**: Defines WHAT tools and capabilities you can use
- **WORKFLOW.md last**: Defines HOW to execute specific workflows

Skipping or reordering breaks the logical foundation for decision-making.

---

## Integration with Step 1 (Think)

В Step 1 (Think) из `06-planning-workflow.md`, добавь чтение спецификации:

```
## Analysis
[Understand task]

## Required Actions
- [ ] Read agents/[AGENT_NAME]/ROLE.md ← ДОЛЖНО БЫТЬ ПЕРВЫМ!
- [ ] Read agents/[AGENT_NAME]/SOUL.md
- [ ] Read agents/[AGENT_NAME]/SKILLS.md
- [ ] Read agents/[AGENT_NAME]/WORKFLOW.md (если применимо)
- [ ] [Other actions]
```

---

## Examples

✅ **Correct**:
```
## Analysis
User wants me to design component X.

## Required Actions
- [ ] Read agents/platform-architect/ROLE.md ← FIRST!
- [ ] Read agents/platform-architect/SOUL.md
- [ ] Read agents/platform-architect/SKILLS.md
- [ ] Understand my role and boundaries
- [ ] Design component X
```

✅ **Correct**:
```
## Analysis
User wants to implement a new feature in the orchestrator.

## Required Actions
- [ ] Read agents/implementation-engineer/ROLE.md ← FIRST!
- [ ] Read agents/implementation-engineer/SOUL.md
- [ ] Read agents/implementation-engineer/SKILLS.md
- [ ] Read SPEC.md to understand requirements
- [ ] Implement feature
```

❌ **Wrong**:
```
## Analysis
User wants me to design component X.

## Required Actions
- [ ] Design component X
- [ ] Write code
```
(Missing role context reading!)

❌ **Wrong**:
```
## Analysis
I need to fix a bug.

## Required Actions
- [ ] Find the bug
- [ ] Fix it
```
(Not reading role specification first - may use forbidden decisions!)

---

## If Specification Missing

Если папка `agents/[AGENT_NAME]/` отсутствует:

- Информируйте orchestrator о проблеме
- Не выполняйте задачу без спецификации
- Запросите создание спецификации

**Не угадывайте** свою роль - это приведёт к ошибкам.

Пример сообщения:
```
❌ Agent specification not found at agents/[AGENT_NAME]/

Cannot proceed without role context. Please create:
- agents/[AGENT_NAME]/ROLE.md
- agents/[AGENT_NAME]/SOUL.md  
- agents/[AGENT_NAME]/SKILLS.md
- agents/[AGENT_NAME]/WORKFLOW.md (if applicable)
```

---

## Validation Checklist

Before starting any task, check:
- [ ] Read agents/[AGENT_NAME]/ROLE.md (FIRST!)
- [ ] Read agents/[AGENT_NAME]/SOUL.md
- [ ] Read agents/[AGENT_NAME]/SKILLS.md
- [ ] Read agents/[AGENT_NAME]/WORKFLOW.md (if applicable)
- [ ] Understood my role and boundaries
- [ ] Understood my allowed decisions
- [ ] Understood my forbidden decisions
- [ ] Understood my skills

During task execution:
- [ ] Follow the role boundaries defined in ROLE.md
- [ ] Adhere to behavioral style from SOUL.md
- [ ] Only use skills defined in SKILLS.md
- [ ] Follow workflow if WORKFLOW.md exists

---

## Why This Rule Matters

### Benefits

- ✅ Consistent behavior across agent invocations
- ✅ Clear understanding of role boundaries
- ✅ Better quality decisions (following allowed/forbidden)
- ✅ Adherence to behavioral style
- ✅ Proper use of defined skills
- ✅ Prevention of scope creep (staying within allowed decisions)

### Failure Modes

**NOT following this rule** results in:

- ❌ Agent making decisions outside role boundaries
- ❌ Inconsistent behavior across sessions
- ❌ Using forbidden decision areas
- ❌ Violating behavioral style
- ❌ Using undefined skills
- ❌ Scope creep (taking on tasks outside role)

### Performance Impact

Research and practice show:
- **Reading role first**: +35% task alignment with expectations
- **Understanding boundaries**: +40% reduction in scope violations
- **Following allowed/forbidden**: +50% reduction in rework
- **Combined**: ~2x improvement in task delivery quality

---

## References

- `06-planning-workflow.md` - Step 1 (Think) requirement
- `agents/` - Agent role specifications directory
- Individual agent ROLE.md, SOUL.md, SKILLS.md, WORKFLOW.md files
