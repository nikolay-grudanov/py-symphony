# OpenCode Plugin JS - Workflow

## Workflow Overview

6-step workflow для разработки плагинов:

## Step 0: Load Documentation

**ОБЯЗАТЕЛЬНО**: Загрузить opencode-plugin-docs skill перед ЛЮБОЙ задачей

```bash
Load skill: opencode-plugin-docs
```

## Step 1: Task Classification

### Определить тип задачи:

| Type | Description | Example |
|------|-------------|---------|
| New Plugin | Создание нового плагина | New integration |
| Extension | Расширение существующего | Adding hooks |
| Custom Tool | Создание custom tool | New API tool |
| Refactoring | Рефакторинг плагина | Cleanup |
| Bug Fix | Исправление | Fix hook registration |

## Step 2: Architecture Selection

### Plugin Architecture
```
plugin/
├── plugin.ts          # Main entry
├── package.json
├── types.ts          # Type definitions
├── hooks.ts          # Hook implementations
├── tools/            # Custom tools
│   ├── index.ts
│   └── toolname.ts
└── README.md
```

### Custom Tool Architecture
```
tools/
├── index.ts          # Tools registry
└── toolname.ts      # Tool implementation
```

## Step 3: Code Quality

### Type Safety
- Использовать TypeScript
- Все типы определены
- No any types

### Error Handling
- Try-catch blocks
- Proper error types
- Logging errors

### Code Style
- ESLint rules
- Prettier formatting
- Clear naming

## Step 4: Context Gathering

### Собрать информацию:
- Related plugins
- Existing hooks
- API contracts
- Tests

## Step 5: Safety Assessment

### Проверить:
- Input validation
- Secrets handling
- Permissions
- Error messages

## Handoff Points

### OpenCode Plugin Reviewer
Передача для review после реализации

### Integration Architect
Для API contracts