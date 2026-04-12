"""Agent backend abstraction layer.

Per TASK-003, this module defines the abstract base class for agent backends,
allowing the AgentRunner to remain agnostic of the specific agent implementation
(Codex, claude-code, aider, opencode, etc.).
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    from .agent import AgentEvent
    from .tracker import Issue


logger = logging.getLogger(__name__)


@dataclass
class TurnResult:
    """Результат выполнения одного turn.

    Per SPEC.md Section 10.3, tracks the outcome of a single
    interaction with the agent.

    Attributes:
        status: Статус turn (completed, failed, cancelled, etc.)
        usage: Метрики использования (token counts, etc.)
        error: Описание ошибки если есть
    """

    status: str
    usage: dict
    error: Optional[str] = None


class AgentBackend(ABC):
    """Абстрактный базовый класс для agent backend'ов.

    Per TASK-003, эта абстракция скрывает за собой:
    - Запуск процесса
    - Protocol handshake
    - Чтение событий
    - Управление turns

    Конкретные реализации (CodexBackend, ClaudeCodeBackend, и т.д.)
    должны наследовать от этого класса.

    Note:
        AgentEvent остаётся внешним контрактом (определён в agent.py).
        Callback механизм остаётся в AgentRunner, не в backend.
    """

    @abstractmethod
    async def start(self, workspace_path: Path) -> None:
        """Запустить процесс/сессию агента.

        Args:
            workspace_path: Путь к workspace директории

        Raises:
            RuntimeError: Если процесс не может быть запущен
        """
        pass

    @abstractmethod
    async def run_session(
        self,
        issue: "Issue",
        prompt: str,
        event_callback: Optional[Callable[["AgentEvent"], None]] = None,
    ) -> str:
        """Выполнить сессию, вернуть session_id.

        Per SPEC.md Section 10.2, performs the protocol handshake sequence:
        initialize -> initialized -> thread/start -> turn/start

        Args:
            issue: Объект Issue из трекера
            prompt: Initial prompt для сессии
            event_callback: Callback для lifecycle events

        Returns:
            session_id: Уникальный идентификатор сессии

        Raises:
            ProtocolError: Если handshake не удался
        """
        pass

    @abstractmethod
    async def run_turn(
        self,
        prompt: str,
        event_callback: Optional[Callable[["AgentEvent"], None]] = None,
    ) -> TurnResult:
        """Выполнить один turn, вернуть статус.

        Per SPEC.md Section 10.3, executes a single turn and waits
        for completion, returning the status and usage metrics.

        Args:
            prompt: Prompt для этого turn
            event_callback: Callback для lifecycle events

        Returns:
            TurnResult: Статус, usage и error (если есть)

        Raises:
            ProtocolError: Если запрос turn/start не удался
            TimeoutError: Если turn не завершился за отведённое время
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Остановить процесс.

        Gracefully shuts down the agent process and cleans up resources.
        Performs:
        - Cancels pending read tasks
        - Closes stdin writer
        - Terminates process with timeout
        - Falls back to kill if necessary
        """
        pass
