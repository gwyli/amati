from typing import Any, Self
from pydantic import BaseModel

class GenericObject(BaseModel):
    """
    A generic model to overwrite __init__ for BaseModel
    to ensure that passed fields are correct.
    """

    def __init__(self: Self, **data: dict[str, Any]):
        super().__init__(**data)
        for key in data:
            if key not in self.model_fields:
                raise ValueError(f"{key} is not a valid field for this object.")