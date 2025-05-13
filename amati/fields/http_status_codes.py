"""
Validates IANA HTTP status codes,

Note that the codes ^[1-5]XX$ are not valid HTTP status codes,
but are in common usage. They can be accessed separately via HTTPStatusCodeX,
or the numeric codes can be accessed via HTTPStatusCodeN.
"""

from itertools import chain
from typing import Annotated

from pydantic import AfterValidator, Field, PositiveInt

from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title="Hypertext Transfer Protocol (HTTP) Status Code Registry",
    url="https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml",
)


ASSIGNED_HTTP_STATUS_CODES = set(
    chain(
        [100, 101, 102, 103, 104],
        range(200, 209),
        [226],
        range(300, 308),
        range(400, 418),
        range(421, 426),
        range(428, 429),
        [431, 451],
        range(500, 508),
        range(510, 511),
    )
)


def _validate_after(value: PositiveInt) -> PositiveInt:
    """
    Pydantic AfterValidator to raise a warning if the status code is unassigned.

    Args:
        value: The status code

    Returns:
        The unchanged value

    Warns:
        UserWarning: If the code is unassigned.
    """

    if value not in ASSIGNED_HTTP_STATUS_CODES:
        message = f"Status code {value} is unassigned or invalid."
        LogMixin.log(Log(message=message, type=Warning, reference=reference))

    return value


type HTTPStatusCodeN = Annotated[  # pylint: disable=invalid-name
    PositiveInt, Field(strict=True, ge=100, le=599), AfterValidator(_validate_after)
]


type HTTPStatusCodeX = Annotated[  # pylint: disable=invalid-name
    str, Field(strict=True, pattern="^[1-5]XX$")
]


# Convenience type for all possibilities
type HTTPStatusCode = HTTPStatusCodeN | HTTPStatusCodeX
