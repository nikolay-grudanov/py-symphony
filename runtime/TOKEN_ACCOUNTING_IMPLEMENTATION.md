# Token Accounting Implementation

## Overview

Реализовано token accounting и rate limits aggregation в Python Orchestrator согласно SPEC.md Section 13.5.

## Изменения

### 1. RunningEntry Dataclass

Добавлены поля для отслеживания token usage:

```python
codex_input_tokens: int = 0
codex_output_tokens: int = 0
codex_total_tokens: int = 0
codex_last_reported_input_tokens: int = 0
codex_last_reported_output_tokens: int = 0
codex_last_reported_total_tokens: int = 0
```

### 2. Методы Orchestrator

#### `_extract_token_usage(update: dict) -> dict`

Извлекает token usage из event payload. Поддерживает различные форматы:
- `usage` field
- `payload` field
- `params.usage` и `params.tokenUsage`
- Вложенные пути для absolute totals (`total_token_usage`)

#### `_extract_rate_limits(update: dict) -> Optional[dict]`

Извлекает rate limits из event payload. Ищет поля:
- `rate_limits`
- `rateLimits`

Валидирует структуру: должен содержать `limit_id`/`limit_name` и buckets (primary/secondary/credits).

#### `_compute_token_delta(running_entry, token_type, usage, reported_key) -> dict`

Вычисляет token delta относительно last reported значения. Используется для предотвращения double-counting.

#### `_extract_token_delta(running_entry, update) -> dict`

Интегрирует `_extract_token_usage` и `_compute_token_delta` для получения полного delta для input/output/total.

#### `_integrate_codex_update(running_entry, update) -> None`

Главный метод для обработки Codex agent update:
- Извлекает и применяет token delta
- Извлекает и сохраняет rate limits

#### `_apply_codex_token_delta(running_entry, token_delta) -> None`

Применяет token delta к:
- Индивидуальной running entry (session totals)
- Глобальным агрегатам в state (overall totals)

#### `_apply_codex_rate_limits(rate_limits) -> None`

Сохраняет последние rate limits в `state.rate_limits`.

### 3. Обновлен `_handle_agent_event()`

Теперь вызывает `_integrate_codex_update()` для обработки token accounting и rate limits.

### 4. Обновлен `get_state_snapshot()`

Добавлены token поля в running entries:
- `codex_input_tokens`
- `codex_output_tokens`
- `codex_total_tokens`

## Тесты

Создан комплексный набор тестов в `tests/test_token_accounting.py`:

1. **Тесты вспомогательных методов:**
   - `test_integer_like_extracts_integers`
   - `test_integer_token_map_identifies_token_maps`
   - `test_get_token_usage_extracts_common_fields`
   - `test_absolute_token_usage_from_payload`

2. **Тесты delta computation:**
   - `test_compute_token_delta_uses_last_reported`
   - `test_compute_token_delta_handles_no_increase`

3. **Тесты извлечения:**
   - `test_extract_token_usage_from_various_locations`
   - `test_extract_rate_limits_identifies_rate_limit_maps`
   - `test_is_rate_limits_map_validates_structure`

4. **Тесты интеграции:**
   - `test_extract_token_delta_from_update`
   - `test_apply_codex_token_delta_updates_entry_and_state`
   - `test_apply_codex_rate_limits_stores_in_state`
   - `test_integrate_codex_update_full_integration`

5. **Тесты business logic:**
   - `test_token_accounting_avoids_double_counting`
   - `test_multiple_sessions_accumulate_tokens_correctly`
   - `test_state_snapshot_includes_token_information`

Всего: **16 тестов** - все проходят ✅

## Ключевые особенности реализации

### Double-counting prevention

Delta вычисляется относительно `codex_last_reported_*` полей:
```
delta = next_total - prev_reported
```

Если `next_total == prev_reported`, delta = 0 (нет double-counting).

### Множественные форматы payload

Поддержка различных форматов token usage:
- `input_tokens` / `prompt_tokens`
- `output_tokens` / `completion_tokens`
- `total_tokens`
- Snake_case и camelCase варианты
- Версии в верхнем регистре

### Absolute totals preference

При наличии multiple источников preference:
1. Absolute totals (`total_token_usage`, `tokenUsage/total`)
2. Turn/completed usage (`method: "turn/completed"`)

### Rate limits validation

Проверяет что rate limits payload содержит:
- Identifier: `limit_id`, `limitId`, `limit_name`, `limitName`
- Buckets: `primary`, `secondary`, `credits`

## Соответствие SPEC.md Section 13.5

✅ **Token accounting rules:**
- Предпочитать absolute thread totals
- Игнорировать delta-style payloads
- Extract leniently из common field names
- Track deltas relative to last reported (avoid double-counting)
- Accumulate aggregates in orchestrator state

✅ **Runtime accounting:**
- Runtime как live aggregate at snapshot time
- Accumulate counter для ended sessions (TODO: add runtime seconds)

✅ **Rate-limit tracking:**
- Track latest rate-limit payload
- Хранить в `state.rate_limits`

## Результаты

- **Все тесты проходят:** 55/55 (существующие + 16 новых)
- **Покрытие кода:** Все новые методы протестированы
- **Интеграция:** Работает с `_handle_agent_event()`
- **Backward compatibility:** Существующая функциональность не нарушена
