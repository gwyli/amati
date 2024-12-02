from pydantic import BaseModel, AnyUrl, Field, field_validator, model_validator

from typing import Optional
from typing_extensions import Self

from specs import helpers
from specs.warnings import InconsistencyWarning

import warnings
import json

with open(helpers.ROOT_DIR / 'data/spdx-licences.json') as f:
    data = json.loads(f.read())

# `seeAlso` is a list of URLs associated with the licence
VALID_LICENCES = {licence['licenseId'] : licence['seeAlso'] for licence in data['licenses']}


class LicenceObject(BaseModel):
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
    def check_identifier(cls, v: str) -> str:
        if v is None: return None
        if v not in VALID_LICENCES:
            raise ValueError(f"{v} is not a valid SPDX licence.")
        return v
    
    @model_validator(mode="after")
    def check_url_associated_with_identifier(self: Self) -> Self:
        if self.identifier is not None and self.url is not None:
            if self.url not in VALID_LICENCES[self.identifier]:
                warnings.warn(f"URL {self.url} is not associated with the identifier {self.identifier}.", InconsistencyWarning)
        elif self.url is not None:
            for value in VALID_LICENCES.values():
                if self.url in value:
                    return self
            warnings.warn(f"URL {self.url} is not associated with any identifier.", InconsistencyWarning)
        return self