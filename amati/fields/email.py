"""
Validates an email according to the RFC5322 ABNF grammar - §3:
"""

from abnf import ParseError
from abnf.grammars import rfc5322

from amati import AmatiValueError
from amati.fields import Str as _Str

reference_uri = "https://www.rfc-editor.org/rfc/rfc5322#section-3"


class Email(_Str):
    """A string subclass representing a validated RFC 5322 email address.

    This class ensures that email addresses conform to the RFC 5322 specification
    by validating the input during initialization. Invalid addresses raise an
    AmatiValueError.

    Args:
        value: The email address string to validate.

    Raises:
        AmatiValueError: If the value is not a valid RFC 5322 email address.

    Example:
        >>> email = Email("user@example.com")
        >>> invalid = Email("not-an-email")
        Traceback (most recent call last):
        amati.exceptions.AmatiValueError: message
    """

    def __init__(self, value: str):
        try:
            rfc5322.Rule("address").parse_all(value)
        except ParseError as e:
            raise AmatiValueError(
                f"{value} is not a valid email address", reference_uri
            ) from e
