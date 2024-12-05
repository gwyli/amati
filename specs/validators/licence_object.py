from pydantic import AnyUrl, Field, field_validator, model_validator

from typing import Optional
from typing_extensions import Self

from specs.warnings import InconsistencyWarning
from specs.validators.generic import GenericObject

import pathlib
import warnings
import json

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / 'data'

with open(DATA_DIRECTORY / 'spdx-licences.json') as f:
    data = json.loads(f.read())

# `seeAlso` is the list of URLs associated with each licence
VALID_LICENCES = {licence['licenseId'] : [AnyUrl(url) for url in licence['seeAlso']]
                  for licence in data['licenses']}
VALID_URLS = [AnyUrl(url) for urls in VALID_LICENCES.values() for url in urls]


class LicenceObject(GenericObject):
    """
    A model representing the Open API Specification licence object:
     https://spec.openapis.org/oas/latest.html#license-object

    Attributes:
        name (str): The name of the licence.
        identifier (Optional[str]): The SPDX identifier of the licence.
        url (Optional[AnyUrl]): The URL associated with the licence.

    Methods:
        check_identifier(cls, v: str) -> str:
            Validates that the identifier is a valid SPDX licence.

        check_url_associated_with_identifier(self: Self) -> Self:
            Validates that the URL is associated with the identifier.
    """
    
    name: str = Field(min_length=1)
    # What difference does Optional make here?
    identifier: Optional[str] = None
    url: Optional[AnyUrl] = None

    @field_validator("identifier")
    def check_identifier(cls, v: Optional[str]) -> Optional[str]:
        if v is None: return None
        if v not in VALID_LICENCES:
            raise ValueError(f"{v} is not a valid SPDX licence.")
        return v
    
    @field_validator("url")
    def check_url(cls, v: Optional[AnyUrl]) -> Optional[AnyUrl]:
        if v is None: return None
        if v == []: return None
    
        if v in VALID_URLS: 
            return v
        else:
            warnings.warn(f"{v} is not associated with any identifier.", InconsistencyWarning)
    
    @model_validator(mode="after")
    def check_url_associated_with_identifier(self: Self) -> Self:

        if self.url is None: return self

        if self.identifier is not None:
            # The list of URLs associated with the licence is not empty
            if VALID_LICENCES[self.identifier]:
                if self.url not in VALID_LICENCES[self.identifier]:
                    warnings.warn(f"{self.url} is not associated with the identifier {self.identifier}.", InconsistencyWarning)
        
        return self