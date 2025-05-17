"""
Validates a media type or media type range according to RFC7321
"""

import json
import pathlib
from typing import Any, Optional

from abnf import ParseError
from abnf.grammars import rfc7231
from pydantic_core import core_schema

from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title="Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content",
    url="https://datatracker.ietf.org/doc/html/rfc7231#appendix-D",
    section="Appendix D",
)

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "media-types.json", "r", encoding="utf-8") as f:
    MEDIA_TYPES = json.loads(f.read())


class MediaType(str):
    """
    Defines a URI, and adds whether the URI is relative, absolute
    etc. The class allows for the type URI to be treated as if it
    were a string in calling Pydantic models.
    """

    type: str = ""
    subtype: str = ""
    parameter: Optional[str] = None
    is_registered: bool = False
    is_range: bool = False

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """Define how Pydantic should handle this custom type."""
        return core_schema.chain_schema(
            [
                # First validate as a string
                core_schema.str_schema(),
                # Then convert to our Test type and run validation
                core_schema.no_info_plain_validator_function(cls.validate),
            ]
        )

    def __init__(self, value: str):
        """
        Validate that the URI is a valid URI, absolute, relative
        or a JSON pointer

        Args:
            value: The URI to validate
        """

        # The OAS standard is to use a fragment identifier
        # (https://www.rfc-editor.org/rfc/rfc6901#section-6) to indicate
        # that it is a JSON pointer per RFC 6901, e.g.
        # "$ref": "#/components/schemas/pet".
        # The hash does not indicate that thex URI is a fragment.

        try:
            media_type = rfc7231.Rule("media-type").parse_all(value)

            for node in media_type.children:
                if node.name in self.__annotations__:
                    self.__dict__[node.name] = node.value

        except ParseError as e:
            raise ValueError("Invalid media type or media type range") from e

        if self.type in MEDIA_TYPES:

            if self.subtype == "*":
                self.is_range = True
                self.is_registered = True

            if self.subtype in MEDIA_TYPES[self.type]:
                self.is_registered = True

        if value == "*/*":
            self.is_range = True
            self.is_registered = True

    @classmethod
    def validate(cls, value: str) -> "MediaType":
        return cls(value)

    def __str__(self) -> str:
        parameter_string = ""
        if self.parameter:
            parameter_string = f"; {self.parameter}"

        return f"{self.type}/{self.subtype}{parameter_string}"
