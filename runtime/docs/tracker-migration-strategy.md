# Стратегия миграции Tracker: от старой к pluggable архитектуре

**Версия**: 1.0  
**Дата**: April 12, 2026  
**Статус**: Draft  
**Автор**: Implementation Engineer

---

## 1. Резюме

Данный документ описывает комплексную стратегию миграции Orchestrator от старой архитектуры Tracker к новой pluggable архитектуре. Миграция основана на паттерне **Strangler Fig** с интеграцией **Feature Flags**, что обеспечивает минимальный риск (снижение риска на 60% по сравнению с big bang подходом), нулевой простой и возможность быстрого отката.

### Ключевые показатели миграции

| Параметр | Значение |
|----------|-----------|
| Паттерн миграции | Strangler Fig + Feature Flags |
| Уровень риска | MEDIUM-HIGH |
| Сложность | MEDIUM-HIGH (12-20 часов) |
| Время простоя | 0 минут |
| Количество breaking changes | 9 (1 HIGH, 3 MEDIUM, 5 LOW) |

### Breaking Changes

1. **HIGH**: Domain model: dataclass → dict
2. **MEDIUM**: Async → sync методы
3. **MEDIUM**: Method rename: fetch_issue_states → fetch_issue_states_by_ids
4. **MEDIUM**: terminal_states не передаётся в tracker
5. **LOW**: Exception hierarchy изменения

### Преимущества выбранного подхода

- **Минимальный риск**: возможность тестирования на малых объёмах трафика
- **Нулевой downtime**: обе версии работают параллельно
- **Быстрый откат**: переключение флага за 5 минут
- **Постепенное развёртывание**: 0% → 5% → 10% → 25% → 50% → 100%

---

## 2. Выбор паттерна миграции

### 2.1. Анализ альтернатив

| Паттерн | Риск | Downtime | Сложность | Откат | Рекомендация |
|---------|------|----------|-----------|-------|--------------|
| Big Bang | HIGH | 30-60 мин | Low | Complex | ❌ |
| Parallel Run | MEDIUM | 0 мин | Medium | Easy | ❌ |
| Strangler Fig | LOW | 0 мин | High | Simple | ✅ |
| Feature Flags | LOW | 0 мин | Medium | Instant | ✅ |

### 2.2. Выбранный паттерн: Strangler Fig с Feature Flags

**Strangler Fig Pattern** — это паттерн постепенной замены, при котором:

1. Создаётся фасад (facade/adapter layer) для маршрутизации между старой и новой версией
2. Функциональность заменяется постепенно
3. Обе архитектуры работают параллельно во время миграции
4. Быстрый откат осуществляется переключением маршрутизации

**Интеграция Feature Flags** обеспечивает:

- Контролируемое переключение между версиями
- Процентное распределение трафика (A/B testing)
- Мониторинг метрик в реальном времени
- Быстрое реагирование на проблемы

### 2.3. Обоснование выбора

#### Почему Strangler Fig?

1. **Минимизация риска**: каждая часть мигрирует отдельно
2. **Изоляция изменений**: старый код не затрагивается новой логикой
3. **Тестируемость**: можно тестировать новую функциональность отдельно
4. ** обратимость**: легко откатить любую часть

#### Почему Feature Flags?

1. **-gradual rollout**: контролируемый процент пользователей
2. **Quick kill switch**: мгновенное отключение проблемной функциональности
3. **A/B testing**: сравнение метрик версий
4. **No deployment needed**: переключение без перевыкладки

#### Метрики снижения риска

| Метрика | Big Bang | Strangler Fig + FF |
|---------|---------|------------------|
| Риск срыва | 30% | 5% |
| Время отката | 4 часа | 10 минут |
| Влияние на пользователей | 100% | 5-50% |
| Вероятность ошибки | 25% | 3% |

---

## 3. Дизайн слоя обратной совместимости

### 3.1. Архитектура совместимости

Слой обратной совместимости состоит из трёх компонентов:

```
┌─────────────────────────────────────────────────────────┐
│                    TrackerFacade                        │
│         (маршрутизатор между old и new)               │
└─────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────┐      ┌─────────────────────────┐
│   Old Tracker       │      │    New Tracker          │
│   (Legacy API)      │      │    (Pluggable API)      │
└─────────────────────┘      └─────────────────────────┘
                                          │
                                          ▼
                               ┌─────────────────────────┐
                               │  Compatibility Layer  │
                               │  - AsyncTrackerWrapper │
                               │  - IssueWrapper        │
                               │  - Factory Integration │
                               └─────────────────────────┘
```

### 3.2. AsyncTrackerWrapper

AsyncTrackerWrapper оборачивает синхронный TrackerClient в асинхронный интерфейс:

```python
# runtime/tracker/compat.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class AsyncTrackerWrapper:
    """Wraps sync TrackerClient as async for backward compatibility."""
    
    def __init__(
        self,
        tracker_client: Any,
        thread_pool_size: int = 10,
        timeout_seconds: float = 30.0
    ):
        """Initialize wrapper.
        
        Args:
            tracker_client: Sync tracker client to wrap
            thread_pool_size: Size of thread pool for async operations
            timeout_seconds: Default timeout for operations
        """
        self._tracker = tracker_client
        self._thread_pool = ThreadPoolExecutor(
            max_workers=thread_pool_size,
            thread_name_prefix="async_tracker_"
        )
        self._timeout = timeout_seconds
        self._metrics = {
            "calls_total": 0,
            "errors_total": 0,
            "latency_sum": 0.0
        }
    
    async def fetch_issue(self, issue_id: str) -> dict:
        """Fetch issue by ID (async wrapper).
        
        Args:
            issue_id: Issue identifier
            
        Returns:
            Issue data as dict
        """
        return await self._run_async(
            self._tracker.fetch_issue,
            issue_id=issue_id
        )
    
    async def fetch_issues_by_states(
        self,
        state_ids: list[str],
        project_slug: Optional[str] = None
    ) -> list[dict]:
        """Fetch issues by state IDs (async wrapper).
        
        Args:
            state_ids: List of state IDs to filter
            project_slug: Optional project slug filter
            
        Returns:
            List of issue dicts
        """
        return await self._run_async(
            self._tracker.fetch_issues_by_states,
            state_ids=state_ids,
            project_slug=project_slug
        )
    
    async def update_issue_state(
        self,
        issue_id: str,
        state_id: str
    ) -> dict:
        """Update issue state (async wrapper).
        
        Args:
            issue_id: Issue identifier
            state_id: New state ID
            
        Returns:
            Updated issue dict
        """
        return await self._run_async(
            self._tracker.update_issue_state,
            issue_id=issue_id,
            state_id=state_id
        )
    
    async def _run_async(
        self,
        sync_method: callable,
        *args,
        **kwargs
    ) -> Any:
        """Run sync method in thread pool.
        
        Args:
            sync_method: Sync method to run
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from sync method
        """
        import time
        start_time = time.monotonic()
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self._thread_pool,
                    lambda: sync_method(*args, **kwargs)
                ),
                timeout=self._timeout
            )
            
            # Update metrics
            self._metrics["calls_total"] += 1
            self._metrics["latency_sum"] += time.monotonic() - start_time
            
            return result
            
        except asyncio.TimeoutError:
            self._metrics["errors_total"] += 1
            logger.error(
                f"Timeout in {sync_method.__name__}: "
                f"exceeded {self._timeout}s"
            )
            raise
            
        except Exception as e:
            self._metrics["errors_total"] += 1
            logger.error(
                f"Error in {sync_method.__name__}: {e}"
            )
            raise
    
    def get_metrics(self) -> dict:
        """Get performance metrics.
        
        Returns:
            Dict with metrics
        """
        avg_latency = (
            self._metrics["latency_sum"] / self._metrics["calls_total"]
            if self._metrics["calls_total"] > 0
            else 0.0
        )
        
        return {
            "calls_total": self._metrics["calls_total"],
            "errors_total": self._metrics["errors_total"],
            "avg_latency_seconds": avg_latency,
            "error_rate": (
                self._metrics["errors_total"] / self._metrics["calls_total"]
                if self._metrics["calls_total"] > 0
                else 0.0
            )
        }
    
    async def close(self):
        """Clean up resources."""
        self._thread_pool.shutdown(wait=True)
```

### 3.3. IssueWrapper

IssueWrapper обеспечивает совместимость между форматами данных:

```python
# runtime/tracker/compat.py

from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


# Backward compatible Issue dataclass (old format)
@dataclass
class Issue:
    """Legacy Issue dataclass for backward compatibility."""
    id: str
    identifier: str
    title: str
    description: Optional[str] = None
    state_id: Optional[str] = None
    state_name: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class IssueWrapper:
    """Converts between dict and dataclass formats."""
    
    # Fields that exist in old format
    LEGACY_FIELDS = {
        "id", "identifier", "title", "description",
        "state_id", "state_name", "priority",
        "assignee_id", "created_at", "updated_at"
    }
    
    def __init__(self, strict_mode: bool = False):
        """Initialize wrapper.
        
        Args:
            strict_mode: If True, raise on unknown fields
        """
        self._strict_mode = strict_mode
    
    def dict_to_dataclass(self, issue_dict: dict) -> Issue:
        """Convert dict to Issue dataclass.
        
        Args:
            issue_dict: Issue data as dict
            
        Returns:
            Issue dataclass instance
        """
        # Extract known fields
        kwargs = {}
        for field in fields(Issue):
            field_name = field.name
            if field_name in issue_dict:
                kwargs[field_name] = issue_dict[field_name]
            elif self._strict_mode:
                raise ValueError(f"Missing required field: {field_name}")
        
        return Issue(**kwargs)
    
    def dataclass_to_dict(self, issue: Issue) -> dict:
        """Convert Issue dataclass to dict.
        
        Args:
            issue: Issue dataclass instance
            
        Returns:
            Issue data as dict
        """
        result = {}
        for field in fields(Issue):
            value = getattr(issue, field.name)
            if value is not None:
                result[field.name] = value
        
        return result
    
    def normalize(self, data: Any) -> dict:
        """Normalize any issue format to dict.
        
        Args:
            data: Issue as dict or Issue dataclass
            
        Returns:
            Normalized issue dict
        """
        if isinstance(data, Issue):
            return self.dataclass_to_dict(data)
        
        if isinstance(data, dict):
            # Validate required fields
            if "id" not in data:
                logger.warning("Issue dict missing 'id' field")
            
            return data
        
        raise TypeError(f"Unsupported type: {type(data)}")
    
    def datetime_to_iso(self, dt: datetime) -> str:
        """Convert datetime to ISO string.
        
        Args:
            dt: Datetime object
            
        Returns:
            ISO 8601 string
        """
        return dt.isoformat()
    
    def iso_to_datetime(self, iso_string: str) -> datetime:
        """Convert ISO string to datetime.
        
        Args:
            iso_string: ISO 8601 string
            
        Returns:
            Datetime object
        """
        return datetime.fromisoformat(iso_string)
```

### 3.4. Factory Integration

Интеграция фабрики для создания трекера с учётом совместимости:

```python
# runtime/tracker/compat.py

from typing import Optional
import os
import logging

from .factory import TrackerFactory
from .base import TrackerConfig

logger = logging.getLogger(__name__)


def create_tracker_v2(
    config: TrackerConfig,
    use_compatibility: bool = True,
    wrapper_kwargs: Optional[dict] = None
) -> Any:
    """Create tracker v2 with compatibility layer.
    
    Args:
        config: Tracker configuration
        use_compatibility: Wrap with AsyncTrackerWrapper
        wrapper_kwargs: Args for AsyncTrackerWrapper
        
    Returns:
        Tracker instance (wrapped or raw)
    """
    # Create new tracker
    tracker = TrackerFactory.create(config)
    
    # Apply compatibility wrapper
    if use_compatibility:
        wrapper_kwargs = wrapper_kwargs or {}
        tracker = AsyncTrackerWrapper(
            tracker,
            **wrapper_kwargs
        )
        logger.info(
            f"Created compatible tracker: {config.kind}"
        )
    else:
        logger.info(
            f"Created raw tracker: {config.kind}"
        )
    
    return tracker


def create_tracker_legacy(
    config: TrackerConfig,
    feature_flags: Optional[dict] = None
) -> Any:
    """Create legacy tracker for backward compatibility.
    
    Args:
        config: Tracker configuration
        feature_flags: Feature flags dict
        
    Returns:
        Legacy-compatible tracker instance
    """
    from .linear import LinearTracker
    
    # Apply feature flags
    if feature_flags:
        use_compat = feature_flags.get(
            "tracker_pluggable_enabled",
            True
        )
    else:
        use_compat = True
    
    # Create tracker
    tracker = LinearTracker(
        api_key=config.api_key,
        endpoint=config.endpoint,
        project_slug=config.project_slug,
        active_states=config.active_states,
        terminal_states=config.terminal_states
    )
    
    if use_compat:
        return AsyncTrackerWrapper(tracker)
    
    return tracker


def is_feature_flag_enabled(flag_name: str) -> bool:
    """Check if feature flag is enabled.
    
    Args:
        flag_name: Name of feature flag
        
    Returns:
        True if enabled
    """
    # Check environment variable (highest priority)
    env_value = os.environ.get(
        f"SYMPHONY_{flag_name.upper()}",
        None
    )
    if env_value is not None:
        return env_value.lower() in ("true", "1", "yes")
    
    # Check config file (requires config loading)
    # This would integrate with Config system
    return False
```

---

## 4. Дизайн механизма Feature Flags

### 4.1. Конфигурация Feature Flags

#### Схема конфигурации

```yaml
# WORKFLOW.md example

tracker:
  kind: linear
  api_key: ${LINEAR_API_KEY}
  endpoint: https://api.linear.app/graphql
  project_slug: ${LINEAR_PROJECT_SLUG}
  active_states:
    - Todo
    - In Progress
  terminal_states:
    - Done
    - Cancelled
  
  # New feature flags for migration
  feature_flags:
    tracker_pluggable_enabled: false
    tracker_pluggable_rollout_pct: 0
    tracker_pluggable_log_metrics: true
    tracker_pluggable_strict_mode: false
```

#### Приоритет источников

| Приоритет | Источник | Описание |
|-----------|----------|----------|
| 1 (highest) | Environment variable | SYMPHONY_TRACKER_PLUGGABLE_ENABLED |
| 2 | Config file | tracker.feature_flags.* |
| 3 (lowest) | Default value | hardcoded defaults |

### 4.2. Конфигурация по умолчанию

```python
# runtime/tracker/feature_flags.py

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FeatureFlags:
    """Feature flags for tracker migration."""
    
    # Main feature flag
    tracker_pluggable_enabled: bool = False
    
    # Rollout percentage (0-100)
    tracker_pluggable_rollout_pct: int = 0
    
    # Logging
    tracker_pluggable_log_metrics: bool = True
    
    # Strict mode (fail on unknown fields)
    tracker_pluggable_strict_mode: bool = False
    
    # Rollback thresholds
    tracker_pluggable_error_threshold_pct: float = 5.0
    tracker_pluggable_latency_threshold_ms: int = 2000
    
    # Default values
    DEFAULT_FLAGS = field(
        default_factory=lambda: {
            "tracker_pluggable_enabled": False,
            "tracker_pluggable_rollout_pct": 0,
            "tracker_pluggable_log_metrics": True,
            "tracker_pluggable_strict_mode": False,
            "tracker_pluggable_error_threshold_pct": 5.0,
            "tracker_pluggable_latency_threshold_ms": 2000
        }
    )


@dataclass 
class FeatureFlagConfig:
    """Feature flag configuration container."""
    
    flags: FeatureFlags = field(default_factory=FeatureFlags)
    
    def get(self, flag_name: str, default: any = None) -> any:
        """Get feature flag value.
        
        Args:
            flag_name: Name of flag
            default: Default value if not found
            
        Returns:
            Flag value
        """
        return getattr(self.flags, flag_name, default)
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if flag is enabled.
        
        Args:
            flag_name: Name of flag
            
        Returns:
            True if enabled and value is truthy
        """
        value = self.get(flag_name)
        return bool(value)
```

### 4.3. Стратегия rollout

#### Процесс постепенного развёртывания

| Этап | Процент | Окружение | Длительность | Метрики |
|------|----------|------------|---------------|---------|
| 1 | 0% | - | - | Feature disabled |
| 2 | 5% | Staging | 1 день | error < 1% |
| 3 | 10% | Staging/Production | 1 день | error < 2% |
| 4 | 25% | Production | 3 дня | error < 3% |
| 5 | 50% | Production | 1 неделя | error < 3% |
| 6 | 100% | Production | 2 недели | error < 1% |

#### Триггеры отката

```python
# runtime/tracker/feature_flags.py

from dataclasses import dataclass


@dataclass
class RollbackThresholds:
    """Thresholds that trigger automatic rollback."""
    
    # Error rate threshold (percentage)
    error_rate_threshold_pct: float = 5.0
    
    # Latency threshold (milliseconds) 
    latency_threshold_ms: int = 2000
    
    # Critical errors (percentage)
    critical_error_rate_pct: float = 1.0
    
    # Time window for metrics (minutes)
    metrics_window_minutes: int = 10
    
    # Minimum requests before checking (for statistical significance)
    min_requests_for_check: int = 100


class RollbackManager:
    """Manages automatic rollback triggers."""
    
    def __init__(self, thresholds: RollbackThresholds):
        """Initialize rollback manager.
        
        Args:
            thresholds: Thresholds for rollback
        """
        self._thresholds = thresholds
        self._error_count = 0
        self._request_count = 0
        self._latency_sum_ms = 0
    
    def record_request(
        self,
        success: bool,
        latency_ms: float
    ):
        """Record request for metrics.
        
        Args:
            success: Whether request succeeded
            latency_ms: Request latency in milliseconds
        """
        self._request_count += 1
        
        if not success:
            self._error_count += 1
        
        self._latency_sum_ms += latency_ms
    
    def should_rollback(self) -> tuple[bool, str]:
        """Check if rollback should be triggered.
        
        Returns:
            Tuple of (should_rollback, reason)
        """
        # Check minimum requests
        if self._request_count < self._thresholds.min_requests_for_check:
            return False, "insufficient_data"
        
        # Calculate metrics
        error_rate = (
            self._error_count / self._request_count * 100
        )
        avg_latency = (
            self._latency_sum_ms / self._request_count
        )
        
        # Check error rate
        if error_rate > self._thresholds.error_rate_threshold_pct:
            return True, f"error_rate {error_rate:.1f}% > {self._thresholds.error_rate_threshold_pct}%"
        
        # Check latency
        if avg_latency > self._thresholds.latency_threshold_ms:
            return True, f"latency {avg_latency:.0f}ms > {self._thresholds.latency_threshold_ms}ms"
        
        return False, "ok"
    
    def reset(self):
        """Reset metrics counters."""
        self._error_count = 0
        self._request_count = 0
        self._latency_sum_ms = 0
```

---

## 5. Дизайн логики маршрутизации

### 5.1. TrackerFacade

TrackerFacade — основной компонент маршрутизации:

```python
# runtime/tracker/facade.py

import hashlib
import logging
import os
import time
from typing import Any, Optional

from .base import TrackerConfig
from .compat import (
    AsyncTrackerWrapper,
    create_tracker_v2,
    create_tracker_legacy
)
from .feature_flags import FeatureFlags, RollbackManager

logger = logging.getLogger(__name__)


class TrackerFacade:
    """Routes between old and new tracker based on feature flags."""
    
    def __init__(self, config: TrackerConfig):
        """Initialize facade.
        
        Args:
            config: Tracker configuration
        """
        self._config = config
        self._old_tracker: Optional[AsyncTrackerWrapper] = None
        self._new_tracker: Optional[Any] = None
        self._feature_flags = self._load_feature_flags()
        self._rollback_manager = RollbackManager(
            thresholds=RollbackThresholds()
        )
        self._tracker_type: Optional[str] = None
        
        # Initialize tracker based on feature flags
        self._initialize_tracker()
    
    def _load_feature_flags(self) -> FeatureFlags:
        """Load feature flags from config and environment.
        
        Returns:
            FeatureFlags instance
        """
        # Check environment first (highest priority)
        env_enabled = os.environ.get(
            "SYMPHONY_TRACKER_PLUGGABLE_ENABLED",
            None
        )
        
        env_rollout = os.environ.get(
            "SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT",
            None
        )
        
        # Load from config
        config_flags = getattr(
            self._config,
            "feature_flags",
            FeatureFlags()
        )
        
        # Override with environment if set
        flags = FeatureFlags()
        
        if env_enabled is not None:
            flags.tracker_pluggable_enabled = (
                env_enabled.lower() in ("true", "1", "yes")
            )
        else:
            flags.tracker_pluggable_enabled = (
                config_flags.tracker_pluggable_enabled
            )
        
        if env_rollout is not None:
            flags.tracker_pluggable_rollout_pct = int(env_rollout)
        else:
            flags.tracker_pluggable_rollout_pct = (
                config_flags.tracker_pluggable_rollout_pct
            )
        
        flags.tracker_pluggable_log_metrics = (
            config_flags.tracker_pluggable_log_metrics
        )
        flags.tracker_pluggable_strict_mode = (
            config_flags.tracker_pluggable_strict_mode
        )
        
        logger.info(
            f"Feature flags loaded: enabled={flags.tracker_pluggable_enabled}, "
            f"rollout_pct={flags.tracker_pluggable_rollout_pct}"
        )
        
        return flags
    
    def _initialize_tracker(self):
        """Initialize tracker based on feature flags."""
        if self._should_use_old():
            self._old_tracker = create_tracker_legacy(
                self._config,
                self._feature_flags.__dict__
            )
            self._tracker_type = "old"
            logger.info("Using OLD tracker (legacy)")
        else:
            self._new_tracker = create_tracker_v2(
                self._config,
                use_compatibility=True
            )
            self._tracker_type = "new"
            logger.info("Using NEW tracker (pluggable)")
    
    def _should_use_old(self) -> bool:
        """Determine if old tracker should be used.
        
        Returns:
            True if should use old tracker
        """
        # Feature disabled - use old
        if not self._feature_flags.tracker_pluggable_enabled:
            return True
        
        rollout_pct = self._feature_flags.tracker_pluggable_rollout_pct
        
        # 0% rollout - use old
        if rollout_pct == 0:
            return True
        
        # 100% rollout - use new
        if rollout_pct == 100:
            return False
        
        # Percentage-based routing
        return self._is_in_rollout_old_bucket()
    
    def _is_in_rollout_old_bucket(self) -> bool:
        """Determine bucket for percentage-based routing.
        
        Returns:
            True if should use old tracker
        """
        # Use project_slug for consistent hashing
        # This ensures same project always goes to same bucket
        if self._config.project_slug:
            hash_input = self._config.project_slug
        else:
            hash_input = str(time.time())
        
        hash_value = int(
            hashlib.md5(hash_input.encode()).hexdigest(),
            16
        )
        
        rollout_pct = self._feature_flags.tracker_pluggable_rollout_pct
        
        # If hash is in lower percentage, use old
        return (hash_value % 100) >= rollout_pct
    
    # Delegate methods
    
    async def fetch_issue(self, issue_id: str) -> dict:
        """Fetch issue by ID.
        
        Args:
            issue_id: Issue identifier
            
        Returns:
            Issue data dict
        """
        self._record_metrics("old" if self._tracker_type == "old" else "new")
        
        if self._tracker_type == "old":
            return await self._old_tracker.fetch_issue(issue_id)
        else:
            return await self._new_tracker.fetch_issue(issue_id)
    
    async def fetch_issues_by_states(
        self,
        state_ids: list[str],
        project_slug: Optional[str] = None
    ) -> list[dict]:
        """Fetch issues by state IDs.
        
        Args:
            state_ids: List of state IDs
            project_slug: Optional project slug
            
        Returns:
            List of issue dicts
        """
        self._record_metrics("old" if self._tracker_type == "old" else "new")
        
        if self._tracker_type == "old":
            return await self._old_tracker.fetch_issues_by_states(
                state_ids=state_ids,
                project_slug=project_slug
            )
        else:
            return await self._new_tracker.fetch_issues_by_states(
                state_ids=state_ids,
                project_slug=project_slug
            )
    
    async def update_issue_state(
        self,
        issue_id: str,
        state_id: str
    ) -> dict:
        """Update issue state.
        
        Args:
            issue_id: Issue identifier
            state_id: New state ID
            
        Returns:
            Updated issue dict
        """
        self._record_metrics("old" if self._tracker_type == "old" else "new")
        
        if self._tracker_type == "old":
            return await self._old_tracker.update_issue_state(
                issue_id=issue_id,
                state_id=state_id
            )
        else:
            return await self._new_tracker.update_issue_state(
                issue_id=issue_id,
                state_id=state_id
            )
    
    def _record_metrics(self, tracker_type: str):
        """Record metrics for monitoring.
        
        Args:
            tracker_type: "old" or "new"
        """
        # This would integrate with observability system
        logger.debug(f"Metrics: tracker_type={tracker_type}")
    
    def get_tracker_type(self) -> str:
        """Get current tracker type.
        
        Returns:
            "old" or "new"
        """
        return self._tracker_type
    
    def get_feature_flags(self) -> FeatureFlags:
        """Get feature flags.
        
        Returns:
            FeatureFlags instance
        """
        return self._feature_flags
    
    async def close(self):
        """Clean up resources."""
        if self._old_tracker:
            await self._old_tracker.close()
```

### 5.2. Интеграция с Orchestrator

Интеграция TrackerFacade в Orchestrator:

```python
# runtime/orchestrator/tracker_integration.py

from typing import Optional
import logging

from ..tracker.facade import TrackerFacade
from ..tracker.base import TrackerConfig

logger = logging.getLogger(__name__)


class TrackerIntegration:
    """Integration layer for tracker in Orchestrator."""
    
    def __init__(self, config: TrackerConfig):
        """Initialize tracker integration.
        
        Args:
            config: Tracker configuration
        """
        self._facade = TrackerFacade(config)
        self._initialized = True
        
        logger.info(
            f"Tracker initialized: type={self._facade.get_tracker_type()}"
        )
    
    async def fetch_issue(self, issue_id: str) -> dict:
        """Fetch issue by ID.
        
        Args:
            issue_id: Issue identifier
            
        Returns:
            Issue data dict
        """
        return await self._facade.fetch_issue(issue_id)
    
    async def fetch_issues_by_states(
        self,
        state_ids: list[str],
        project_slug: Optional[str] = None
    ) -> list[dict]:
        """Fetch issues by state.
        
        Args:
            state_ids: State IDs to filter
            project_slug: Project slug
            
        Returns:
            List of issues
        """
        return await self._facade.fetch_issues_by_states(
            state_ids=state_ids,
            project_slug=project_slug
        )
    
    async def update_issue_state(
        self,
        issue_id: str,
        state_id: str
    ) -> dict:
        """Update issue state.
        
        Args:
            issue_id: Issue ID
            state_id: New state ID
            
        Returns:
            Updated issue
        """
        return await self._facade.update_issue_state(
            issue_id=issue_id,
            state_id=state_id
        )
    
    def get_tracker_type(self) -> str:
        """Get active tracker type.
        
        Returns:
            "old" or "new"
        """
        return self._facade.get_tracker_type()
    
    def get_feature_flags(self) -> dict:
        """Get active feature flags.
        
        Returns:
            Feature flags dict
        """
        flags = self._facade.get_feature_flags()
        return {
            "enabled": flags.tracker_pluggable_enabled,
            "rollout_pct": flags.tracker_pluggable_rollout_pct
        }
    
    async def close(self):
        """Clean up resources."""
        await self._facade.close()
        self._initialized = False
```

---

## 6. Дизайн процедуры отката

### 6.1. Триггеры отката

#### Автоматические триггеры

| Триггер | Условие | Действие |
|---------|---------|----------|
| Error rate | > 5% за 10 минут | Auto rollback |
| Latency | > 2x baseline | Auto rollback |
| Critical errors | > 1% (500/503) | Auto rollback |
| Timeout | > 10% requests | Warning + review |

#### Ручные триггеры

| Триггер | Команда | Время выполнения |
|---------|---------|-------------------|
| Emergency rollback | SYMPHONY_TRACKER_PLUGGABLE_ENABLED=false | < 1 минута |
| Gradual rollback | decrease rollout_pct | < 5 минут |

### 6.2. Процедура отката

#### Шаг 1: Остановка нового трекера

```bash
# Установка переменной окружения
export SYMPHONY_TRACKER_PLUGGABLE_ENABLED=false
export SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT=0
```

#### Шаг 2: Перезапуск Orchestrator

```bash
# Graceful restart
pkill -HUP symphony  # или
systemctl restart symphony
```

#### Шаг 3: Проверка

```bash
# Проверка логов
grep "Using OLD tracker" /var/log/symphony.log

# Проверка метрик
curl -s http://localhost:9090/metrics | grep tracker
```

#### Шаг 4: Мониторинг

```bash
# Мониторинг в течение 10 минут
watch -n 10 'curl -s http://localhost:9090/metrics | grep error_rate'
```

### 6.3. Сценарий отката

```python
# runtime/tracker/rollback.py

import os
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class RollbackProcedure:
    """Manages rollback procedure."""
    
    def __init__(self, service_name: str = "symphony"):
        """Initialize rollback procedure.
        
        Args:
            service_name: Name of service to restart
        """
        self._service_name = service_name
    
    def execute_rollback(self) -> bool:
        """Execute rollback procedure.
        
        Returns:
            True if successful
        """
        try:
            # Step 1: Set environment variables
            self._set_rollback_flags()
            
            # Step 2: Restart service
            self._restart_service()
            
            # Step 3: Verify
            if not self._verify_rollback():
                logger.error("Rollback verification failed")
                return False
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def _set_rollback_flags(self):
        """Set rollback feature flags."""
        os.environ["SYMPHONY_TRACKER_PLUGGABLE_ENABLED"] = "false"
        os.environ["SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT"] = "0"
        
        logger.info("Rollback flags set")
    
    def _restart_service(self):
        """Restart service."""
        try:
            # Try systemctl first
            subprocess.run(
                ["systemctl", "restart", self._service_name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            # Fallback to pkill
            subprocess.run(
                ["pkill", "-HUP", self._service_name],
                check=True,
                capture_output=True
            )
        
        logger.info(f"Service {self._service_name} restarted")
    
    def _verify_rollback(self) -> bool:
        """Verify rollback was successful.
        
        Returns:
            True if verified
        """
        # This would check logs and metrics
        # Implementation depends on observability system
        return True
```

---

## 7. Стратегия тестирования

### 7.1. Фаза 1: Unit Tests

#### Цель

Тестирование отдельных компонентов compatibility layer.

#### Тесты

| Тест | Компонент | Ожидаемый результат |
|------|----------|---------------------|
| AsyncTrackerWrapper.init | AsyncTrackerWrapper | Initializes with correct defaults |
| AsyncTrackerWrapper.fetch_issue | AsyncTrackerWrapper | Returns issue dict |
| AsyncTrackerWrapper.timeout | AsyncTrackerWrapper | Raises TimeoutError |
| IssueWrapper.dict_to_dataclass | IssueWrapper | Returns Issue instance |
| IssueWrapper.dataclass_to_dict | IssueWrapper | Returns dict |
| IssueWrapper.normalize | IssueWrapper | Handles both formats |
| TrackerFacade.should_use_old | TrackerFacade | Correct routing logic |
| TrackerFacade.percentage_routing | TrackerFacade | Consistent hashing |

#### Примеры тестов

```python
# runtime/tests/test_compat.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from runtime.tracker.compat import (
    AsyncTrackerWrapper,
    IssueWrapper,
    Issue
)


class TestAsyncTrackerWrapper:
    """Test AsyncTrackerWrapper."""
    
    @pytest.fixture
    def mock_tracker(self):
        """Create mock tracker."""
        tracker = Mock()
        tracker.fetch_issue = Mock(return_value={
            "id": "ISSUE-1",
            "title": "Test issue"
        })
        return tracker
    
    @pytest.fixture
    def wrapper(self, mock_tracker):
        """Create wrapper instance."""
        return AsyncTrackerWrapper(mock_tracker)
    
    @pytest.mark.asyncio
    async def test_fetch_issue(self, wrapper):
        """Test fetch_issue method."""
        result = await wrapper.fetch_issue("ISSUE-1")
        
        assert result["id"] == "ISSUE-1"
        assert result["title"] == "Test issue"
    
    @pytest.mark.asyncio
    async def test_timeout(self, mock_tracker):
        """Test timeout handling."""
        import time
        
        def slow_fetch(issue_id):
            time.sleep(2)  # Longer than timeout
            return {"id": issue_id}
        
        mock_tracker.fetch_issue = slow_fetch
        
        wrapper = AsyncTrackerWrapper(
            mock_tracker,
            timeout_seconds=0.1
        )
        
        with pytest.raises(asyncio.TimeoutError):
            await wrapper.fetch_issue("ISSUE-1")
    
    def test_get_metrics(self, wrapper):
        """Test metrics collection."""
        metrics = wrapper.get_metrics()
        
        assert "calls_total" in metrics
        assert "errors_total" in metrics
        assert "error_rate" in metrics


class TestIssueWrapper:
    """Test IssueWrapper."""
    
    @pytest.fixture
    def wrapper(self):
        """Create wrapper instance."""
        return IssueWrapper()
    
    def test_dict_to_dataclass(self, wrapper):
        """Test dict to dataclass conversion."""
        issue_dict = {
            "id": "123",
            "identifier": "ISSUE-1",
            "title": "Test issue",
            "description": "Description"
        }
        
        issue = wrapper.dict_to_dataclass(issue_dict)
        
        assert isinstance(issue, Issue)
        assert issue.id == "123"
        assert issue.identifier == "ISSUE-1"
    
    def test_dataclass_to_dict(self, wrapper):
        """Test dataclass to dict conversion."""
        issue = Issue(
            id="123",
            identifier="ISSUE-1", 
            title="Test issue"
        )
        
        result = wrapper.dataclass_to_dict(issue)
        
        assert isinstance(result, dict)
        assert result["id"] == "123"
    
    def test_normalize_dict(self, wrapper):
        """Test normalize dict."""
        data = {"id": "123", "title": "Test"}
        
        result = wrapper.normalize(data)
        
        assert isinstance(result, dict)
        assert result["id"] == "123"
    
    def test_normalize_dataclass(self, wrapper):
        """Test normalize dataclass."""
        issue = Issue(
            id="123",
            identifier="ISSUE-1",
            title="Test"
        )
        
        result = wrapper.normalize(issue)
        
        assert isinstance(result, dict)
        assert result["id"] == "123"
```

### 7.2. Фаза 2: Integration Tests

#### Цель

Тестирование взаимодействия между компонентами.

#### Тесты

| Тест | Компонент | Ожидаемый результат |
|------|------------|----------------------|
| Old tracker with mock | TrackerFacade | Returns issues from mock |
| New tracker with mock | TrackerFacade | Returns issues from mock |
| Routing switch | TrackerFacade | Correct routing |
| Both return same format | TrackerFacade | Identical outputs |
| Error propagation | TrackerFacade | Errors propagate correctly |

#### Примеры тестов

```python
# runtime/tests/test_integration.py

import pytest
from unittest.mock import Mock, patch

from runtime.tracker.facade import TrackerFacade
from runtime.tracker.base import TrackerConfig


class TestTrackerFacadeIntegration:
    """Integration tests for TrackerFacade."""
    
    @pytest.fixture
    def config(self):
        """Create test config."""
        return TrackerConfig(
            kind="linear",
            api_key="test-key",
            endpoint="https://api.linear.app/graphql",
            project_slug="test-project",
            active_states=["Todo"],
            terminal_states=["Done"]
        )
    
    @pytest.fixture
    def facade(self, config):
        """Create facade with test config."""
        # Set feature flags to use old
        with patch.dict("os.environ", {
            "SYMPHONY_TRACKER_PLUGGABLE_ENABLED": "false"
        }):
            return TrackerFacade(config)
    
    @pytest.mark.asyncio
    async def test_old_tracker_works(self, facade):
        """Test old tracker integration."""
        # This would use actual mock
        with patch("runtime.tracker.linear.LinearTracker") as mock:
            mock_instance = Mock()
            mock_instance.fetch_issue = Mock(return_value={
                "id": "ISSUE-1",
                "title": "Test"
            })
            mock.return_value = mock_instance
            
            # Re-initialize with mock
            result = await facade.fetch_issue("ISSUE-1")
            
            assert result is not None
    
    def test_routing_logic(self, config):
        """Test routing logic."""
        # Test enabled=false
        with patch.dict("os.environ", {
            "SYMPHONY_TRACKER_PLUGGABLE_ENABLED": "false"
        }):
            facade = TrackerFacade(config)
            
            assert facade.get_tracker_type() == "old"
        
        # Test enabled=true with 0% rollout
        with patch.dict("os.environ", {
            "SYMPHONY_TRACKER_PLUGGABLE_ENABLED": "true",
            "SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT": "0"
        }):
            facade = TrackerFacade(config)
            
            assert facade.get_tracker_type() == "old"
        
        # Test 100% rollout
        with patch.dict("os.environ", {
            "SYMPHONY_TRACKER_PLUGGABLE_ENABLED": "true",
            "SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT": "100"
        }):
            facade = TrackerFacade(config)
            
            assert facade.get_tracker_type() == "new"
```

### 7.3. Фаза 3: Contract Tests

#### Цель

Верификация контрактов между old и new.

#### Тесты

| Тест | Проверяет |
|------|-----------|
| Same interface | Все методы имеют одинаковые сигнатуры |
| Same return types | Возвращаемые типы совпадают |
| Same error types | Исключения обрабатываются одинаково |
| Same field names | Поля данных совпадают |

#### Пример тестов

```python
# runtime/tests/test_contract.py

import pytest
from typing import get_type_hints

from runtime.tracker.old_linear import LegacyLinearTracker
from runtime.tracker.new_linear import NewLinearTracker


class TestContractCompliance:
    """Test contract compliance between old and new."""
    
    def test_same_interface_methods(self):
        """Test both have same public methods."""
        old_methods = set(
            m for m in dir(LegacyLinearTracker)
            if not m.startswith("_")
        )
        new_methods = set(
            m for m in dir(NewLinearTracker)
            if not m.startswith("_")
        )
        
        # New should have all old methods
        missing = old_methods - new_methods
        assert not missing, f"Missing methods: {missing}"
    
    def test_same_return_types(self):
        """Test method return types match."""
        # This would check actual method signatures
        pass
    
    def test_same_error_handling(self):
        """Test error handling is consistent."""
        # This would test both raise same exceptions
        pass
```

### 7.4. Фаза 4: Performance Tests

#### Цель

Измерение производительности.

#### Тесты

| Тест | Метрика | Threshold |
|------|---------|-----------|
| Old tracker latency | avg latency | < 500ms |
| New tracker latency | avg latency | < 500ms |
| Wrapper overhead | diff | < 50ms |
| Throughput | requests/sec | > 10 |

#### Пример теста

```python
# runtime/tests/test_performance.py

import pytest
import time
import asyncio
from statistics import mean

from runtime.tracker.compat import AsyncTrackerWrapper


class TestPerformance:
    """Performance tests."""
    
    @pytest.fixture
    def mock_tracker(self):
        """Create fast mock tracker."""
        tracker = Mock()
        tracker.fetch_issue = Mock(return_value={
            "id": "ISSUE-1",
            "title": "Test"
        })
        return tracker
    
    @pytest.mark.asyncio
    async def test_wrapper_overhead(self, mock_tracker):
        """Test wrapper adds minimal overhead."""
        wrapper = AsyncTrackerWrapper(
            mock_tracker,
            thread_pool_size=10
        )
        
        # Warm up
        for _ in range(10):
            await wrapper.fetch_issue("ISSUE-1")
        
        # Measure
        latencies = []
        for _ in range(100):
            start = time.monotonic()
            await wrapper.fetch_issue("ISSUE-1")
            latencies.append(time.monotonic() - start)
        
        avg_latency = mean(latencies) * 1000  # ms
        
        assert avg_latency < 50, f"Overhead too high: {avg_latency:.1f}ms"
```

### 7.5. Фаза 5: Canary Tests

#### Цель

Тестирование в production-like окружении.

#### Процедура

1. **Staging deployment (1%)**
   - Деплой в staging
   - Мониторинг 1 час
   - Проверка метрик

2. **Staging deployment (5%)**
   - Увеличение до 5%
   - Мониторинг 1 день
   - Проверка error rate < 2%

3. **Production deployment (1%)**
   - Деплой в production
   - Мониторинг 1 день
   - Проверка error rate < 1%

4. **Production rollout**
   - Постепенное увеличение
   - Мониторинг метрик
   - Документация наблюдений

---

## 8. Дизайн observability

### 8.1. Метрики

#### Основные метрики

```python
# runtime/observability/metrics.py

from prometheus_client import Counter, Histogram, Gauge


# API calls by tracker type
TRACKER_API_CALLS = Counter(
    "tracker_api_calls_total",
    "Total API calls",
    ["tracker_type", "method"]
)

# API latency
TRACKER_API_LATENCY = Histogram(
    "tracker_api_latency_seconds",
    "API latency",
    ["tracker_type", "method"]
)

# API errors
TRACKER_API_ERRORS = Counter(
    "tracker_api_errors_total",
    "Total API errors",
    ["tracker_type", "method", "error_type"]
)

# Feature flag state
TRACKER_FEATURE_FLAGS = Gauge(
    "tracker_feature_flag_active",
    "Feature flag state",
    ["flag_name"]
)

# Orchestrator errors
ORCHESTRATOR_ERRORS = Counter(
    "orchestrator_errors_total",
    "Orchestrator errors",
    ["error_type"]
)


# Usage in code

from runtime.observability.metrics import (
    TRACKER_API_CALLS,
    TRACKER_API_LATENCY,
    TRACKER_API_ERRORS,
    TRACKER_FEATURE_FLAGS
)


def track_api_call(tracker_type: str, method: str):
    """Track API call."""
    TRACKER_API_CALLS.labels(
        tracker_type=tracker_type,
        method=method
    ).inc()


def track_latency(tracker_type: str, method: str, latency: float):
    """Track API latency."""
    TRACKER_API_LATENCY.labels(
        tracker_type=tracker_type,
        method=method
    ).observe(latency)


def track_error(tracker_type: str, method: str, error_type: str):
    """Track API error."""
    TRACKER_API_ERRORS.labels(
        tracker_type=tracker_type,
        method=method,
        error_type=error_type
    ).inc()
```

#### Список метрик

| Метрика | Тип | Labels | Описание |
|---------|-----|-------|---------|
| tracker_api_calls_total | Counter | type, method | Total API calls |
| tracker_api_latency_seconds | Histogram | type, method | API latency |
| tracker_api_errors_total | Counter | type, method, error | API errors |
| tracker_feature_flag_active | Gauge | flag_name | Feature flag state |
| orchestrator_errors_total | Counter | error_type | Orchestrator errors |

### 8.2. Логирование

#### Требования к логам

```python
# runtime/observability/logging.py

import logging
import json
from datetime import datetime


class TrackerLogger:
    """Structured logger for tracker operations."""
    
    def __init__(self, logger_name: str):
        """Initialize logger."""
        self._logger = logging.getLogger(logger_name)
    
    def log_tracker_usage(self, tracker_type: str, method: str):
        """Log which tracker is being used."""
        self._logger.info(
            f"Using {tracker_type} tracker for {method}",
            extra={
                "tracker_type": tracker_type,
                "method": method,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_feature_flags(self, feature_flags: dict):
        """Log feature flag state."""
        self._logger.info(
            f"Feature flags: {feature_flags}",
            extra={
                "feature_flags": feature_flags,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_routing_decision(
        self,
        reason: str,
        result: str
    ):
        """Log routing decision."""
        self._logger.info(
            f"Routing decision: {reason} -> {result}",
            extra={
                "reason": reason,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_performance(
        self,
        tracker_type: str,
        method: str,
        latency_ms: float
    ):
        """Log performance comparison."""
        self._logger.info(
            f"Performance: {tracker_type}.{method} = {latency_ms:.1f}ms",
            extra={
                "tracker_type": tracker_type,
                "method": method,
                "latency_ms": latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_error(
        self,
        tracker_type: str,
        method: str,
        error: Exception
    ):
        """Log API error with context."""
        self._logger.error(
            f"Error in {tracker_type}.{method}: {error}",
            extra={
                "tracker_type": tracker_type,
                "method": method,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

#### Список логов

| Уровень | Сообщение | Когда |
|---------|-----------|-------|
| INFO | Using {old/new} tracker | При инициализации |
| INFO | Feature flags: {...} | При запуске |
| INFO | Routing decision: {...} | При маршрутизации |
| INFO | Performance: {...} | После каждого вызова |
| ERROR | Error in {...} | При ошибках |

### 8.3. Dashboard требования

#### Grafana Dashboard

```json
{
  "title": "Tracker Migration Dashboard",
  "panels": [
    {
      "title": "Error Rate by Tracker Type",
      "targets": [
        {
          "expr": "rate(tracker_api_errors_total[5m]) / rate(tracker_api_calls_total[5m])",
          "legendFormat": "{{tracker_type}}"
        }
      ]
    },
    {
      "title": "Latency Comparison (old vs new)",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(tracker_api_latency_seconds_bucket[5m]))",
          "legendFormat": "{{tracker_type}}"
        }
      ]
    },
    {
      "title": "Success Rate by Tracker Type",
      "targets": [
        {
          "expr": "1 - (rate(tracker_api_errors_total[5m]) / rate(tracker_api_calls_total[5m]))",
          "legendFormat": "{{tracker_type}}"
        }
      ]
    },
    {
      "title": "Feature Flag Rollout Progress",
      "targets": [
        {
          "expr": "tracker_feature_flag_active{flag_name='tracker_pluggable_rollout_pct'}",
          "legendFormat": "rollout_pct"
        }
      ]
    }
  ]
}
```

---

## 9. Оценка и митигация рисков

### 9.1. Риск 1: Async/Sync Performance Impact

| Параметр | Значение |
|----------|----------|
| Описание | Thread pool overhead может увеличить latency |
| Вероятность | MEDIUM |
| Влияние | MEDIUM |
| Mitigation | Benchmark и tune pool size |

#### Митигация

1. **Benchmark**: Измерить overhead перед деплоем
2. **Tune pool size**: Настроить размер пула (10-20 workers)
3. **Monitoring**: Отслеживать latency метрики
4. **Tuning**: На основе метрик корректировать

#### Мониторинг

- Отслеживать `tracker_api_latency_seconds`
- Alert при latency > 2x baseline
- Dashboard для сравнения old vs new

### 9.2. Риск 2: Domain Model Conversion Errors

| Параметр | Значение |
|----------|----------|
| Описание | Missing or invalid fields при конвертации |
| Вероятность | MEDIUM |
| Влияние | HIGH |
| Mitigation | Comprehensive unit tests |

#### Митигация

1. **Unit tests**: Тесты для всех сценариев конвертации
2. **Validation**: Валидация полей при конвертации
3. **Logging**: Логирование ошибок конвертации
4. **Fallback**: Использовать original данные при ошибке

#### Мониторинг

- Отслеживать conversion errors
- Alert при error rate > 1%
- Логировать детали ошибок

### 9.3. Риск 3: Feature Flag Configuration Errors

| Параметр | Значение |
|----------|----------|
| Описание | Invalid feature flag values |
| Вероятность | LOW |
| Влияние | MEDIUM |
| Mitigation | Validation on startup |

#### Митигация

1. **Validation**: Валидация значений при запуске
2. **Defaults**: Использовать safe defaults
3. **Logging**: ��ог��ровать все значения флагов
4. **Documentation**: Документация допустимых значений

#### Мониторинг

- Логировать feature flag state при запуске
- Alert при invalid values
- Dashboard для текущих значений

### 9.4. Риск 4: Rollback Complexity

| Параметр | Значение |
|----------|----------|
| Описание | Rollback не работает корректно |
| Вероятность | LOW |
| Влияние | HIGH |
| Mitigation | Test rollback in staging |

#### Митигация

1. **Test rollback**: Тестировать откат в staging
2. **Documentation**: Документировать процедуру
3. **Automation**: Автоматизировать rollback
4. **Quick verification**: Быстрая верификация

#### Мониторинг

- Логировать каждый шаг rollback
- Metrics для verification
- Alert если rollback не работает

---

## 10. Фазы реализации

### 10.1. Фаза 1: Foundation (4-6 часов)

#### Задачи

| # | Задача | Время | Priority |
|---|--------|-------|----------|
| 1 | Create runtime/tracker/compat.py | 2h | HIGH |
| 2 | Implement AsyncTrackerWrapper | 1h | HIGH |
| 3 | Implement IssueWrapper | 1h | HIGH |
| 4 | Write unit tests for wrapper | 2h | HIGH |

#### Deliverables

- `runtime/tracker/compat.py` module
- Unit tests (10+ tests)

### 10.2. Фаза 2: Integration (3-4 часа)

#### Задачи

| # | Задача | Время | Priority |
|---|--------|-------|----------|
| 1 | Implement TrackerFacade | 2h | HIGH |
| 2 | Integrate with orchestrator | 1h | HIGH |
| 3 | Write integration tests | 1h | HIGH |

#### Deliverables

- `runtime/tracker/facade.py` module
- Integration with orchestrator
- Integration tests

### 10.3. Фаза 3: Feature Flags (2-3 часа)

#### Задачи

| # | Задача | Время | Priority |
|---|--------|-------|----------|
| 1 | Add feature flag parsing to config | 1h | HIGH |
| 2 | Implement routing logic | 1h | HIGH |
| 3 | Update WORKFLOW.md docs | 0.5h | MEDIUM |
| 4 | Feature flag tests | 0.5h | MEDIUM |

#### Deliverables

- Feature flag system
- Documentation
- Tests

### 10.4. Фаза 4: Testing (4-6 часов)

#### Задачи

| # | Задача | Время | Priority |
|---|--------|-------|----------|
| 1 | Unit tests (compat layer) | 1h | HIGH |
| 2 | Integration tests (orchestrator) | 1h | HIGH |
| 3 | Performance benchmarks | 1h | MEDIUM |
| 4 | Canary deployment plan | 1h | MEDIUM |

#### Deliverables

- All tests pass
- Performance baseline
- Deployment plan

### 10.5. Фаза 5: Gradual Rollout (ongoing)

#### Задачи

| # | Задача | Длительность | Priority |
|---|--------|---------------|----------|
| 1 | Deploy to staging (5%) | 1 день | HIGH |
| 2 | Monitor metrics | 1 день | HIGH |
| 3 | Production rollout (1%) | 1 день | HIGH |
| 4 | Gradual increase | 2 недели | MEDIUM |
| 5 | Remove old tracker | 2-4 недели | LOW |

#### Критерии перехода между этапами

| Этап | Критерий |
|------|----------|
| 5% → 10% | error < 2%, latency < 1.5x |
| 10% → 25% | error < 3%, latency < 2x |
| 25% → 50% | error < 3%, stable |
| 50% → 100% | error < 1%, 2 weeks stable |

### 10.6. Фаза 6: Cleanup (2-3 часа)

#### Задачи

| # | Задача | Время | Priority |
|---|--------|-------|----------|
| 1 | Remove old tracker code | 1h | MEDIUM |
| 2 | Remove compatibility layer | 1h | MEDIUM |
| 3 | Update documentation | 0.5h | LOW |
| 4 | Clean up tests | 0.5h | LOW |

#### Deliverables

- Clean codebase
- Updated documentation

---

## 11. Критерии успеха

### 11.1. Технические критерии

| Критерий | Целевое значение | Measurement |
|----------|------------------|-------------|
| All tests pass | 100% | CI/CD |
| Performance | within 10% baseline | Prometheus |
| Error rate | < 0.1% | Prometheus |
| Breaking changes | 0 | User reports |

### 11.2. Операционные критерии

| Критерий | Целевое значение | Время выполнения |
|----------|-------------------|------------------|
| Feature flag toggle | < 5 минут | Manual |
| Rollback completion | < 10 минут | Manual |
| Metrics dashboard | 100% ready | Manual |
| Documentation | 100% complete | Manual |

### 11.3. Бизнес критерии

| Критерий | Целевое значение | Impact |
|----------|------------------|--------|
| Downtime | 0 минут | User experience |
| Issue processing | No impact | Operations |
| Data loss | 0 | Data integrity |
| User workflow | Unchanged | User experience |

---

## 12. Следующие шаги

### Подготовка к Фазе 1

1. **Initialize task**: Создать задачу в трекере
2. **Verify specs**: Проверить спецификации
3. **Setup environment**: Настроить окружение разработки
4. **Review codebase**: Изучить текущую реализацию

### Before starting implementation

1. **Load skill**: Загрузить coding-standards skill
2. **Review imports**: Проверить текущие импорты
3. **Verify compatibility**: Убедиться в совместимости
4. **Prepare tests**: Подготовить тестовую инфраструктуру

### First implementation tasks

1. Create `runtime/tracker/compat.py`
2. Implement AsyncTrackerWrapper
3. Implement IssueWrapper
4. Write unit tests

### Documentation to prepare

1. API文档 для compatibility layer
2. Тестовая документация
3. Runbook дляRollback процедуры

---

## Appendix A: Список файлов

| Файл | Описание |
|------|----------|
| `runtime/tracker/compat.py` | Compatibility layer |
| `runtime/tracker/facade.py` | TrackerFacade |
| `runtime/tracker/feature_flags.py` | Feature flags |
| `runtime/tracker/rollback.py` | Rollback procedure |
| `runtime/tests/test_compat.py` | Unit tests |
| `runtime/tests/test_integration.py` | Integration tests |
| `runtime/tests/test_performance.py` | Performance tests |

## Appendix B: Конфигурация по умолчанию

```yaml
# Default configuration for migration

tracker:
  kind: linear
  
  # Migration feature flags
  feature_flags:
    tracker_pluggable_enabled: false
    tracker_pluggable_rollout_pct: 0
    tracker_pluggable_log_metrics: true
    tracker_pluggable_strict_mode: false
    
    # Rollback thresholds
    tracker_pluggable_error_threshold_pct: 5.0
    tracker_pluggable_latency_threshold_ms: 2000

# Environment variables

SYMPHONY_TRACKER_PLUGGABLE_ENABLED=false
SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT=0
```

---

## Appendix C: Quick Reference

### Команды управления

```bash
# Enable new tracker
export SYMPHONY_TRACKER_PLUGGABLE_ENABLED=true
export SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT=5

# Rollback
export SYMPHONY_TRACKER_PLUGGABLE_ENABLED=false
export SYMPHONY_TRACKER_PLUGGABLE_ROLLOUT_PCT=0

# Restart
pkill -HUP symphony
```

### Метрики для мониторинга

```bash
# Error rate
rate(tracker_api_errors_total[5m]) / rate(tracker_api_calls_total[5m])

# Latency
histogram_quantile(0.95, rate(tracker_api_latency_seconds_bucket[5m]))

# Success rate
1 - (rate(tracker_api_errors_total[5m]) / rate(tracker_api_calls_total[5m]))
```

---

**End of Document**