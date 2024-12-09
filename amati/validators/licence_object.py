"""
Validates the Open API Specification licence object - §4.8.4: 
https://spec.openapis.org/oas/latest.html#license-object
"""

import json
import pathlib
from typing import Annotated, Optional

from pydantic import AfterValidator, AnyUrl, Field, model_validator
from typing_extensions import Self

from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / 'data'

with open(DATA_DIRECTORY / 'spdx-licences.json', 'r', encoding='utf-8') as f:
    data = json.loads(f.read())

# `seeAlso` is the list of URLs associated with each licence
VALID_LICENCES: dict[str, list[str]] = {
    licence['licenseId']: licence['seeAlso'] for licence in data['licenses']}
VALID_URLS: list[str] = [
    url for urls in VALID_LICENCES.values() for url in urls]


def _validate_after_spdx_identifier(value: Optional[str]) -> Optional[str]:
    """
    Validate that the licence identifier is a valid SPDX licence.

    Args:
        v: The licence identifier to validate

    Returns:
        The validated licence identifier or None if not provided

    Raises:
        ValueError: If the identifier is not a valid SPDX licence
    """
    if value is None: return None
    if value not in VALID_LICENCES: 
        LogMixin.log(Log(f'{value} is not a valid SPDX licence identifier.', Warning))

    return value


SPDXIdentifier = Annotated[
    Optional[str],
    AfterValidator(_validate_after_spdx_identifier)
]


def _validate_after_spdx_url(value: Optional[AnyUrl]) -> Optional[AnyUrl]:
    """
    Validate that the licence URL exists in the list of known SPDX licence URLs.
    Not that the URL is associated with the specific identifier.

    Args:
        v: The URL to validate

    Returns:
        The validated URL or None if not provided

    Warns:
        InconsistencyWarning: If the URL is not associated with any known licence.
    """
    if value is None: return None
    if str(value) in VALID_URLS: return value

    LogMixin.log(Log(f'{value} is not associated with any identifier.', Warning))

    return value


SPDXURL = Annotated[
    Optional[AnyUrl],
    AfterValidator(_validate_after_spdx_url)
]


class LicenceObject(GenericObject):
    """
    A model representing the Open API Specification licence object:
     https://spec.openapis.org/oas/latest.html#license-object
     
    OAS uses the SPDX licence list: https://spdx.org/licenses/

    Args:
        name: The name of the licence
        identifier: The SPDX identifier of the licence
        url: The URL associated with the licence
    """

    name: str = Field(min_length=1)
    # What difference does Optional make here?
    identifier: SPDXIdentifier = None
    url: SPDXURL = None

    @model_validator(mode='after')
    def check_url_associated_with_identifier(self: Self) -> Self:
        """
        Validate that the URL matches the provided licence identifier.

        This validator checks if the URL is listed among the known URLs for the 
        specified licence identifier.

        Returns:
            The validated licence object

        Warns:
            InconsistencyWarning: If the URL doesn't match the specified identifier
        """
        if self.url is None or self.identifier is None:
            return self

        if self.identifier in VALID_LICENCES:
            # The list of URLs associated with the licence is not empty
            if VALID_LICENCES[self.identifier]:
                if str(self.url) not in VALID_LICENCES[self.identifier]:
                    LogMixin.log(Log(f'{self.url} is not associated with the identifier {self.identifier}', Warning))

        return self
