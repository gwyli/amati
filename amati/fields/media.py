"""
Validates a media type or media type range according to RFC7321
"""

import json
import pathlib
from typing import Optional

from abnf import ParseError
from abnf.grammars import rfc7231

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str

reference = Reference(
    title="Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content",
    url="https://datatracker.ietf.org/doc/html/rfc7231#appendix-D",
    section="Appendix D",
)

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "media-types.json", "r", encoding="utf-8") as f:
    MEDIA_TYPES = json.loads(f.read())


class MediaType(_Str):
    """
    A class representing an HTTP media type as defined in RFC 7231.

    This class parses and validates media type strings (e.g., "text/html", "image/png")
    according to the RFC 7231 specification. It provides attributes for accessing the
    components of a media type and methods for string representation.

    Attributes:
        type (str): The primary type component (e.g., "text", "image", "application").
        subtype (str): The subtype component (e.g., "html", "png", "json").
        parameter (Optional[str]): Optional parameters (e.g., "charset=utf-8").
        is_registered (bool): Whether this is a registered IANA media type.
        is_range (bool): Whether this is a media type range (contains wildcards).
    """

    type: str = ""
    subtype: str = ""
    parameter: Optional[str] = None
    is_registered: bool = False
    is_range: bool = False

    def __init__(self, value: str):
        """
        Parses the input string according to RFC 7231 grammar rules for media types.
        Sets the appropriate attributes based on the parsed components and determines
        if the media type is registered and/or represents a range.

        Args:
            value (str): A string representing a media type (e.g., "text/html").

        Raises:
            AmatiValueError: If the input string is not a valid media type according to
                RFC 7231.
        """

        try:
            media_type = rfc7231.Rule("media-type").parse_all(value)

            for node in media_type.children:
                if node.name in self.__annotations__:
                    self.__dict__[node.name] = node.value

        except ParseError as e:
            raise AmatiValueError(
                "Invalid media type or media type range", reference=reference
            ) from e

        if self.type in MEDIA_TYPES:

            if self.subtype == "*":
                self.is_range = True
                self.is_registered = True

            if self.subtype in MEDIA_TYPES[self.type]:
                self.is_registered = True

        if value == "*/*":
            self.is_range = True
            self.is_registered = True

    def __str__(self) -> str:
        """
        Return the string representation of the media type.

        Returns:
            str: A properly formatted media type string
                (e.g., "text/html; charset=utf-8").
        """
        parameter_string = ""
        if self.parameter:
            parameter_string = f"; {self.parameter}"

        return f"{self.type}/{self.subtype}{parameter_string}"
