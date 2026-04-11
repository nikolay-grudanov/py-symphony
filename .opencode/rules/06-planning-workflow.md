# Planning Workflow Rule

**Priority**: HIGH | **Applies to**: All agents

---

## Purpose

Define the standard workflow for task planning, self-criticism, and task tracking using think, criticize, and todo tools.

---

## Mandatory Planning Workflow

**EVERY agent MUST follow this 5-step workflow:**

### Step 1: Think (Plan Development)

**BEFORE starting any task**, use `think` tool to:
1. Understand the user's request
2. Identify all required actions
3. Determine dependencies between actions
4. Estimate complexity and time
5. Consider potential issues/risks

**Think format**:
```
## Analysis
[Your understanding of the task]

## Required Actions
- [ ] Action 1
- [ ] Action 2
- [ ] Action 3

## Dependencies
- Action 2 depends on Action 1
- Action 3 depends on Action 2

## Estimated Time
- Action 1: 5 minutes
- Action 2: 10 minutes
- Action 3: 15 minutes

## Potential Issues
- Issue 1: Description
- Issue 2: Description
```

---

### Step 2: Criticize (Self-Correction)

**IMMEDIATELY after planning**, use `criticize` tool to:
1. Review the plan for completeness
2. Identify gaps or missing steps
3. Check for logical errors
4. Verify all constraints are considered
5. Assess if the plan is realistic

**Criticize format**:
```
## Strengths
- Strength 1
- Strength 2

## Weaknesses
- Weakness 1: How to fix
- Weakness 2: How to fix

## Missing Elements
- Missing element 1: Impact and solution
- Missing element 2: Impact and solution

## Improved Plan
[Refined plan based on criticism]
```

---

### Step 3: Create Todo List

**AFTER criticism and plan refinement**, use `todowrite` tool to create a todo list:

```json
{
  "todos": [
    {
      "content": "Action 1 description",
      "status": "pending",
      "priority": "high",
      "id": "1"
    },
    {
      "content": "Action 2 description",
      "status": "pending",
      "priority": "medium",
      "id": "2"
    },
    {
      "content": "Action 3 description",
      "status": "pending",
      "priority": "low",
      "id": "3"
    }
  ]
}
```

**Priority levels**:
- `high`: Critical for task completion
- `medium`: Important but not blocking
- `low`: Optional or secondary tasks

---

### Step 4: Execute Tasks

**Work through the todo list sequentially:**
1. Start with first pending task
2. Mark task as `in_progress` before starting
3. Complete the task
4. Mark task as `completed` after finishing

**Status transitions**:
```
pending → in_progress → completed
     ↓
  cancelled (if task becomes unnecessary)
```

---

### Step 5: Update Todo After Each Task

**AFTER completing each task**, immediately update the todo list:

```json
{
  "todos": [
    {
      "content": "Action 1 (COMPLETED)",
      "status": "completed",
      "priority": "high",
      "id": "1"
    },
    {
      "content": "Action 2 (IN PROGRESS)",
      "status": "in_progress",
      "priority": "medium",
      "id": "2"
    },
    {
      "content": "Action 3 (PENDING)",
      "status": "pending",
      "priority": "low",
      "id": "3"
    }
  ]
}
```

---

## Critical Rule: Complete All Tasks

**DO NOT STOP until ALL todos are completed:**

- ❌ **WRONG**: Complete first 2 tasks and say "I'm done"
- ✅ **CORRECT**: Complete all 3 tasks, then provide final summary

**Only acceptable stopping conditions**:
1. ALL tasks marked as `completed`
2. User explicitly asks to stop
3. Task becomes impossible due to blocking issues (inform user first)

---

## Example Workflow

### User Request
"Create a ML project structure for customer churn prediction"

### Step 1: Think
```
## Analysis
User wants to create a new ML project with proper directory structure
for a customer churn prediction task. Need to follow ML project standards.

## Required Actions
- [ ] Create directory structure (data/, notebooks/, src/, models/, docs/, tests/)
- [ ] Create README.md with project overview
- [ ] Create requirements.txt with basic dependencies
- [ ] Create initial EDA notebook template

## Dependencies
- README.md should be created after directory structure
- Requirements.txt independent of other tasks
- EDA notebook independent of other tasks

## Estimated Time
- Directory structure: 2 minutes
- README.md: 5 minutes
- requirements.txt: 3 minutes
- EDA notebook: 5 minutes
Total: 15 minutes

## Potential Issues
- User might want specific files beyond basics
- May need to ask about model type (classification/regression)
```

### Step 2: Criticize
```
## Strengths
- Clear step-by-step approach
- Dependencies identified correctly
- Realistic time estimates

## Weaknesses
- EDA notebook template might be too generic
- Not asking user about specific requirements first
- README.md content not defined clearly

## Missing Elements
- Missing: git initialization (common for new projects)
- Missing: .gitignore file creation (should not commit data/models)
- Missing: Config file for project settings

## Improved Plan
1. Ask user for specific requirements (model type, additional files)
2. Create directory structure
3. Create README.md with specific sections (Overview, Installation, Usage)
4. Create requirements.txt
5. Create .gitignore
6. Initialize git
7. Create EDA notebook template if still needed
```

### Step 3: Create Todo

```json
{
  "todos": [
    {
      "content": "Ask user for specific project requirements",
      "status": "pending",
      "priority": "high",
      "id": "1"
    },
    {
      "content": "Create directory structure (data/, notebooks/, src/, models/, docs/, tests/)",
      "status": "pending",
      "priority": "high",
      "id": "2"
    },
    {
      "content": "Create README.md with project overview",
      "status": "pending",
      "priority": "medium",
      "id": "3"
    },
    {
      "content": "Create requirements.txt with basic dependencies",
      "status": "pending",
      "priority": "medium",
      "id": "4"
    },
    {
      "content": "Create .gitignore file",
      "status": "pending",
      "priority": "medium",
      "id": "5"
    },
    {
      "content": "Initialize git repository",
      "status": "pending",
      "priority": "low",
      "id": "6"
    },
    {
      "content": "Create EDA notebook template",
      "status": "pending",
      "priority": "low",
      "id": "7"
    }
  ]
}
```

### Step 4: Execute (Update todo after each task)

**After task 1 completed:**
```json
{
  "todos": [
    {
      "content": "Ask user for specific project requirements",
      "status": "completed",
      "priority": "high",
      "id": "1"
    },
    {
      "content": "Create directory structure (data/, notebooks/, src/, models/, docs/, tests/)",
      "status": "in_progress",
      "priority": "high",
      "id": "2"
    },
    ...
  ]
}
```

**After task 2 completed:**
```json
{
  "todos": [
    {
      "content": "Ask user for specific project requirements",
      "status": "completed",
      "priority": "high",
      "id": "1"
    },
    {
      "content": "Create directory structure (data/, notebooks/, src/, models/, docs/, tests/)",
      "status": "completed",
      "priority": "high",
      "id": "2"
    },
    {
      "content": "Create README.md with project overview",
      "status": "in_progress",
      "priority": "medium",
      "id": "3"
    },
    ...
  ]
}
```

### Step 5: Complete All Tasks

**After all 7 tasks completed:**
```json
{
  "todos": [
    {
      "content": "Ask user for specific project requirements",
      "status": "completed",
      "priority": "high",
      "id": "1"
    },
    {
      "content": "Create directory structure (data/, notebooks/, src/, models/, docs/, tests/)",
      "status": "completed",
      "priority": "high",
      "id": "2"
    },
    {
      "content": "Create README.md with project overview",
      "status": "completed",
      "priority": "medium",
      "id": "3"
    },
    {
      "content": "Create requirements.txt with basic dependencies",
      "status": "completed",
      "priority": "medium",
      "id": "4"
    },
    {
      "content": "Create .gitignore file",
      "status": "completed",
      "priority": "medium",
      "id": "5"
    },
    {
      "content": "Initialize git repository",
      "status": "completed",
      "priority": "low",
      "id": "6"
    },
    {
      "content": "Create EDA notebook template",
      "status": "completed",
      "priority": "low",
      "id": "7"
    }
  ]
}
```

**Final response to user:**
```markdown
## ✅ Project Structure Created

All tasks completed:
1. ✅ Asked for requirements
2. ✅ Created directory structure
3. ✅ Created README.md
4. ✅ Created requirements.txt
5. ✅ Created .gitignore
6. ✅ Initialized git
7. ✅ Created EDA notebook template

Project is ready for development!
```

---

## Error Handling

### If Task Fails

1. **Update todo**: Mark as `pending` or add new task to fix
2. **Think**: Analyze why it failed
3. **Criticize**: Review approach and fix plan
4. **Retry**: Attempt with corrected approach

**Example:**
```json
{
  "todos": [
    {
      "content": "Create directory structure",
      "status": "pending",
      "priority": "high",
      "id": "2"
    },
    {
      "content": "Fix permission error: investigate mkdir issue",
      "status": "in_progress",
      "priority": "high",
      "id": "8"
    },
    ...
  ]
}
```

### If Plan Changes Mid-Task

1. **Think**: Re-analyze remaining tasks
2. **Criticize**: Review updated plan
3. **Update todo**: Add/remove tasks as needed

**Example:**
```
Task 3 revealed that task 4 is unnecessary.
Update todo: Mark task 4 as cancelled.
```

---

## Best Practices

### Planning (Think)

✅ **DO**:
- Be thorough and consider all edge cases
- Estimate realistic timeframes
- Identify dependencies clearly
- Think about potential issues

❌ **DON'T**:
- Skip thinking phase
- Create overly vague plans
- Ignore dependencies
- Be overly optimistic about time

### Criticizing (Criticize)

✅ **DO**:
- Be honest about weaknesses
- Identify missing elements
- Provide specific improvements
- Update the plan based on criticism

❌ **DON'T**:
- Skip criticism phase
- Be overly negative without solutions
- Ignore valid points in the plan

### Todo Management

✅ **DO**:
- Update status immediately after each task
- Use clear, specific task descriptions
- Set appropriate priorities
- Complete ALL tasks before stopping

❌ **DON'T**:
- Forget to update status
- Leave tasks hanging (in_progress) when completed
- Stop before completing all todos
- Use vague task descriptions

---

## Validation Checklist

Before starting any task:
- [ ] Used `think` tool to create initial plan
- [ ] Used `criticize` tool to review plan
- [ ] Used `todowrite` tool to create todo list
- [ ] All tasks have clear descriptions
- [ ] All tasks have appropriate priorities

During task execution:
- [ ] Marked task as `in_progress` before starting
- [ ] Updated todo to `completed` after finishing
- [ ] Updated todo after EACH task completion

After task completion:
- [ ] ALL tasks marked as `completed`
- [ ] No tasks left in `pending` or `in_progress`
- [ ] Final summary provided to user

---

## Why This Workflow Matters

### Benefits

1. **Improved quality**: Planning + criticism = better solutions
2. **Transparency**: User sees exactly what you're doing
3. **Consistency**: Always follow the same structured approach
4. **Reliability**: Don't forget tasks or stop prematurely
5. **Error reduction**: Catch issues before implementation

### Performance Impact

Research shows:
- **Planning first**: +30% task success rate
- **Self-criticism**: +25% solution quality
- **Task tracking**: +40% completion rate
- **Combined**: ~2x improvement in task delivery

---

## Failure Modes

**NOT following this workflow** results in:
- Incomplete solutions (forgot tasks)
- Poor quality plans (no criticism)
- User frustration (unclear what's happening)
- Lost tasks (no tracking)
- Premature stopping (didn't complete all todos)

**ALWAYS use the 5-step workflow for best results.**
