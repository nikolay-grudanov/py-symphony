# Git Adapter Specification

**Статус**: Draft | **Версия**: 0.1

## Назначение и область применения

Данный документ определяет спецификацию интеграции с Git для Symphony сервиса.

**Цель**:
- Обеспечить интеграцию Git с workspace lifecycle
- Поддержать стандартные Git операции в рамках workflow

**Область применения**:
- Клонирование репозиториев в workspace
- Pull/push операции
- Управление ветками
- Проверка статуса репозитория
- Интеграция с workspace hooks (см. SPEC.md Section 5.3.4)

## Точки интеграции

### Workspace Hooks Integration
Git adapter интегрируется с workspace hooks на следующих этапах:

```
┌──────────────────────────────────────────────┐
│ Workspace Lifecycle                          │
├──────────────────────────────────────────────┤
│                                              │
│  after_create hook  →  git clone/checkout    │
│                                              │
│  before_run hook   →  git pull/status       │
│                                              │
│  after_run hook    →  git status/commit*    │
│                                              │
│  before_remove hook →  cleanup (optional)   │
│                                              │
└──────────────────────────────────────────────┘
```

**Примечание**: Коммиты должны выполняться coding agent через tools, не автоматически через hooks.

## Требуемые операции

### 1. `clone(repo_url, workspace_path, branch="main")`
**Назначение**: Клонирование репозитория в workspace

**Параметры**:
- `repo_url` (string) - URL репозитория (HTTPS или SSH)
- `workspace_path` (string) - путь к workspace директории
- `branch` (string, optional) - имя ветки для checkout (default: "main")

**Возвращает**: Boolean indicating success

**Детали реализации**:
- Использует `git clone --depth 1 --branch <branch>` для shallow clone
- Обрабатывает случаи, когда workspace уже существует (pull вместо clone)
- Логирует progress

### 2. `pull(workspace_path, remote="origin")`
**Назначение**: Обновление workspace из remote

**Параметры**:
- `workspace_path` (string) - путь к workspace директории
- `remote` (string, optional) - имя remote (default: "origin")

**Возвращает**: Boolean indicating success

**Детали реализации**:
- Использует `git pull` или `git fetch && git merge`
- Обрабатывает merge conflicts
- Опционально: stash local changes перед pull

### 3. `push(workspace_path, branch, remote="origin")`
**Назначение**: Отправка изменений в remote

**Параметры**:
- `workspace_path` (string) - путь к workspace директории
- `branch` (string) - имя ветки
- `remote` (string, optional) - имя remote (default: "origin")

**Возвращает**: Boolean indicating success

**Детали реализации**:
- Использует `git push <remote> <branch>`
- Обрабатывает auth failures
- Поддерживает force-push с флагом (опасно, использовать с осторожностью)

### 4. `create_branch(workspace_path, branch_name, from_branch="HEAD")`
**Назначение**: Создание новой ветки

**Параметры**:
- `workspace_path` (string) - путь к workspace директории
- `branch_name` (string) - имя новой ветки
- `from_branch` (string, optional) - точка ветвления (default: "HEAD")

**Возвращает**: Boolean indicating success

**Детали реализации**:
- Использует `git checkout -b <branch_name> <from_branch>`
- Проверяет, что ветка не существует

### 5. `checkout(workspace_path, branch_name)`
**Назначение**: Переключение на ветку

**Параметры**:
- `workspace_path` (string) - путь к workspace директории
- `branch_name` (string) - имя ветки

**Возвращает**: Boolean indicating success

**Детали реализации**:
- Использует `git checkout <branch_name>`
- Сохраняет stash при наличии uncommitted changes

### 6. `status(workspace_path)`
**Назначение**: Получение статуса репозитория

**Параметры**:
- `workspace_path` (string) - путь к workspace директории

**Возвращает**: Status object:
```json
{
  "branch": "main",
  "is_detached": false,
  "has_changes": false,
  "untracked_files": [],
  "modified_files": [],
  "staged_files": [],
  "ahead": 0,
  "behind": 0
}
```

**Детали реализации**:
- Использует `git status --porcelain` для парсинга
- Использует `git rev-list --count --left-right @{upstream}...HEAD` для ahead/behind

### 7. `get_current_commit(workspace_path)`
**Назначение**: Получение хеша текущего коммита

**Параметры**:
- `workspace_path` (string) - путь к workspace директории

**Возвращает**: Commit hash (string)

**Детали реализации**:
- Использует `git rev-parse HEAD`

### 8. `get_remote_url(workspace_path, remote="origin")`
**Назначение**: Получение URL remote репозитория

**Параметры**:
- `workspace_path` (string) - путь к workspace директории
- `remote` (string, optional) - имя remote (default: "origin")

**Возвращает**: Remote URL (string)

**Детали реализации**:
- Использует `git remote get-url <remote>`

## Аутентификация

### Поддерживаемые методы

#### 1. HTTPS с Personal Access Token
**Конфигурация**:
- `git.auth.token`: Personal Access Token или `$GIT_TOKEN`
- `git.auth.type`: "token"

**URL формат**: `https://<token>@github.com/user/repo.git`

#### 2. SSH
**Конфигурация**:
- `git.auth.ssh_key_path`: Путь к SSH ключу (опционально)
- `git.auth.ssh_key_passphrase`: Пароль для SSH ключа (опционально)
- `git.auth.type`: "ssh"

**URL формат**: `git@github.com:user/repo.git`

**Детали**:
- Использует системный SSH agent если доступен
- Поддерживает ключи с парольной фразой

#### 3. HTTPS с Username/Password (не рекомендуется)
**Конфигурация**:
- `git.auth.username`: Username
- `git.auth.password`: Password
- `git.auth.type`: "basic"

### Управление credentials
- Credential helper integration (git-credential-helper)
- Автоматическая очистка credentials из logs
- Валидация credentials при первом использовании

## Обработка ошибок

### Категории ошибок

| Категория | Описание | Обработка |
|-----------|-----------|-----------|
| `git_not_found` | Git не установлен в системе | Fatal error |
| `git_repo_not_found` | Репозиторий не найден | Fatal error |
| `git_auth_error` | Ошибка аутентификации | Fatal error |
| `git_network_error` | Ошибка сети/timeout | Retry с backoff |
| `git_merge_conflict` | Merge conflict | Fatal error (manual resolution) |
| `git_invalid_path` | Неверный путь к workspace | Fatal error |
| `git_detached_head` | Detached HEAD state | Warning |
| `git_permission_denied` | Нет прав доступа | Fatal error |

### Retry политика
- Сетевые ошибки: exponential backoff (max 3 attempts)
- Auth errors: немедленный failure (no retry)
- Merge conflicts: немедленный failure (требуется ручное разрешение)

## Конфигурация

### WORKFLOW.md front matter
```yaml
hooks:
  after_create: |
    git clone $REPO_URL . || true
    git checkout -b issue-${{issue.identifier}}

  before_run: |
    git pull origin main || echo "Pull failed, continuing..."

  after_run: |
    git status

git:
  auth:
    type: "token"
    token: "$GIT_TOKEN"
  default_branch: "main"
  remote: "origin"
```

## Безопасность

### Инварианты безопасности
1. **Workspace isolation**: Git операции выполняются только в workspace path
2. **Credential protection**: Никогда не логировать пароли или токены
3. **Path validation**: Проверять, что workspace path находится внутри workspace.root (см. SPEC.md Section 9.5)

### Рекомендации
- Использовать scoped PAT tokens с минимальными правами
- Не включать credentials в WORKFLOW.md
- Использовать environment variables для secrets

## TODO

### Определить точные hook интерфейсы
- **Задача**: Определить детальный контракт для workspace hooks интеграции
- **Детали**:
  - Явный интерфейс для Git operations в hooks
  - Сигнатуры функций и return values
  - Контекст, доступный в hooks (issue, attempt, etc.)
  - Error handling semantics для hook failures

### Дополнительные задачи
- [ ] Определить стратегию для shallow vs full clones
- [ ] Реализовать поддержку Git LFS
- [ ] Добавить поддержку submodules
- [ ] Определить поведение при uncommitted changes
- [ ] Реализовать unit tests для Git adapter
- [ ] Добавить интеграционные тесты с real Git repos
- [ ] Определить ограничения на размер репозитория
- [ ] Реализовать progress reporting для long-running operations
- [ ] Поддержать Git worktrees для multi-branch workflows
- [ ] Добавить поддержку Git hooks (pre-commit, pre-push, etc.)

## Ссылки

- SPEC.md: Symphony Service Specification
- SPEC.md Section 5.3.4: Workspace Hooks
- SPEC.md Section 9: Workspace Management and Safety
- Git Documentation: https://git-scm.com/docs
