from typing import Optional

from pydantic import AnyUrl

from amati.fields.email import Email
from amati.validators import title
from amati.validators.reference_object import Reference, ReferenceModel
from amati.validators.generic import GenericObject


class ContactObject(GenericObject):
    """
    Validates the Open API Specification contact object - §4.8.3
    """
    name: Optional[str] = None
    url: Optional[AnyUrl] = None
    email: Optional[Email] = None
    _reference: Reference =  ReferenceModel( # type: ignore
        title=title,
        url='https://spec.openapis.org/oas/latest.html#contact-object',
        section='Contact Object'
        )
