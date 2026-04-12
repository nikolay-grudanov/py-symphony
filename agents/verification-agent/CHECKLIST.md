# Verification Agent - Чеклист завершения

## Обзор

Чеклист определяет критерии завершения при верификации артефактов. Verification Agent не может считать верификацию завершенной, пока все пункты не выполнены.

## Чеклист для верификации кода

### Requirements Coverage

- [ ] **Все требования из ADR покрыты**
  - [ ] Functional requirements покрыты
  - [ ] Non-functional требования покрыты
  - [ ] Missing функциональность идентифицирована
  - [ ] Cross-reference с реализацией выполнен

- [ ] **Соответствие SPEC.md**
  - [ ] Все требования SPEC.md проверены
  - [ ] Constraints из SPEC.md соблюдены
  - [ ] Non-functional requirements из SPEC.md проверены

### Code Quality

- [ ] **Code standards compliance**
  - [ ] PEP 8 compliance проверен
  - [ ] Type hints проверены
  - [ ] Docstrings проверены
  - [ ] Naming conventions проверены

- [ ] **Code quality principles**
  - [ ] Clean code principles соблюдены
  - [ ] SRP (Single Responsibility Principle) соблюден
  - [ ] DRY (Don't Repeat Yourself) соблюден
  - [ ] Code organization проверена

- [ ] **Error handling**
  - [ ] Error handling реализован
  - [ ] Custom exceptions определены
  - [ ] Error messages информативные
  - [ ] Errors логируются с контекстом

- [ ] **Security**
  - [ ] Input validation реализован
  - [ ] SQL injection prevention проверен
  - [ ] XSS prevention проверен если применимо
  - [ ] Password handling проверен если применимо

### Test Coverage

- [ ] **Unit tests**
  - [ ] Все public methods протестированы
  - [ ] Edge cases протестированы
  - [ ] Error paths протестированы
  - [ ] Mocking appropriate

- [ ] **Integration tests**
  - [ ] Интеграции с внешними API протестированы
  - [ ] Database integration tests созданы
  - [ ] Test data setup/teardown проверен

- [ ] **Coverage metrics**
  - [ ] Line coverage >= target
  - [ ] Branch coverage >= target
  - [ ] Function coverage >= target
  - [ ] Uncovered code reviewed

- [ ] **Test quality**
  - [ ] Tests ясные и понятные
  - [ ] Tests independent
  - [ ] Test fixtures appropriate

### Documentation

- [ ] **Docstrings**
  - [ ] Все public functions имеют docstrings
  - [ ] Все public classes имеют docstrings
  - [ ] Args документация полная
  - [ ] Returns документация полная
  - [ ] Raises документация полная

- [ ] **README**
  - [ ] Обновлен если API изменился
  - [ ] Installation instructions ясные
  - [ ] Usage examples предоставлены
  - [ ] API documentation links включены

- [ ] **API documentation**
  - [ ] Создана если применимо
  - [ ] Complete
  - [ ] Examples для всех методов

## Чеклист для верификации контрактов

### Requirements Coverage

- [ ] **Все бизнес-требования покрыты**
  - [ ] Functional requirements покрыты
  - [ ] Edge cases рассмотрены
  - [ ] Error handling стратегия полная

- [ ] **Соответствие внешним спецификациям**
  - [ ] Контракт соответствует внешней API
  - [ ] Поля и типы соответствуют
  - [ ] Error codes определены

### Contract Quality

- [ ] **Спецификация полная**
  - [ ] OpenAPI/GraphQL schema полная
  - [ ] All endpoints/operations определены
  - [ ] Request/response formats описаны
  - [ ] Status codes определены

- [ ] **Error handling стратегия**
  - [ ] Error classification полная
  - [ ] Retry стратегия определена
  - [ ] Circuit breaker спроектирован
  - [ ] Fallback механизмы определены

- [ ] **Rate limiting**
  - [ ] Rate limits определены
  - [ ] Enforcement стратегия определена
  - [ ] Rate limit detection спроектирован

- [ ] **Authentication и Authorization**
  - [ ] Authentication метод определен
  - [ ] Authorization метод определен
  - [ ] Scopes/permissions определены

### Documentation

- [ ] **HOWTO guide**
  - [ ] Prerequisites документированы
  - [ ] Authentication flow описан
  - [ ] Usage examples предоставлены
  - [ ] Error handling guide создан

- [ ] **Примеры**
  - [ ] Happy path examples
  - [ ] Error handling examples
  - [ ] Edge case examples
  - [ ] Code examples

## Чеклист для создания отчета

### Report Structure

- [ ] **Overview section**
  - [ ] ADR номер и название
  - [ ] Дата верификации
  - [ ] Верификатор

- [ ] **Артефакты для верификации**
  - [ ] Код ссылки
  - [ ] Tests ссылки
  - [ ] Документация ссылки
  - [ ] ADR ссылка
  - [ ] SPEC.md ссылки

- [ ] **Валидация sections**
  - [ ] Requirements coverage
  - [ ] SPEC.md compliance
  - [ ] Code quality
  - [ ] Test coverage
  - [ ] Documentation
  - [ ] Security

- [ ] **Findings section**
  - [ ] Critical issues документированы
  - [ ] High issues документированы
  - [ ] Medium issues документированы
  - [ ] Low issues документированы
  - [ ] Severity классифицирована

- [ ] **Summary section**
  - [ ] Total findings по severity
  - [ ] Overall status по каждому aspect
  - [ ] Metrics для каждого aspect

- [ ] **Recommendation section**
  - [ ] Approval или rejection decision
  - [ ] Rationale для decision
  - [ ] Next steps

- [ ] **Appendix section**
  - [ ] Детальные проверки документированы
  - [ ] Evidence для всех findings

### Report Quality

- [ ] **Clear communication**
  - [ ] Описания лаконичные и ясные
  - [ ] Bullet points и tables использованы
  - [ ] Evidence для всех findings

- [ ] **Actionable recommendations**
  - [ ] Specific suggestions для каждого issue
  - [ ] Priority order для fixes
  - [ ] Examples где применимо

- [ ] **Professional tone**
  - [ ] Objective и fact-based
  - [ ] Constructive feedback
  - [ ] Respectful tone

## Итоговый чеклист завершения

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

## Чеклист для approval

Approval если:

- [ ] Все critical критерии выполнены
- [ ] Все high критерии выполнены
- [ ] Test coverage >= target
- [ ] Security проверен и безопасен
- [ ] Нет critical или high issues
- [ ] Medium и low issues могут быть отложены

## Чеклист для rejection

Rejection если:

- [ ] Critical issues найдены
- [ ] High issues найдены
- [ ] Test coverage < target
- [ ] Security vulnerability найдена
- [ ] Requirements не покрыты
- [ ] Дедлайн установлен

## Post-handoff checklist

После передачи build-orchestrator:

- [ ] Отчет передан
- [ ] Decision (approval/rejection) communicated
- [ ] Findings переданы
- [ ] Feedback implementation-engineer если rejection
- [ ] Дедлайн установлен если rejection
