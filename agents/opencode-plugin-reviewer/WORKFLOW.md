# OpenCode Plugin Reviewer - Workflow

## Workflow Overview

5-step workflow для review плагинов:

## Step 0: Load Documentation

**ОБЯЗАТЕЛЬНО**: Загрузить opencode-plugin-docs skill

## Step 1: Task Understanding

### Понять требования:
- Что должен делать плагин
- Какие задачи решать
- Какие constraints

## Step 2: Code Analysis

### Analyze по категориям:

#### 1. Task Alignment
- ✅ Плагин решает нужную задачу
- ✅ correct type (plugin vs tool)

#### 2. Plugin Architecture
- ✅ Правильная структура
- ✅ Separation of concerns
- ✅ Proper exports

#### 3. Plugin vs Custom Tool
- ✅ Правильный выбор типа
- ✅ Обоснование

#### 4. Hooks/Events
- ✅ Правильная регистрация
- ✅ Корректный wiring
- ✅ Lifecycle management

#### 5. Security & Side Effects
- ✅ Input validation
- ✅ No secrets exposure
- ✅ Proper error handling

#### 6. File Structure & Exports
- ✅ Структура соответствует conventions
- ✅ Exports правильные

#### 7. Readability
- ✅ Clean code
- ✅ Type hints
- ✅ Comments где нужно

#### 8. DX
- ✅ Clear API
- ✅ Error messages
- ✅ Documentation

#### 9. Orchestration Risks
- ✅ Нет блокирующих рисков
- ✅ Proper async handling

#### 10. Edge Cases
- ✅ Обработка edge cases
- ✅ Error cases

## Step 3: Findings Summary

### Формат:
```markdown
## [Category]
**Status**: ✅|❌
**Finding**: description
**Recommendation**: fix recommendation
```

## Step 4: Verdict

### Определить вердикт:
- **PASS**: Все категории ✅
- **PASS WITH CHANGES**: Minor issues
- **REVISE**: Important issues
- **REJECT**: Critical issues

## Step 5: Report Generation

### Формат отчета:
```
## Plugin Review: [Название]

### Verdict: [PASS|PASS WITH CHANGES|REVISE|REJECT]

### Summary
- Total issues: N
- Critical: N
- Important: N
- Minor: N

### Findings
[Detailed findings by category]
```

## Handoff Points

### opencode-plugin-js
Для исправления issues

### Integration Architect
Для API contract вопросов