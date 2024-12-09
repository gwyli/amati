"""
Logging utilities for Amati.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import ClassVar, List, Optional, Type, Generator

from pydantic import AnyUrl

LogType = Exception | Warning

@dataclass(frozen=True)
class Log:
    message: str
    type: Type[LogType]
    reference: Optional[AnyUrl] = None


class LogMixin(object):
    """
    A mixin class that provides logging functionality.

    This class maintains a list of Log messages and provides methods to
    manage and interact with these logs.
    """
    logs: ClassVar[List[Log]] = []

    @classmethod
    def log(cls, message: Log) -> List[Log]:
        """Add a new log message to the logs list.

        Args:
            message: A Log object containing the message to be logged.

        Returns:
            The current list of logs after adding the new message.
        """
        cls.logs.append(message)
        return cls.logs

    @classmethod
    def clear(cls) -> None:
        """Clear all stored logs."""
        cls.logs.clear()

    @classmethod
    @contextmanager
    def context(cls) -> Generator[List[Log], None, None]:
        """Create a context manager for handling logs.

        Yields:
            The current list of logs.

        Notes:
            Automatically resets the logs when exiting the context.
        """
        try:
            yield cls.logs
        finally:
            cls.clear()
