"""
A generic object to add extra functionality to pydantic.BaseModel.

Should be used as the base class for all classes in the project.
"""

import re
from typing import (
    Any,
    Callable,
    ClassVar,
    Optional,
    Pattern,
    Type,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel, ConfigDict, PrivateAttr

from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference


class GenericObject(LogMixin, BaseModel):
    """
    A generic model to overwrite provide extra functionality
    to pydantic.BaseModel.
    """

    _reference: ClassVar[Optional[Reference]] = PrivateAttr()
    _pattern: Pattern[str] = PrivateAttr()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        if "extra" in self.model_config:
            return

        # If extra fields aren't allowed log those that aren't going to be added
        # to the model.
        for field in data:
            if field in self.model_fields:
                continue
            LogMixin.log(
                Log(
                    message=f"{field} is not a valid field for {self.__repr_name__()}.",
                    type=ValueError,
                )
            )

    def model_post_init(self, __context: Any) -> None:
        if not self.model_extra:
            return

        excess_fields: set[str] = set()

        # Any extra fields are allowed
        if self._pattern is None:
            return
        else:
            prog: Pattern[str] = re.compile(self._pattern)
            excess_fields.update(
                key for key in self.model_extra.keys() if not prog.match(key)
            )

        for field in excess_fields:
            message = f"{field} is not a valid field for {self.__repr_name__()}."
            LogMixin.log(
                Log(
                    message=message,
                    type=ValueError,
                )
            )


T = TypeVar("T", bound=GenericObject)


def allow_extra_fields(pattern: Optional[str] = None) -> Callable[[Type[T]], Type[T]]:
    """
    A decorator that modifies a Pydantic BaseModel to allow extra fields
    and optionally sets a pattern for specification extensions.

    Args:
        pattern: Optional pattern string for specification extensions.
        If not provided all extra fields will be allowed

    Returns:
        A decorator function that adds a ConfigDict allowing extra fields
        and the pattern those fields should follow to the class.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        """
        A decorator function that adds a ConfigDict allowing extra fields.
        """
        namespace: dict[str, Union[ConfigDict, Optional[str]]] = {
            "model_config": ConfigDict(extra="allow"),
            "_pattern": pattern,
        }
        # Create a new class with the updated configuration
        return cast(Type[T], type(cls.__name__, (cls,), namespace))

    return decorator
