"""
A generic object to add extra functionality to pydantic.BaseModel.

Should be used as the base class for all classes in the project.
"""

import re
from collections.abc import Callable
from typing import (
    Any,
    ClassVar,
    TypeVar,
    cast,
)

from pydantic import BaseModel, ConfigDict, PrivateAttr
from pydantic_core._pydantic_core import PydanticUndefined

from amati._logging import Logger


class GenericObject(BaseModel):
    """
    A generic model to overwrite provide extra functionality
    to pydantic.BaseModel.
    """

    _reference_uri: ClassVar[str] = PrivateAttr()
    _extra_field_pattern: re.Pattern[str] | None = PrivateAttr()

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
                Logger.log(
                    {
                        "msg": message,
                        "type": "value_error",
                        "loc": (self.__repr_name__(),),
                        "input": field,
                        "url": self._reference_uri,
                    }
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

        pattern: re.Pattern[str] = re.compile(self._extra_field_pattern)
        excess_fields.update(
            key for key in self.model_extra.keys() if not pattern.match(key)
        )

        for field in excess_fields:
            message = f"{field} is not a valid field for {self.__repr_name__()}."
            Logger.log(
                {
                    "msg": message,
                    "type": "value_error",
                    "loc": (self.__repr_name__(),),
                    "input": field,
                    "url": self._reference_uri,
                }
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


def allow_extra_fields(pattern: str | None = None) -> Callable[[type[T]], type[T]]:
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

    def decorator(cls: type[T]) -> type[T]:
        """
        A decorator function that adds a ConfigDict allowing extra fields.
        """
        namespace: dict[str, ConfigDict | str | None] = {
            "model_config": ConfigDict(extra="allow"),
            "_extra_field_pattern": pattern,
        }
        # Create a new class with the updated configuration
        return cast(type[T], type(cls.__name__, (cls,), namespace))

    return decorator
