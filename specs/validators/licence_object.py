"""
Validates the Open API Specification licence object: 
https://spec.openapis.org/oas/latest.html#license-object
"""

from typing import Optional

import pathlib
import warnings
import json

from typing_extensions import Self
from pydantic import AnyUrl, Field, field_validator, model_validator
from specs.warnings import InconsistencyWarning
from specs.validators.generic import GenericObject


DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / 'data'

with open(DATA_DIRECTORY / 'spdx-licences.json', 'r', encoding='utf-8') as f:
    data = json.loads(f.read())

# `seeAlso` is the list of URLs associated with each licence
VALID_LICENCES: dict[str, list[str]] = {
    licence['licenseId']: licence['seeAlso'] for licence in data['licenses']}
VALID_URLS: list[str] = [
    url for urls in VALID_LICENCES.values() for url in urls]


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
    @classmethod
    def check_identifier(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that the licence identifier is a valid SPDX licence.

        Args:
            v (Optional[str]): The licence identifier to validate

        Returns:
            Optional[str]: The validated licence identifier or None if not provided

        Raises:
            ValueError: If the identifier is not a valid SPDX licence
        """
        if v is None:
            return None
        if v not in VALID_LICENCES:
            raise ValueError(f"{v} is not a valid SPDX licence.")
        return v

    @field_validator("url")
    @classmethod
    def check_url(cls, v: Optional[AnyUrl]) -> Optional[AnyUrl]:
        """
        Validate that the licence URL exists in the list of known SPDX licence URLs.

        Args:
            v (Optional[AnyUrl]): The URL to validate

        Returns:
            Optional[AnyUrl]: The validated URL or None if not provided

        Warns:
            InconsistencyWarning: If the URL is not associated with any known licence
        """
        if v is None: 
            return None
        if v == []:
            return None

        if str(v) in VALID_URLS:
            return v

        warnings.warn(
            f"{v} is not associated with any identifier.", InconsistencyWarning)

        return None

    @model_validator(mode="after")
    def check_url_associated_with_identifier(self: Self) -> Self:
        """
        Validate that the URL matches the provided licence identifier.

        This validator checks if the URL is listed among the known URLs for the 
        specified licence identifier.

        Returns:
            Self: The validated licence object

        Warns:
            InconsistencyWarning: If the URL doesn't match the specified identifier
        """
        if self.url is None:
            return self

        if self.identifier is not None:
            # The list of URLs associated with the licence is not empty
            if VALID_LICENCES[self.identifier]:
                if str(self.url) not in VALID_LICENCES[self.identifier]:
                    warnings.warn(
                        f"{self.url} is not associated with the identifier {self.identifier}",
                        InconsistencyWarning)
        return self
