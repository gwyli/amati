"""
Validates an email according to the RFC5322 ABNF grammar - §3:
"""

from typing import Annotated, Optional

from abnf.grammars import rfc5322
from pydantic import AfterValidator

from amati.validators.reference_object import Reference, ReferenceModel


reference: Reference = ReferenceModel(
    title='Internet Message Format',
    url='https://www.rfc-editor.org/rfc/rfc5322#section-3',
    section='Syntax'
)


def _validate_after_email(value: str) -> str:
    """
    Validate that the email address is a valid email address.

    Args:
        value: The email address to validate
    
    Raises:
        ParseError: If the email address does not conform to RFC5322 ABNF grammar
    """

    return rfc5322.Rule('address').parse_all(value).value


Email = Annotated[
    Optional[str],
    AfterValidator(_validate_after_email)
]
