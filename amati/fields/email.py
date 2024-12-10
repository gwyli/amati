"""
Validates the Open API Specification contact object - §4.8.3
"""

from typing import Annotated, Optional

from abnf.grammars import rfc5322
from pydantic import AfterValidator, AnyUrl

from amati.validators import title
from amati.validators.reference_object import Reference, ReferenceModel
from amati.validators.generic import GenericObject


reference: Reference = ReferenceModel(
    title=title,
    url='https://spec.openapis.org/oas/latest.html#contact-object',
    section='Contact Object'
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

class ContactObject(GenericObject):
    name: Optional[str] = None
    url: Optional[AnyUrl] = None
    email: Optional[Email] = None
    _reference: Reference =  reference # type: ignore
