from http import HTTPStatus
from pydantic import Field, AfterValidator
from typing import Annotated
from itertools import chain
import warnings

ASSIGNED_HTTP_STATUS_CODES = set(chain(
    [100, 101, 102, 103, 104],
    range(200, 209),
    [226],
    range(300, 308),
    range(400, 418),
    range(421, 426),
    range(428, 429),
    [431, 451],
    range(500, 508),
    range(510, 511)
))

def validate_http_status(value: int) -> int:
    if value not in ASSIGNED_HTTP_STATUS_CODES:
        warnings.warn(f"Status code {value} is unassigned or invalid.", UserWarning)
    return value

HTTPStatusCode = Annotated[
    int,
    Field(strict=True, ge=100, le=599),
    AfterValidator(validate_http_status)
]