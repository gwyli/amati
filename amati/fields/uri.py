"""
Validates a URI according to the RFC3986 ABNF grammar
"""

from enum import Enum
from typing import Any

from abnf import ParseError
from abnf.grammars import rfc3986
from pydantic_core import core_schema

from amati.grammars import rfc6901
from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title="Uniform Resource Identifier (URI): Generic Syntax",
    url="https://datatracker.ietf.org/doc/html/rfc3986#appendix-A",
    section="Appendix A",
)


class URIType(str, Enum):
    """Enum for different types of URIs"""

    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    AUTHORITY = "authority"
    JSON_POINTER = "json_pointer"
    UNKNOWN = "unknown"


class URI(str):
    """
    Defines a URI, and adds whether the URI is relative, absolute
    etc. The class allows for the type URI to be treated as if it
    were a string in calling Pydantic models.
    """

    type: URIType

    def __new__(cls, content: str = ""):
        instance = super().__new__(cls, content)
        instance.type = URIType.UNKNOWN  # Initialize type attribute
        return instance

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

    @classmethod
    def validate(cls, value: str) -> "URI":
        """
        Validate that the URI is a valid URI, absolute, relative
        or a JSON pointer

        Args:
            value: The URI to validate

        Raises: ParseError
        """

        # The OAS standard is to use a fragment identifier
        # (https://www.rfc-editor.org/rfc/rfc6901#section-6) to indicate
        # that it is a JSON pointer per RFC 6901, e.g.
        # "$ref": "#/components/schemas/pet".
        # The hash does not indicate that the URI is a fragment.

        result: URI = cls(value)

        if result.startswith("#"):
            try:
                rfc6901.Rule("json-pointer").parse_all(result[1:])
            except ParseError:
                message = (
                    f"{value} is a fragment identifier but an invalid JSON pointer"
                )
                LogMixin.log(
                    Log(
                        message=message,
                        type=ValueError,
                        reference=reference,
                    )
                )
            # If the URI is a JSON pointer then there's no point testing
            # whether it's absolute or relative. A JSON pointer can't
            # have the type AnyUrl so return the string.
            result.type = URIType.JSON_POINTER
            return result

        try:
            # Prioritise validating the URI as absolute.
            rfc3986.Rule("URI").parse_all(result)
            result.type = URIType.ABSOLUTE
            return result
        except ParseError:
            pass

        try:
            # Using `relative-ref` to find authoratitive URIs
            # as the ABNF grammar doesn't directly index for
            # a URI of the form //authority/?guery or
            # //authority/#fragment.
            rfc3986.Rule("relative-ref").parse_all(result)

            # If the URI has an authority, it is not relative. Check
            # that next as the distinction is important in some cases.
            if result.startswith("//"):
                result.type = URIType.AUTHORITY
            else:
                result.type = URIType.RELATIVE
            return result
        except ParseError:
            LogMixin.log(
                Log(
                    message=f"{value} is not a valid URI",
                    type=ValueError,
                    reference=reference,
                )
            )

        result.type = URIType.UNKNOWN
        return result


class URIWithVariables(URI):
    """
    Defines a URI, and adds whether the URI is relative, absolute
    etc. The class allows for the type URI to be treated as if it
    were a string in calling Pydantic models. The URI can be of the
    form https://{username}.example.com/api/v1/{resource}, i.e. where
    some string interpolation is expected by software that will
    use this URI.
    """

    @classmethod
    def validate(cls, value: str) -> "URIWithVariables":
        """
        Validate that the URI is a valid URI with variables.
        e.g. of the form:

        https://{username}.example.com/api/v1/{resource}

        Args:
            value: The URI to validate

        Returns:
            The original value, if valid

        Raises:
            ParseError: If the URI is not valid
        """

        result: URIWithVariables = cls(value)
        result.type = URIType.UNKNOWN

        # Beautiful hack. `string.format()` takes a dict of the key, value pairs to
        # replace to replace the keys inside braces. As we don't have the keys a dict
        # that returns the keys that `string.format()` is expecting will have the
        # effect of replacing '{a}b{c} with 'abc'.
        class MissingKeyDict(dict[str, str]):
            def __missing__(self, key: str) -> str:
                return key

        # Unbalanced or embedded braces, e.g. /example/{id{a}}/ or /example/{id
        # will cause a ValueError in .format_map().
        try:
            intermediate = super().validate(result.format_map(MissingKeyDict()))
            result.type = intermediate.type
        except ValueError:
            message = "Unbalanced or embedded braces in URI"
            LogMixin.log(Log(message=message, type=ValueError, reference=reference))

        return result
