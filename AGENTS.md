# Symphony Agents Guide

## Общая структура репозитория

- Основная реализация: `elixir/` (Elixir/OTP)
- Python-реализация (зачаточная): `runtime/`
- Спецификация: `SPEC.md` (языко-агностическая)

## Важные ссылки

- Подробная реализация для Elixir: [`elixir/AGENTS.md`](elixir/AGENTS.md)
- Конфигурация рантайма: `WORKFLOW.md` (YAML front matter + prompt template)
- PR-шаблон: [`.github/pull_request_template.md`](.github/pull_request_template.md)
- Статус реализации pluggable tracker: [`docs/tracker-implementation-status.md`](docs/tracker-implementation-status.md)
- План развития tracker адаптера: [`docs/tracker-next-steps.md`](docs/tracker-next-steps.md)

## Как запустить

```bash
cd elixir && mise exec -- ./bin/symphony ./WORKFLOW.md
```

## Quality gate

```bash
make -C elixir all
```

## PR requirements

- Обязательно использовать PR-шаблон из `.github/pull_request_template.md`
- Валидация локально:

```bash
mix pr_body.check --file /path/to/pr_body.md
```

## Логирование

См. [`elixir/docs/logging.md`](elixir/docs/logging.md) для конвенций логирования.

## Ключевые принципы

- Workspace safety: никогда не запускать Codex в рабочей директории исходного репозитория
- Workspaces должны оставаться в пределах настроенного workspace root
- Держать реализацию согласованной со `SPEC.md` (реализация может быть надмножеством, но не должна конфликтовать)

## Архитектура

Основные компоненты (подробнее в SPEC.md Section 3):

- **Workflow Loader** — читает WORKFLOW.md, парсит YAML front matter + prompt template
- **Config Layer** — типизированные геттеры для конфига с defaults и env resolution
- **Issue Tracker Client** — адаптер для Linear (другие трекеры — расширение)
- **Orchestrator** — полёт цикл, стейт-машина, retry, reconciliation
- **Workspace Manager** — маппинг issue → workspace, lifecycle hooks, cleanup
- **Agent Runner** — запуск Codex app-server, протокол over stdio
- **Status Surface** (опционально) — dashboard/API для наблюдаемости

Направления данных: WORKFLOW.md → Config → Orchestrator → Workspace → Agent Runner → Codex

## Status Tracker Adapters

**Текущее состояние:** ✅ Завершено (April 12, 2026)

Реализован pluggable tracker adapter с поддержкой множественных систем отслеживания задач.

**Документация:**
- Статус реализации: [`docs/tracker-implementation-status.md`](docs/tracker-implementation-status.md)
- План развития: [`docs/tracker-next-steps.md`](docs/tracker-next-steps.md)

**Поддерживаемые трекеры:**
- Linear (stub implementation, требует LINEAR_API_KEY)
- Jira (stub implementation, требует JIRA_API_TOKEN)
- GitHub (в планах)
- GitLab (в планах)
- Azure DevOps (в планах)

## Troubleshooting

**Стандартные проблемы:**

| Проблема | Решение |
|----------|---------|
| `WORKFLOW.md` не найден | Проверить путь, убедиться что файл существует |
| `LINEAR_API_KEY` не установлен | Экспортировать: `export LINEAR_API_KEY=...` |
| Codex не найден | Убедиться что `codex` в PATH или указать полный путь |
| Директория workspace не создаётся | Проверить права на запись в `workspace.root` |
| Мити не стартуют | Проверить активные статусы в `tracker.active_states` |
| Stuck сессия | Проверить stall_timeout_ms, логи по issue_id |

**Отладка:**

```bash
# Логирование
cd elixir && MIX_LOG=debug ./bin/symphony ./WORKFLOW.md

# Единичный тест
mix test test/symphony_elixir/some_test.exs

# Диагностика workspace
ls -la ./workspaces/
```