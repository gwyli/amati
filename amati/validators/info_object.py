"""
Validates the Open API Specification info object - §4.8.2:
https://spec.openapis.org/oas/latest.html#info-object
"""

from typing import Optional

from amati.validators.contact_object import ContactObject
from amati.validators.generic import GenericObject
from amati.validators.licence_object import LicenceObject

class InfoObject(GenericObject):
    title: str
    summary: Optional[str] = None
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenceObject] = None
    version: str
