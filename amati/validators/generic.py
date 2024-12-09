"""
A generic object to add extra functionality to pydantic.BaseModel.

Should be used as the base class for all classes in the project.
"""

from types import NoneType
from typing import Self, Union

from pydantic import BaseModel

from amati.logging import LogMixin, Log


# Define JSON
JSONPrimitive = Union[str, int, float, bool, NoneType]
JSONArray = list['JSONValue']
JSONObject = dict[str, 'JSONValue']
JSONValue = Union[JSONPrimitive, JSONArray, JSONObject]

# Type alias for cleaner usage
JSON = JSONValue


class GenericObject(LogMixin, BaseModel):
    """
    A generic model to overwrite provide extra functionality 
    to pydantic.BaseModel.
    """

    def __init__(self: Self, **data: JSON):

        for key in data:
            if key not in self.model_fields:
                LogMixin.log(Log(f'{key} is not a valid field for this object.', ValueError))

        super().__init__(**data)
