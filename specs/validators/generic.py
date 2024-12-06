from typing import Union, Self
from types import NoneType
from pydantic import BaseModel


JSONPrimitive = Union[str, int, float, bool, NoneType]
JSONArray = list['JSONValue']
JSONObject = dict[str, 'JSONValue']
JSONValue = Union[JSONPrimitive, JSONArray, JSONObject]

# Type alias for cleaner usage
JSON = JSONValue


class GenericObject(BaseModel):
    """
    A generic model to overwrite __init__ for BaseModel
    to ensure that passed fields are correct.
    """

    def __init__(self: Self, **data: JSON):

        for key in data:
            if key not in self.model_fields:
                raise ValueError(
                    f"{key} is not a valid field for this object.")

        super().__init__(**data)