<!--
Sync Impact Report:
Version change: 1.0.0 → 1.0.1
Modified principles: N/A (initial full version)
Added sections: All (initial version)
Removed sections: None
Templates requiring updates:
  - ✅ plan-template.md - Constitution Check section already compatible with quality gates
  - ✅ spec-template.md - No changes needed (focuses on user stories, not constraints)
  - ✅ tasks-template.md - No changes needed (organizes by user stories, not principles)
Follow-up TODOs: None
-->

# py-symphony Constitution

**Версия**: 1.0.1 | **Ратифицирована**: 2026-04-13 | **Последнее изменение**: 2026-04-13

> Этот документ содержит **неизменяемые инварианты** системы py-symphony.
> Любое изменение в репозитории, которое нарушает хотя бы один пункт этой конституции,
> должно быть заблокировано — независимо от дедлайна, удобства или мнения агента.
>
> Операциональные детали (роутинг, шаблоны handoff, навыки агентов) живут в:
> `agents/build-orchestrator/WORKFLOW.md`, `HANDOFFS.md`, `SKILLS.md`, `SOUL.md`, `CHECKLIST.md`.

---

## 1. Идентичность системы

**py-symphony** — открытая Python-платформа оркестрации задач разработки.
Система диспетчеризует задачи к AI-агентам через polling loop.

Два фундаментальных свойства системы, которые НИКОГДА не нарушаются:

- **Tracker-agnostic**: runtime не знает ни о каком конкретном трекере задач.
- **Agent-agnostic**: runtime не знает ни о каком конкретном AI-агенте или CLI-инструменте.

Репозиторий: https://github.com/nikolay-grudanov/py-symphony
Спецификация (источник правды): `SPEC.md`

---

## 2. Технологический стек (инварианты)

### Язык и рантайм
- Python **3.11+** минимум, 3.13 предпочтительно.
- Строгие type annotations везде. `mypy --strict` **обязан** проходить перед merge.
- `Any` запрещён без явного комментария-обоснования рядом с использованием.

### Управление зависимостями
- **uv** — единственный разрешённый инструмент.
- `pip install` напрямую — **нарушение конституции**.
- `uv.lock` всегда коммитится в репозиторий.
- Dev-зависимости: `uv add --dev <package>`.
- Запуск скриптов: `uv run pytest`, `uv run python`, etc.

### Тестирование
- **pytest** — единственный разрешённый тест-раннер. unittest, nose — запрещены.
- Минимальный coverage: **80%** для любого модуля.
- Критические модули (runtime core, state machine): **90%+**.
- Структура тестов зеркалит структуру источников: `plugins/X/tests/test_*.py`.

### Качество кода
- **ruff check** + **ruff format** — оба обязательны перед merge.
- Максимальная длина строки: **100 символов**.
- Все публичные методы — с docstring.
- `except:` без явного типа исключения — **запрещён**.

---

## 3. Tracker Agnosticism Contract

### Инвариант
`runtime/` **не содержит** никакой tracker-specific логики.

### Проверяемые нарушения (любое из ниже = нарушение конституции):
- В `runtime/` есть прямой импорт: `import linear`, `import jira`, `import yandex_tracker` и т.п.
- В `runtime/` используется `LINEAR_API_KEY`, `JIRA_API_TOKEN` или любая tracker-specific переменная окружения.
- В `runtime/` есть HTTP-запросы к конкретному tracker API.
- В `runtime/` есть условные ветки вида `if tracker_type == "linear"`.

### Правильная точка расширения
- Интерфейс: `runtime/tracker/base.py` → класс `TrackerClient`.
- Реализация: `plugins/symphony-<tracker>/` — отдельный пакет со своим `pyproject.toml`.
- Добавление нового трекера = новый плагин, **ноль изменений в `runtime/`**.
- Регистрация: `entry_points` под `symphony.trackers`.

---

## 4. Agent Backend Agnosticism Contract

### Инвариант
`runtime/` **не содержит** никакой agent-specific логики.

### Проверяемые нарушения (любое из ниже = нарушение конституции):
- В `runtime/` есть прямой импорт: `import opencode`, `import codex`, `import claude_code` и т.п.
- В `runtime/` есть CLI-вызовы конкретного агента: `subprocess.run(["opencode", ...])`, `subprocess.run(["codex", ...])`.
- В `runtime/` есть условные ветки вида `if agent_type == "opencode"`.
- В `runtime/` есть конфигурационные ключи, специфичные для конкретного агента.

### Правильная точка расширения
- Интерфейс: `AgentBackend` base class в `runtime/`.
- Реализация: `plugins/symphony-<backend>/` — отдельный пакет.
- Добавление нового агента = новый плагин, **ноль изменений в `runtime/`**.
- Регистрация: `entry_points` под `symphony.backends`.

---

## 5. Plugin Isolation Contract

### Инвариант
Плагины **не импортируют** друг друга.

### Проверяемые нарушения:
- `plugins/symphony-linear/` импортирует из `plugins/symphony-jira/` или любого другого плагина.
- Плагин использует внутренние классы другого плагина напрямую, не через `runtime/` интерфейс.

### Правила:
- Общая логика, нужная нескольким плагинам → выносится в `runtime/`.
- Плагин может зависеть только от `runtime/` и внешних пакетов.

### Структура каждого плагина (обязательно):
```
plugins/symphony-<name>/
├── pyproject.toml      ← независимый, со своим entry_point
├── README.md
└── tests/
    └── test_*.py
```

---

## 6. State Machine Contract

### Допустимые состояния задачи:
```
UNCLAIMED → CLAIMED → RUNNING → RELEASED
```

### Инварианты:
- Переходы **атомарны** — нет промежуточных или неопределённых состояний.
- **Неявных переходов нет** — каждый переход явно инициирован кодом.
- Нет перехода из `RELEASED` назад в `RUNNING` без явного re-claim.
- Нет перехода через состояние (например, `UNCLAIMED → RUNNING` минуя `CLAIMED`).

---

## 7. Architecture Decision Records (ADR)

### Обязательность
ADR **создаётся** для каждого изменения, которое затрагивает:
- Новый runtime-компонент.
- Новый плагин (tracker adapter или agent backend).
- Изменение state machine.
- Изменение plugin registration contract.
- Любое изменение публичного API `runtime/`.

### Исключения (ADR не требуется):
- Bug fix без изменения контрактов.
- Documentation-only изменение.

### Структура ADR (обязательные секции):
1. **Status**: `Accepted` / `Rejected` / `Superseded by ADR-XXX`
2. **Context** — проблема и требование
3. **Alternatives** — минимум 2 рассмотренных альтернативы
4. **Decision** — выбранное решение с обоснованием
5. **Consequences** — плюсы, минусы, риски
6. **SPEC.md compliance** — ссылки на разделы SPEC.md

ADR хранятся в: `docs/adr/`

---

## 8. Quality Gates (строгий порядок, все обязательны)

Ни один gate не может быть пропущен. Порядок нарушать нельзя.

```
Gate 1: ADR создан и записан в docs/adr/
        (исключение: bug_fix, documentation_only)
        ↓
Gate 2: Реализация создана. PR открыт.
        uv run pytest    — все тесты зелёные
        Coverage ≥ 80%   (критические модули ≥ 90%)
        mypy --strict    — без ошибок
        ruff check       — без ошибок
        ruff format      — без ошибок
        ↓
Gate 3: code-reviewer вернул APPROVED
        ↓
Gate 4: verification-agent вернул PASSED
        (соответствие SPEC.md подтверждено)
        ↓
Gate 5: MERGE разрешён
```

**Любой gate, не пройденный в правильном порядке = БЛОКИРОВКА.**

---

## 9. Build-Orchestrator: абсолютные запреты

Агент `build-orchestrator` **НИКОГДА**:

- не пишет код — ни строчки, ни фрагмента.
- не принимает архитектурные решения — это ответственность архитекторов.
- не выбирает библиотеки, фреймворки, инструменты.
- не пропускает QA Gates — даже под давлением дедлайна или просьбы.
- не делает merge без прохождения всех Gate 1–5.
- не угадывает `task_type` при неоднозначности — спрашивает человека.
- не пытается resolve агентный сбой больше **одного раза** самостоятельно.

### При сбое агента:
1. Один retry — и только один.
2. Если повтор не помог → записывает комментарий в трекер по шаблону эскалации из `SOUL.md`.
3. Задача остаётся в состоянии `CLAIMED` до ответа человека.
4. Без явного разрешения человека — задача **не переназначается**.

### Классификация task_type:
- Источник: метка задачи в трекере + ключевые слова в названии/описании.
- Детальные правила классификации: `agents/build-orchestrator/WORKFLOW.md §1`.
- При неоднозначности → уточняющий вопрос в трекере, работа не начинается.

---

## 10. Файловые инварианты

```
py-symphony/
├── runtime/          ← ТОЛЬКО агностический код. Никакого tracker/agent кода.
├── plugins/          ← Один пакет = одна интеграция
│   └── symphony-<name>/
│       ├── pyproject.toml
│       ├── README.md
│       └── tests/
├── agents/           ← Определения агентов opencode
│   └── <agent-name>/
│       ├── ROLE.md
│       ├── SKILLS.md
│       ├── WORKFLOW.md
│       ├── HANDOFFS.md
│       ├── CHECKLIST.md
│       └── SOUL.md
├── docs/
│   └── adr/          ← Все ADR здесь
├── integrations/     ← Спецификации внешних API
├── workflows/        ← WORKFLOW.md файлы для Symphony задач
└── schemas/          ← JSON schemas для валидации конфигов
```

### Запреты:
- `requirements.txt` не используется — только `uv` и `uv.lock`.
- Tracker-specific код вне `plugins/` — **нарушение конституции**.
- Agent-specific код вне `plugins/` — **нарушение конституции**.

---

## 11. Соответствие SPEC.md

- `SPEC.md` — **главный источник правды** о поведении системы.
- При конфликте SPEC.md и любого другого документа — **SPEC.md имеет приоритет**.
- При конфликте SPEC.md и конституции — поднимается ADR для разрешения.
- Verification-agent проверяет соответствие SPEC.md перед каждым merge (Gate 4).

---

## 12. Чеклист нарушений конституции

Любое из ниже = **блокировка merge**:

- Прямой импорт tracker/agent библиотек в `runtime/`
- Tracker/agent-specific env vars в `runtime/`
- HTTP-запросы к конкретному tracker/agent API в `runtime/`
- Условные ветки `if tracker_type ==` или `if agent_type ==` в `runtime/`
- Плагин импортирует другой плагин напрямую
- Отсутствует ADR для архитектурного изменения
- Использован `pip install` вместо `uv`
- `requirements.txt` существует в репозитории
- Coverage < 80% (или < 90% для критических модулей)
- `mypy --strict` не проходит
- `ruff check` или `ruff format` не проходит
- `.opencode/` закоммичен в репозиторий
- Build-orchestrator сделал merge без прохождения всех Gate 1–5

---

## Изменение конституции

Конституция изменяется **только через ADR** с явным указанием:
- Какой инвариант меняется и почему.
- Какие последствия для существующих плагинов и runtime.
- Approval от владельца проекта.

Рутинные изменения (добавление агента в roster, изменение шаблонов handoff,
обновление тайм-аутов мониторинга) — **не требуют изменения конституции**.
Они вносятся в соответствующие операциональные файлы агента.


**Version**: 1.0.1 | **Ratified**: 2026-04-13 | **Last Amended**: 2026-04-13