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
from pydantic_core._pydantic_core import PydanticUndefined

from amati import Reference
from amati.logging import Log, LogMixin


class GenericObject(LogMixin, BaseModel):
    """
    A generic model to overwrite provide extra functionality
    to pydantic.BaseModel.
    """

    _reference: ClassVar[Reference] = PrivateAttr()
    _extra_field_pattern: Optional[Pattern[str]] = PrivateAttr()

    def __init__(self, **data: Any) -> None:

        super().__init__(**data)

        if self.model_config.get("extra") == "allow":
            return

        # If extra fields aren't allowed log those that aren't going to be added
        # to the model.
        for field in data:
            if (
                field not in self.model_dump().keys()
                and field not in self.get_field_aliases()
            ):
                message = f"{field} is not a valid field for {self.__repr_name__()}."
                self.log(
                    Log(
                        message=message,
                        type=ValueError,
                    )
                )

    def model_post_init(self, __context: Any) -> None:
        if not self.model_extra:
            return

        if self.__private_attributes__["_extra_field_pattern"] == PrivateAttr(
            PydanticUndefined
        ):
            return

        # Any extra fields are allowed
        if self._extra_field_pattern is None:
            return

        excess_fields: set[str] = set()

        pattern: Pattern[str] = re.compile(self._extra_field_pattern)
        excess_fields.update(
            key for key in self.model_extra.keys() if not pattern.match(key)
        )

        for field in excess_fields:
            message = f"{field} is not a valid field for {self.__repr_name__()}."
            LogMixin.log(
                Log(
                    message=message,
                    type=ValueError,
                )
            )

    def get_field_aliases(self) -> list[str]:
        """
        Gets a list of aliases for confirming whether extra
        fields are allowed.

        Returns:
            A list of field aliases for the class.
        """

        aliases: list[str] = []

        for field_info in self.__class__.model_fields.values():
            if field_info.alias:
                aliases.append(field_info.alias)

        return aliases


T = TypeVar("T", bound=GenericObject)


def allow_extra_fields(pattern: Optional[str] = None) -> Callable[[Type[T]], Type[T]]:
    """
    A decorator that modifies a Pydantic BaseModel to allow extra fields and optionally
    sets a pattern for those extra fields

    Args:
        pattern: Optional pattern string for extra fields. If not provided all extra
        fields will be allowed

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
            "_extra_field_pattern": pattern,
        }
        # Create a new class with the updated configuration
        return cast(Type[T], type(cls.__name__, (cls,), namespace))

    return decorator
