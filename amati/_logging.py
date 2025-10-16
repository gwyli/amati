"""
Logging utilities for Amati.
"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, ClassVar, NotRequired, TypedDict

type LogType = Exception | Warning


@dataclass(frozen=True)
class Log(TypedDict):
    type: str
    loc: NotRequired[tuple[int | str, ...]]
    msg: str
    input: NotRequired[Any]
    url: NotRequired[str]


class Logger:
    """A simple class-level logger for collecting Log objects.

    This class provides methods for appending logs and managing
    a logging context that automatically clears the logs.
    """

    logs: ClassVar[list[Log]] = []

    @classmethod
    def log(cls, message: Log) -> None:
        """Add a new message to the logs list.

        Args:
            message: A Log object containing the message to be logged.

        Returns:
            The current list of logs after adding the new message.
        """
        cls.logs.append(message)

    @classmethod
    @contextmanager
    def context(cls) -> Generator[list[Log]]:
        """Create a context manager for handling logs.

        Yields:
            The current list of logs.

        Notes:
            Automatically clears the logs when exiting the context.
        """
        try:
            yield cls.logs
        finally:
            cls.logs.clear()
