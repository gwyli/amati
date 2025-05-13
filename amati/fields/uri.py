"""
Validates a URI according to the RFC3986 ABNF grammar
"""

from typing import Annotated

from abnf import ParseError
from abnf.grammars import rfc3986
from pydantic import AfterValidator, AnyUrl

from amati.grammars import rfc6901
from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title="Uniform Resource Identifier (URI): Generic Syntax",
    url="https://datatracker.ietf.org/doc/html/rfc3986#appendix-A",
    section="Appendix A",
)


def _validate_after(value: AnyUrl | str) -> AnyUrl | str:
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

    value_: str = str(value)

    if value_.startswith("#"):
        try:
            rfc6901.Rule("json-pointer").parse_all(value_[1:])
        except ParseError:
            message = f"{value} is a fragment identifier but an invalid JSON pointer"
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
        return value_

    try:
        # Prioritise validating the URI as absolute.
        return AnyUrl(rfc3986.Rule("URI").parse_all(value_).value)
    except ParseError:
        pass

    try:
        return rfc3986.Rule("relative-ref").parse_all(value_).value
    except ParseError:
        LogMixin.log(
            Log(
                message=f"{value} is not a valid URI",
                type=ValueError,
                reference=reference,
            )
        )
    return value


def _validate_after_uri_with_variables(value: str) -> str:
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

    # Beautiful hack. `string.format()` takes a dict of the key, value pairs to replace
    # to replace the keys inside braces. As we don't have the keys a dict that returns
    # the keys that `string.format()` is expecting will have the effect of replacing
    # '{a}b{c} with 'abc'.
    class MissingKeyDict(dict[str, str]):
        def __missing__(self, key: str) -> str:
            return key

    # Unbalanced or embedded braces, e.g. /example/{id{a}}/ or /example/{id
    # will cause a ValueError in .format_map().
    try:
        uri: URI = value.format_map(MissingKeyDict())
        _validate_after(uri)
    except ValueError:
        message = "Unbalanced or embedded braces in URI"
        LogMixin.log(Log(message=message, type=ValueError, reference=reference))

    return value


type URI = Annotated[  # pylint: disable=invalid-name
    AnyUrl | str, AfterValidator(_validate_after)
]

type URIWithVariables = Annotated[
    str, AfterValidator(_validate_after_uri_with_variables)
]
