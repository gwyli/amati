"""
Validates IANA HTTP status codes,

Note that the codes ^[1-5]XX$ are not valid HTTP status codes,
but are in common usage. They can be accessed separately via HTTPStatusCodeX,
or the numeric codes can be accessed via HTTPStatusCodeN.
"""

import json
import pathlib
import re
from typing import Optional, Self

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str

reference = Reference(
    title="Hypertext Transfer Protocol (HTTP) Status Code Registry",
    url="https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml",
)

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "http-status-codes.json", "r", encoding="utf-8") as f:
    HTTP_STATUS_CODES = json.loads(f.read())


class HTTPStatusCode(_Str):
    """
    A class representing an HTTP status code as defined in RFC 7231 and related RFCs.

    This class validates and provides information about HTTP status codes, including
    whether they are registered with IANA, assigned for use, or represent a status code
    range (e.g., 4XX). It inherits from _Str to maintain compatibility with string
    operations while adding HTTP-specific validation and metadata.

    Attributes:
        description (Optional[str]): The official description of the status code,
            if registered.
        is_registered (bool): Whether the status code is registered with IANA.
        is_assigned (bool): Whether the status code is assigned for use
            (not marked as 'Unassigned').
        is_range (bool): Whether the status code represents a range (e.g., "2XX").
    """

    description: Optional[str] = None
    is_registered: bool = False
    is_assigned: bool = False
    is_range: bool = False
    _pattern = re.compile(r"^[1-5]XX$")

    def __init__(self: Self, value: str):
        """
        Initialize an HTTPStatusCode object from a string or integer value.

        Validates the input against known HTTP status codes and status code ranges.
        Sets attributes indicating whether the code is registered, assigned, and/or
        represents a range.

        NB: OAS 3.1.1 states that:
        > This field MUST be enclosed in quotation marks (for example, “200”)
        > for compatibility between JSON and YAML.

        Args:
            value (str | int): A string or integer representing an HTTP status code
                (e.g., "200", 404) or status code range (e.g., "4XX").

        Raises:
            AmatiValueError: If the provided value is not a valid HTTP status code or
                status code range.
        """

        # Type-hinting that something should be a string is not enough
        # double check that a string will be returned in the models.
        if not isinstance(value, str):  # type: ignore

            type_ = type(value).__name__
            raise AmatiValueError(
                f"{value} of type {type_} cannot be a valid HTTP Status code."
            )

        candidate = str(value)

        if candidate in HTTP_STATUS_CODES:
            self.is_registered = True
            self.description = HTTP_STATUS_CODES[candidate]
        elif self._pattern.match(candidate):
            self.is_range = True
        else:
            raise AmatiValueError(
                f"{value} is not a valid HTTP Status Code", reference=reference
            )

        if self.description != "Unassigned":
            self.is_assigned = True
