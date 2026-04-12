# CI/CD Adapter Specification

**Статус**: Draft | **Версия**: 0.1

## Назначение и область применения

Данный документ определяет спецификацию интеграции с CI/CD системами для Symphony сервиса.

**Цель**:
- Обеспечить интеграцию CI/CD pipelines с workflow Symphony
- Поддержать автоматический запуск CI на основе изменений в issue tracker

**Область применения**:
- Триггеры для запуска CI пайплайнов
- Интеграция с WORKFLOW.md для определения pipeline stages
- Отчетность об артефактах и результатах CI
- Поддержка различных CI providers (GitHub Actions, GitLab CI, Jenkins, etc.)

## Архитектура интеграции

### Компоненты
```
┌─────────────────┐     ┌─────────────────┐
│   Orchestrator  │────▶│  CI/CD Adapter   │
│                 │     │  - Trigger       │
│  - Issue State  │     │  - Monitor       │
│  - PR Events    │     │  - Report        │
└─────────────────┘     └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ CI Provider     │
                       │ (GitHub/GitLab  │
                       │  Jenkins/etc)   │
                       └─────────────────┘
```

### Интеграция с WORKFLOW.md
CI конфигурация определяется в WORKFLOW.md front matter (см. SPEC.md Section 5.3):

```yaml
ci:
  provider: "github-actions"  # or "gitlab-ci", "jenkins", etc.
  triggers:
    on_issue_change: true
    on_pr_create: true
    on_pr_update: true
    manual: true
  pipeline:
    stages:
      - name: "build"
        timeout_ms: 300000
      - name: "test"
        timeout_ms: 600000
      - name: "deploy"
        timeout_ms: 900000
        condition: "branch == 'main'"
```

## Триггеры CI

### 1. Issue Change Trigger
**Назначение**: Запуск CI при изменении состояния issue

**Условия запуска**:
- Issue переходит в активное состояние
- Issue обновляется с определенными label changes
- Конфигурируемый фильтр по issue state/labels

**Параметры**:
- `issue` (Issue entity) - нормализованная сущность issue
- `previous_state` (string, optional) - предыдущее состояние issue
- `labels_changed` (list of strings, optional) - измененные labels

**Возвращает**: CI run ID (string) или error

### 2. Pull Request Create Trigger
**Назначение**: Запуск CI при создании PR

**Условия запуска**:
- PR создан из ветки, связанной с issue
- PR target branch соответствует конфигурации
- Конфигурируемый фильтр по PR labels/files

**Параметры**:
- `pr_id` (string) - ID PR
- `source_branch` (string) - source branch
- `target_branch` (string) - target branch
- `issue_identifier` (string, optional) - связанный issue identifier

**Возвращает**: CI run ID (string) или error

### 3. Pull Request Update Trigger
**Назначение**: Запуск CI при обновлении PR

**Условия запуска**:
- Новые коммиты в PR
- Изменения в PR description/labels
- Конфигурируемый debounce для частых обновлений

**Параметры**:
- `pr_id` (string) - ID PR
- `last_commit_hash` (string) - хеш последнего коммита
- `issue_identifier` (string, optional) - связанный issue identifier

**Возвращает**: CI run ID (string) или error

### 4. Manual Trigger
**Назначение**: Ручной запуск CI

**Параметры**:
- `issue_identifier` (string) - issue identifier
- `branch` (string, optional) - branch для запуска
- `stages` (list of strings, optional) - список stages для запуска

**Возвращает**: CI run ID (string) или error

## Pipeline Stages

### Общая структура pipeline
Pipeline состоит из последовательных stages, определенных в WORKFLOW.md:

```
┌─────────────────────────────────────────┐
│           CI Pipeline                   │
├─────────────────────────────────────────┤
│                                         │
│  Stage 1: Build                         │
│    - Build artifacts                    │
│    - Compile code                       │
│    - Dependencies                       │
│                                         │
│  Stage 2: Test                          │
│    - Unit tests                         │
│    - Integration tests                  │
│    - Linting                            │
│                                         │
│  Stage 3: Deploy (conditional)          │
│    - Deploy to staging                  │
│    - Deploy to production (main only)   │
│                                         │
└─────────────────────────────────────────┘
```

### Стандартные stages

#### Build Stage
**Назначение**: Сборка артефактов

**Конфигурация**:
```yaml
stages:
  - name: "build"
    timeout_ms: 300000
    commands:
      - "npm install"
      - "npm run build"
    artifacts:
      - path: "dist/"
        name: "build-artifacts"
```

**Детали реализации**:
- Выполняется в workspace directory
- Timeout из конфигурации
- Сохранение артефактов для последующих stages

#### Test Stage
**Назначение**: Запуск тестов

**Конфигурация**:
```yaml
stages:
  - name: "test"
    timeout_ms: 600000
    commands:
      - "npm test"
      - "npm run lint"
    coverage:
      enabled: true
      format: "lcov"
```

**Детали реализации**:
- Выполняется в workspace directory
- Timeout из конфигурации
- Опциональный сбор coverage reports

#### Deploy Stage
**Назначение**: Деплой артефактов

**Конфигурация**:
```yaml
stages:
  - name: "deploy"
    timeout_ms: 900000
    condition: "branch == 'main'"
    environment: "production"
    commands:
      - "npm run deploy"
```

**Детали реализации**:
- Выполняется только если condition выполняется
- Timeout из конфигурации
- Опциональное определение target environment

## Интеграция с WORKFLOW.md

### Конфигурация CI в WORKFLOW.md
```yaml
ci:
  enabled: true
  provider: "github-actions"

  triggers:
    on_issue_change: true
    on_pr_create: true
    on_pr_update: true
    manual: true

  pipeline:
    timeout_ms: 1800000  # 30 minutes total
    on_failure: "retry"  # or "stop", "continue"
    max_retries: 2

    stages:
      - name: "build"
        timeout_ms: 300000
        commands:
          - "npm install"
          - "npm run build"
        artifacts:
          - path: "dist/"
        on_failure: "stop"

      - name: "test"
        timeout_ms: 600000
        commands:
          - "npm test"
        on_failure: "retry"

      - name: "deploy"
        timeout_ms: 900000
        condition: "branch == 'main'"
        commands:
          - "npm run deploy"
        environment: "production"
        on_failure: "stop"
```

### Переменные окружения в CI
Доступные переменные для CI commands:
- `SYMPHONY_ISSUE_ID` - ID issue
- `SYMPHONY_ISSUE_IDENTIFIER` - Issue identifier
- `SYMPHONY_BRANCH` - Branch name
- `SYMPHONY_WORKSPACE` - Workspace path
- `SYMPHONY_STAGE` - Current stage name
- `SYMPHONY_CI_RUN_ID` - CI run ID

## Отчетность об артефактах

### Артефакты CI
Типы артефактов:
- Build artifacts (compiled code, bundles)
- Test reports (junit, lcov, etc.)
- Coverage reports
- Logs
- Screenshots (для UI тестов)

### Структура отчета
```json
{
  "ci_run_id": "gh-12345",
  "issue_identifier": "PROJ-123",
  "branch": "feature/test",
  "status": "success",
  "stages": [
    {
      "name": "build",
      "status": "success",
      "duration_ms": 120000,
      "artifacts": [
        {
          "type": "build",
          "path": "dist/",
          "url": "https://artifacts.example.com/dist/"
        }
      ]
    },
    {
      "name": "test",
      "status": "success",
      "duration_ms": 300000,
      "artifacts": [
        {
          "type": "test_report",
          "path": "test-results/",
          "url": "https://artifacts.example.com/test-results/"
        },
        {
          "type": "coverage",
          "path": "coverage/",
          "url": "https://artifacts.example.com/coverage/"
        }
      ]
    }
  ],
  "total_duration_ms": 420000
}
```

### Отправка отчетов
- Отправка отчета в issue tracker (через coding agent tools)
- Публикация артефактов в artifact storage
- Опциональное уведомление через внешние системы (Slack, email, etc.)

## Мониторинг CI запусков

### Статус CI run
Возможные статусы:
- `pending` - ожидание запуска
- `running` - выполняется
- `success` - успешно завершен
- `failed` - завершился с ошибкой
- `cancelled` - отменен
- `timeout` - превышен timeout

### Операции мониторинга
- `get_ci_run_status(ci_run_id)` - получить статус запуска
- `list_ci_runs(issue_identifier)` - список запусков для issue
- `cancel_ci_run(ci_run_id)` - отменить запуск

## Обработка ошибок

### Категории ошибок

| Категория | Описание | Обработка |
|-----------|-----------|-----------|
| `ci_provider_error` | Ошибка CI provider | Retry или fatal |
| `ci_timeout` | Превышен timeout | Cancel run |
| `ci_auth_error` | Ошибка аутентификации | Fatal error |
| `ci_invalid_config` | Неверная конфигурация | Fatal error |
| `ci_stage_failure` | Ошибка в stage | Обработка по on_failure policy |
| `ci_workspace_error` | Ошибка workspace | Fatal error |

### Retry политика
- Provider errors: retry с exponential backoff
- Stage failures: retry или stop по on_failure policy
- Auth errors: немедленный failure
- Timeout errors: немедленный cancel

## Конфигурация для различных CI providers

### GitHub Actions
```yaml
ci:
  provider: "github-actions"
  config:
    repo: "owner/repo"
    workflow_file: ".github/workflows/symphony.yml"
```

### GitLab CI
```yaml
ci:
  provider: "gitlab-ci"
  config:
    project_id: "123"
    gitlab_url: "https://gitlab.com"
```

### Jenkins
```yaml
ci:
  provider: "jenkins"
  config:
    url: "https://jenkins.example.com"
    job_name: "symphony-job"
    credentials_id: "symphony-token"
```

## TODO

### Определить CI provider specifics
- **Задача**: Определить детальную конфигурацию для каждого поддерживаемого CI provider
- **Детали**:
  - GitHub Actions: webhook configuration, workflow triggers, artifact storage
  - GitLab CI: pipeline triggers, artifact registry, environment deployment
  - Jenkins: job configuration, build triggers, artifact archiving
  - CircleCI: workflow configuration, API integration, orb usage
  - Azure DevOps: pipeline configuration, artifact publishing, environment management

### Дополнительные задачи
- [ ] Определить формат CI logs для streaming в Orchestrator
- [ ] Реализовать поддержку parallel stages
- [ ] Добавить поддержку matrix builds
- [ ] Определить стратегию для cache между runs
- [ ] Реализовать unit tests для CI adapter
- [ ] Добавить интеграционные тесты с real CI providers
- [ ] Определить ограничения на concurrent CI runs
- [ ] Поддержать conditional execution stages
- [ ] Добавить поддержку manual approval gates
- [ ] Реализовать rollback mechanism для deploy stage
- [ ] Определить политику cleanup для старых артефактов

## Ссылки

- SPEC.md: Symphony Service Specification
- SPEC.md Section 5.3: Front Matter Schema
- SPEC.md Section 8.2: Candidate Selection Rules
- GitHub Actions Documentation: https://docs.github.com/en/actions
- GitLab CI Documentation: https://docs.gitlab.com/ee/ci/
- Jenkins Documentation: https://www.jenkins.io/doc/
