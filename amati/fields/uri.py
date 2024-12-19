"""
Validates a URI according to the RFC3986 ABNF grammar
"""

from typing import Annotated, Union

from abnf import ParseError
from abnf.grammars import rfc3986
from pydantic import AfterValidator, AnyUrl

from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title="Uniform Resource Identifier (URI): Generic Syntax",
    url="https://datatracker.ietf.org/doc/html/rfc3986#appendix-A",
    section="Appendix A",
)


def _validate_after_relative(value: str | AnyUrl) -> str:
    """
    Validate that the URI is a valid relative URI.

    Args:
        value: The URI to validate

    Returns:
        The original value

    Notes:
        Logs if the URI is relative
    """

    return rfc3986.Rule("relative-ref").parse_all(str(value)).value


def _validate_after_absolute(value: AnyUrl | str) -> AnyUrl:
    """
    Validate that the URI is a valid absolute URI.

    Args:
        value: The URI to validate
    """
    uri = rfc3986.Rule("URI").parse_all(str(value))

    return AnyUrl(uri.value)


def _validate_after(value: AnyUrl | str) -> AnyUrl | str:
    """
    Validate that the URI is a valid URI.

    Args:
        value: The URI to validate

    Raises: ParseError
    """
    try:
        return _validate_after_absolute(value)
    except ParseError:
        # If the URI is neither absolute or relative then raise an error
        return _validate_after_relative(value)


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

    count = 0

    for char in value:
        if char == "{":
            if count > 0:  # Already have an opening brace
                raise ValueError("Opening brace inside opening brace")
            count += 1
        elif char == "}":
            if count == 0:  # Closing brace without opening brace
                raise ValueError("No closing brace")
            count -= 1

    if count != 0:  # Check for any unmatched opening braces
        raise ValueError("Unmatched opening brace")

    # Beautiful hack. `string.format()` takes a dict of the key, value pairs to replace
    # to replace the keys inside braces. As we don't have the keys a dict that returns
    # the keys that `string.format()` is expecting will have the effect of replacing
    # '{a}b{c} with 'abc'.
    class MissingKeyDict(dict[str, str]):
        def __missing__(self, key: str) -> str:
            return key

    uri: URI = value.format_map(MissingKeyDict())
    _validate_after(uri)

    return value


AbsoluteURI = Annotated[AnyUrl | str, AfterValidator(_validate_after_absolute)]

RelativeURI = Annotated[str, AfterValidator(_validate_after_relative)]

URI = Annotated[Union[AbsoluteURI, RelativeURI], AfterValidator(_validate_after)]

URIWithVariables = Annotated[str, AfterValidator(_validate_after_uri_with_variables)]
