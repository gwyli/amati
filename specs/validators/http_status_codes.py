import warnings

from typing import Annotated
from itertools import chain

from pydantic import Field, AfterValidator, PositiveInt




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

def _validate_after(value: PositiveInt) -> PositiveInt:
    if value not in ASSIGNED_HTTP_STATUS_CODES:
        warnings.warn(UserWarning(f"Status code {value} is unassigned or invalid."))
    return value

HTTPStatusCode = Annotated[
    PositiveInt,
    Field(strict=True, ge=100, le=599),
    AfterValidator(_validate_after)
    ]

HTTPStatusCodeX = Annotated[
    str,
    Field(strict=True, pattern='^[1-5]XX$')
    ]
