"""
A generic object to add extra functionality to pydantic.BaseModel.

Should be used as the base class for all classes in the project.
"""

from typing import ClassVar, Optional, Self

from pydantic import BaseModel, PrivateAttr

from amati.fields.json import JSON
from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference


class GenericObject(LogMixin, BaseModel):
    """
    A generic model to overwrite provide extra functionality
    to pydantic.BaseModel.
    """

    _reference: ClassVar[Optional[Reference]] = PrivateAttr()

    def __init__(self: Self, **data: JSON):

        for key in data:
            if key not in self.model_fields:
                LogMixin.log(
                    Log(
                        message=f"{key} is not a valid field for this {self.__repr_name__()}.",  # pylint: disable=line-too-long
                        type=ValueError,
                    )
                )

        super().__init__(**data)
