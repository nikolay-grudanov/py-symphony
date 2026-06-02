# py-symphony Agents Inventory

## Overview

14 агентов с распределением по моделям MiniMax:
- **M2.7**: 1 агент (оркестратор)
- **M2.5**: 6 агентов (архитекторы + верификация)
- **M2.1**: 7 агентов (исполнители + плагины)

---

## Orchestrator (M2.7)

| Agent | Role | Model | Temp |
|-------|------|-------|------|
| `build-orchestrator` | Координация задач, управление workflow | M2.7 | 0.7 |

---

## Architects & Verification (M2.5)

| Agent | Role | Model | Temp |
|-------|------|-------|------|
| `platform-architect` | Архитектура платформы | M2.5 | 0.5 |
| `agent-runtime-architect` | Runtime протоколы | M2.5 | 0.5 |
| `integration-architect` | API контракты | M2.5 | 0.5 |
| `workflow-architect` | Workflow дизайн | M2.5 | 0.5 |
| `verification-agent` | Верификация артефактов | M2.5 | 0.4 |
| `code-reviewer` | Code review | M2.5 | 0.3 |

---

## Executors (M2.1)

| Agent | Role | Model | Temp |
|-------|------|-------|------|
| `implementation-engineer` | Реализация кода | M2.1 | 0.3 |
| `python-coder` | Python разработка | M2.1 | 0.3 |
| `test-engineer` | Тестирование | M2.1 | 0.3 |
| `documentation-writer` | Документация | M2.1 | 0.3 |
| `researcher` | Исследование | M2.1 | 0.8 |

---

## Plugins (M2.1)

| Agent | Role | Model | Temp |
|-------|------|-------|------|
| `opencode-plugin-js` | JS плагины | M2.1 | 0.3 |
| `opencode-plugin-reviewer` | Ревью плагинов | M2.1 | 0.3 |

---

## Agent Prompts

Каждый агент использует ROLE.md из директории `./agents/{agent-name}/ROLE.md`:

```
build-orchestrator        → ./agents/build-orchestrator/ROLE.md
platform-architect       → ./agents/platform-architect/ROLE.md
agent-runtime-architect  → ./agents/agent-runtime-architect/ROLE.md
integration-architect    → ./agents/integration-architect/ROLE.md
workflow-architect       → ./agents/workflow-architect/ROLE.md
verification-agent       → ./agents/verification-agent/ROLE.md
code-reviewer            → ./agents/code-reviewer/ROLE.md
implementation-engineer  → ./agents/implementation-engineer/ROLE.md
python-coder             → ./agents/python-coder/ROLE.md
test-engineer            → ./agents/test-engineer/ROLE.md
documentation-writer     → ./agents/documentation-writer/ROLE.md
researcher               → ./agents/researcher/ROLE.md
opencode-plugin-js       → ./agents/opencode-plugin-js/ROLE.md
opencode-plugin-reviewer → ./agents/opencode-plugin-reviewer/ROLE.md
```

---

## Files Structure

```
.opencode/
├── opencode.json        # Main config (agents + global settings)
└── agents/
    ├── agents-config.json  # Detailed config reference
    └── INVENTORY.md         # Этот файл
```

---

## Model Distribution Summary

| Tier | Count | Agents | Use Case |
|------|-------|--------|----------|
| **M2.7** | 1 | orchestrator | Coordination, strategy |
| **M2.5** | 6 | architects, verification | Architecture, deep analysis |
| **M2.1** | 7 | executors, plugins | Fast execution, templates |
