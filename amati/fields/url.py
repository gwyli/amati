"""
Validates a URL according to the RFC3986 ABNF grammar
"""

from typing import Annotated, Union

from abnf import ParseError
from abnf.grammars import rfc3986
from pydantic import AfterValidator, AnyUrl

from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title='Uniform Resource Identifier (URI): Generic Syntax',
    url='https://datatracker.ietf.org/doc/html/rfc3986#appendix-A',
    section='Appendix A'
)

def _validate_after_relative(value: str|AnyUrl) -> str:
    """
    Validate that the URL is a valid relative URL.

    Args:
        value: The URL to validate
    
    Returns:
        The original value
        
    Notes:
        Logs if the URL is relative
    """

    return rfc3986.Rule('relative-ref').parse_all(str(value)).value


def _validate_after_absolute(value: AnyUrl|str) -> AnyUrl:
    """
    Validate that the URL is a valid absolute URL.

    Args:
        value: The URL to validate
    """
    uri = rfc3986.Rule('URI').parse_all(str(value))

    return AnyUrl(uri.value)


def _validate_after(value: AnyUrl|str) -> AnyUrl|str:
    """
    Validate that the URL is a valid URL.

    Args:
        value: The URL to validate
        
    Raises: ParseError
    """
    try:
        return _validate_after_absolute(value)
    except ParseError:
        pass

    # If the URI is neither absolute or relative then raise an error
    return _validate_after_relative(value)


def _validate_after_url_with_variables(value: str) -> str:
    """
    Validate that the URL is a valid URL with variables.
    e.g. of the form:
    
    https://{username}.example.com/api/v1/{resource}

    Args:
        value: The URL to validate
    
    Returns:
        The original value, if valid
    
    Raises:
        ParseError: If the URL is not valid
    """

    count = 0

    for char in value:
        if char == '{':
            if count > 0:  # Already have an opening brace
                raise ValueError('Opening brace inside opening brace')
            count += 1
        elif char == '}':
            if count == 0:  # Closing brace without opening brace
                raise ValueError('No closing brace')
            count -= 1

    if count != 0: # Check for any unmatched opening braces
        raise ValueError('Unmatched opening brace')

    # Beautiful hack. `string.format()` takes a dict of the key, value pairs to replace
    # to replace the keys inside braces. As we don't have the keys a dict that returns
    # the keys that `string.format()` is expecting will have the effect of replacing
    # '{a}b{c} with 'abc'.
    class MissingKeyDict(dict[str, str]):
        def __missing__(self, key: str) -> str:
            return key

    url: URL = value.format_map(MissingKeyDict())

    return url


AbsoluteURL = Annotated[AnyUrl | str, AfterValidator(_validate_after_absolute)]

RelativeURL = Annotated[str, AfterValidator(_validate_after_relative)]

URL = Annotated[Union[AbsoluteURL, RelativeURL], AfterValidator(_validate_after)]

URLWithVariables = Annotated[str, AfterValidator(_validate_after_url_with_variables)]
