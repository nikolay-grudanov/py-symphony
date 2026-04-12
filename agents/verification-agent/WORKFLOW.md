# Verification Agent - Рабочий процесс

## Обзор процесса

Verification Agent следует workflow: понимание требований → обзор артефактов → валидация против спецификаций → отчет о проблемах.

## Шаг 1: Понимание требований

### Изучение ADR

Изучить Architecture Decision Record:

```
## Анализ ADR: [Номер и название]

**Статус**: Accepted
**Approved by**: [архитектор]

**Требования**:
- [ ] Требование 1: [описание]
- [ ] Требование 2: [описание]
- [ ] Требование 3: [описание]

**Решение**:
- [ ] Архитектурный подход: [описание]
- [ ] Паттерны: [список]
- [ ] Технологии: [список]

**Последствия**:
- Положительные: [список]
- Отрицательные: [список]

**Соответствие SPEC.md**:
- Разделы: [ссылки]
```

### Изучение SPEC.md

Изучить соответствующие разделы SPEC.md:

- Requirements из SPEC.md
- Constraints из SPEC.md
- Non-functional requirements из SPEC.md

### Изучение QA Gate критериев

Изучить QA Gate критерии от build-orchestrator:

- Что нужно проверить
- Criteria для acceptance
- Expected results

## Шаг 2: Обзор артефактов

### Обзор кода

Изучить реализованный код:

```
## Обзор кода: [ADR номер]

**Файлы**:
- [ ] file1.py: [описание]
- [ ] file2.py: [описание]

**Модули**:
- [ ] module1: [функциональность]
- [ ] module2: [функциональность]

**Classes**:
- [ ] Class1: [описание]
- [ ] Class2: [описание]

**Functions**:
- [ ] function1: [описание]
- [ ] function2: [описание]
```

### Обзор тестов

Изучить тесты:

```
## Обзор тестов: [ADR номер]

**Unit tests**:
- [ ] test_module1.py: [количество tests]
- [ ] test_module2.py: [количество tests]

**Integration tests**:
- [ ] test_integration.py: [количество scenarios]

**Coverage**:
- Line coverage: [X%]
- Branch coverage: [X%]
- Function coverage: [X%]
```

### Обзор документации

Изучить документацию:

```
## Обзор документации: [ADR номер]

**Docstrings**:
- [ ] Все public functions: [да/нет]
- [ ] Все public classes: [да/нет]
- [ ] Quality: [оценка]

**README**:
- [ ] Обновлен: [да/нет]
- [ ] Installation instructions: [да/нет]
- [ ] Usage examples: [да/нет]

**API документация**:
- [ ] Создана: [да/нет]
- [ ] Complete: [да/нет]
```

## Шаг 3: Валидация против спецификаций

### Валидация требований

Проверить что все требования из ADR покрыты:

```
## Валидация требований: ADR-[номер]

| Requirement | Source | Status | Evidence | Notes |
|-------------|--------|--------|----------|-------|
| Req 1 | ADR-[номер] section X.Y | ✅/❌ | [ссылка на код] | [notes] |
| Req 2 | ADR-[номер] section X.Z | ✅/❌ | [ссылка на код] | [notes] |
| Req 3 | SPEC.md section A.B | ✅/❌ | [ссылка на код] | [notes] |

**Summary**: X из Y требований покрыто (Z%)
```

### Валидация SPEC.md compliance

Проверить соответствие SPEC.md:

```
## Валидация SPEC.md: ADR-[номер]

| Section | Requirement | Status | Evidence | Notes |
|---------|-------------|--------|----------|-------|
| Section X.Y | Requirement 1 | ✅/❌ | [ссылка] | [notes] |
| Section X.Z | Requirement 2 | ✅/❌ | [ссылка] | [notes] |

**Summary**: X из Y требований SPEC.md покрыто (Z%)
```

### Валидация архитектуры

Проверить что архитектура реализована корректно:

- [ ] Architectural patterns применены
- [ ] Design patterns соблюдены
- [ ] Layers separation (API, Business Logic, Data Access)
- [ ] Dependencies правильные
- [ ] Coupling минимален

### Валидация контрактов

Проверить что контракты соблюдены (если применимо):

- [ ] API контракты соблюдены
- [ ] Data contracts соблюдены
- [ ] Integration contracts соблюдены
- [ ] Interface contracts соблюдены

## Шаг 4: Валидация качества

### Валидация code quality

Проверить code quality:

```
## Валидация code quality: ADR-[номер]

**Code standards**:
- [ ] PEP 8 compliance: [да/нет]
- [ ] Type hints: [все/некоторые/нет]
- [ ] Docstrings: [полные/частичные/нет]

**Clean code**:
- [ ] Имена описательные: [да/нет]
- [ ] Functions короткие: [да/нет]
- [ ] Нет дублирования: [да/нет]
- [ ] SRP соблюден: [да/нет]

**Error handling**:
- [ ] Errors обработаны: [да/нет]
- [ ] Custom exceptions: [да/нет]
- [ ] Error messages информативные: [да/нет]
- [ ] Errors логируются: [да/нет]

**Security**:
- [ ] Input validation: [да/нет]
- [ ] SQL injection prevention: [да/нет]
- [ ] XSS prevention: [да/нет если применимо]
- [ ] Password hashing: [да/нет если применимо]
```

### Валидация test coverage

Проверить test coverage:

```
## Валидация test coverage: ADR-[номер]

**Coverage**:
- Line coverage: [X%] (target: Y%)
- Branch coverage: [X%]
- Function coverage: [X%]

**Test types**:
- [ ] Unit tests: [да/нет]
- [ ] Integration tests: [да/нет если применимо]
- [ ] Edge cases протестированы: [да/нет]
- [ ] Error paths протестированы: [да/нет]

**Test quality**:
- [ ] Tests ясные: [да/нет]
- [ ] Tests independent: [да/нет]
- [ ] Mocking appropriate: [да/нет]
```

### Валидация документации

Проверить документацию:

```
## Валидация документации: ADR-[номер]

**Docstrings**:
- [ ] Все public functions: [да/нет]
- [ ] Все public classes: [да/нет]
- [ ] Args документация: [да/нет]
- [ ] Returns документация: [да/нет]
- [ ] Raises документация: [да/нет]
- [ ] Examples: [да/нет если применимо]

**README**:
- [ ] Обновлен: [да/нет]
- [ ] Installation instructions: [да/нет]
- [ ] Usage examples: [да/нет]
- [ ] API documentation links: [да/нет]

**API документация**:
- [ ] Создана: [да/нет если применимо]
- [ ] Complete: [да/нет]
- [ ] Examples для всех методов: [да/нет]
```

## Шаг 5: Идентификация issues

### Классификация findings

Классифицировать найденные issues по severity:

**Critical**:
- Security vulnerability
- Отсутствие критической функциональности
- Non-compliance с SPEC.md

**High**:
- Существенная функциональность отсутствует
- Code quality существенно нарушен
- Test coverage < target

**Medium**:
- Незначительная функциональность отсутствует
- Code quality частично нарушен
- Документация неполная

**Low**:
- Cosmetic issues
- Minor improvements
- Optional documentation

### Документирование findings

Документировать все findings:

```
## Findings: ADR-[номер]

### Critical

1. **[Issue title]**
   - **Location**: [файл:строка]
   - **Requirement**: ADR-[номер] section X.Y или SPEC.md section X.Y
   - **Description**: [детальное описание]
   - **Impact**: [как влияет на систему]
   - **Suggestion**: [предложение по исправлению]

### High

1. **[Issue title]**
   - **Location**: [файл:строка]
   - **Requirement**: [ссылка]
   - **Description**: [детальное описание]
   - **Impact**: [как влияет на систему]
   - **Suggestion**: [предложение по исправлению]

### Medium

1. **[Issue title]**
   - **Location**: [файл:строка]
   - **Description**: [детальное описание]
   - **Impact**: [как влияет на систему]
   - **Suggestion**: [предложение по исправлению]

### Low

1. **[Issue title]**
   - **Location**: [файл:строка]
   - **Description**: [детальное описание]
   - **Suggestion**: [предложение по исправлению]
```

## Шаг 6: Создание отчета

### Summary отчета

Создать summary отчет:

```
## Summary отчет: ADR-[номер]

**Общий статус**: [Approval/Rejection]

**Валидация**:
- Requirements coverage: [X/Y] (Z%)
- SPEC.md compliance: [X/Y] (Z%)
- Code quality: [X/Y] (Z%)
- Test coverage: [X%] (target: Y%)
- Documentation: [X/Y] (Z%)
- Security: [X/Y] (Z%)

**Findings**:
- Critical: [X]
- High: [Y]
- Medium: [Z]
- Low: [W]

**Решение**: [Approval/Rejection]
**Rationale**: [обоснование]
```

### Детальный отчет

Создать детальный отчет (см. шаблон в SOUL.md):

- Overview
- Артефакты для верификации
- Валидация (все sections)
- Findings (с классификацией)
- Summary
- Recommendation
- Appendix с детальными проверками

## Шаг 7: Approval или Rejection

### Approval критерии

Approval если:
- [ ] Все critical требования покрыты
- [ ] Все high критерии выполнены
- [ ] Test coverage >= target
- [ ] Security проверен и безопасен
- [ ] Нет critical или high issues

### Rejection критерии

Rejection если:
- [ ] Critical issues найдены
- [ ] High issues найдены
- [ ] Test coverage < target
- [ ] Security vulnerability найдена
- [ ] Requirements не покрыты

### Approval

```
✅ Approval: ADR-[номер]

**Артефакты**: [список]

**Валидация**:
- Requirements coverage: [X/Y] (Z%) ✅
- SPEC.md compliance: [X/Y] (Z%) ✅
- Code quality: [X/Y] (Z%) ✅
- Test coverage: [X%] (target: Y%) ✅
- Documentation: [X/Y] (Z%) ✅
- Security: [X/Y] (Z%) ✅

**Findings**:
- Critical: 0
- High: 0
- Medium: [X]
- Low: [Y]

**Rationale**:
- Все critical критерии выполнены
- Все high критерии выполнены
- Несущественные issues могут быть отложены

**Recommendation**: Approve для merge

**Next**: Передача build-orchestrator
```

### Rejection

```
❌ Rejection: ADR-[номер]

**Артефакты**: [список]

**Валидация**:
- Requirements coverage: [X/Y] (Z%) ❌
- SPEC.md compliance: [X/Y] (Z%) ✅
- Code quality: [X/Y] (Z%) ❌
- Test coverage: [X%] (target: Y%) ❌
- Documentation: [X/Y] (Z%) ❌
- Security: [X/Y] (Z%) ✅

**Findings**:
- Critical: [X]
- High: [Y]
- Medium: [Z]
- Low: [W]

**Critical issues** (must fix):
1. [Issue 1]: [описание]

**High issues** (must fix):
1. [Issue 1]: [описание]
2. [Issue 2]: [описание]

**Rationale**:
- Critical issues найдены
- High issues найдены
- Требуется исправление перед merge

**Recommendation**: Reject до исправления critical и high issues

**Дедлайн**: [дата]
**Next**: Feedback implementation-engineer
```

## Завершение

### Final checklist

Перед завершением верификации:

- [ ] Все requirements проверены
- [ ] SPEC.md compliance проверен
- [ ] Code quality проверен
- [ ] Test coverage проверен
- [ ] Documentation проверена
- [ ] Security проверен
- [ ] Все findings документированы
- [ ] Severity классифицирована
- [ ] Отчет создан
- [ ] Approval или rejection decision сделан

### Подготовка к передаче

Подготовить передачу:

**Approval**:
```
## Handoff: Approval ADR-[номер]

**От**: verification-agent
**Кому**: build-orchestrator

**ADR**: ADR-[номер]
**Артефакты**: [список]

**Валидация summary**: [summary]
**Findings**: [summary]

**Решение**: Approval

**Next**: Merge
```

**Rejection**:
```
## Handoff: Rejection ADR-[номер]

**От**: verification-agent
**Кому**: build-orchestrator

**ADR**: ADR-[номер]
**Артефакты**: [список]

**Валидация summary**: [summary]
**Findings**: [summary]

**Critical issues**: [список]
**High issues**: [список]

**Решение**: Rejection

**Next**: Feedback implementation-engineer
**Дедлайн**: [дата]
```
