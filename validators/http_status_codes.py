from http import HTTPStatus
from pydantic import Field, AfterValidator
from typing import Annotated
import warnings

def validate_http_status(value: int) -> int:
    if value not in HTTPStatus._value2member_map_:
        warnings.warn(f"Status code {value} is unassigned or invalid.")
    return value

HTTPStatusCode = Annotated[
    int,
    Field(strict=True, ge=100, le=599),
    AfterValidator(validate_http_status)
]