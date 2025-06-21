"""
HTTP Authentication Scheme validation module.

This module provides functionality for validating HTTP authentication schemes according
to the IANA registry defined in ISO9110. It includes constants, data loading utilities,
and a class for scheme validation.
"""

import json
import pathlib

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str

reference = Reference(
    title="Hypertext Transfer Protocol (HTTP) Authentication Scheme Registry (ISO9110)",
    url="https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml",
)


DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "iso9110.json", "r", encoding="utf-8") as f:
    data = json.loads(f.read())


HTTP_AUTHENTICATION_SCHEMES: set[str] = set(
    [x["Authentication Scheme Name"].lower() for x in data]
)


class HTTPAuthenticationScheme(_Str):
    """
    A class representing an HTTP authentication scheme as defined in ISO9110.

    This class validates that a string value is a registered HTTP authentication scheme
    according to the IANA registry. It inherits from _Str to maintain compatibility
    with string operations while adding HTTP authentication-specific validation.

    The validation is performed against the list of schemes loaded from the ISO9110
    data file, which includes schemes like Basic, Bearer, Digest, etc.

    Attributes:
        Inherits all attributes from _Str

    Example:
        >>> scheme = HTTPAuthenticationScheme("Bearer")
        >>> str(scheme)
        'Bearer'
        >>> HTTPAuthenticationScheme("InvalidScheme")
        Traceback (most recent call last):
        amati.AmatiValueError: message
    """

    def __init__(self, value: str):

        if value.lower() not in HTTP_AUTHENTICATION_SCHEMES:
            raise AmatiValueError(
                f"{value} is not a valid HTTP authentication schema.",
                reference=reference,
            )
