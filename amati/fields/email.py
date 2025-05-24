"""
Validates an email according to the RFC5322 ABNF grammar - §3:
"""

from abnf import ParseError
from abnf.grammars import rfc5322

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str

reference = Reference(
    title="Internet Message Format",
    url="https://www.rfc-editor.org/rfc/rfc5322#section-3",
    section="Syntax",
)


class Email(_Str):

    def __init__(self, value: str):

        try:
            rfc5322.Rule("address").parse_all(value)
        except ParseError as e:
            raise AmatiValueError(
                message=f"{value} is not a valid email address", reference=reference
            ) from e
