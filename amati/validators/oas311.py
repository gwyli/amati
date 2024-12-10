from typing import Optional
from typing_extensions import Self

from pydantic import AnyUrl, Field, model_validator

from amati.logging import Log, LogMixin
from amati.fields.email import Email
from amati.fields.spdx_licences import SPDXIdentifier, SPDXURL, VALID_LICENCES
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
    
class LicenceObject(GenericObject):
    """
    A model representing the Open API Specification licence object
     
    OAS uses the SPDX licence list

    Args:
        name: The name of the licence
        identifier: The SPDX identifier of the licence
        url: The URL associated with the licence
    """

    name: str = Field(min_length=1)
    # What difference does Optional make here?
    identifier: SPDXIdentifier = None
    url: SPDXURL = None
    _reference: Reference = ReferenceModel( # type: ignore
        title=title,
        url='https://spec.openapis.org/oas/v3.1.1.html#license-object',
        section='License Object'
        ) 

    @model_validator(mode='after')
    def check_url_associated_with_identifier(self: Self) -> Self:
        """
        Validate that the URL matches the provided licence identifier.

        This validator checks if the URL is listed among the known URLs for the 
        specified licence identifier.

        Returns:
            The validated licence object
        """
        if self.url is None:
            return self

        # Checked in the type AfterValidator, not necessary to raise a warning here.
        # only done to avoid an unnecessary KeyError
        if self.identifier not in VALID_LICENCES:
            return self

        if str(self.url) not in VALID_LICENCES[self.identifier]:
            LogMixin.log(Log(f'{self.url} is not associated with the identifier {self.identifier}', Warning, self._reference))

        return self

