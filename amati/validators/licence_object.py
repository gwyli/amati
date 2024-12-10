"""
Validates the Open API Specification licence object - §4.8.4.
"""

import json
import pathlib
from typing import Annotated, Optional
from typing_extensions import Self

from pydantic import AfterValidator, AnyUrl, Field, model_validator

from amati.validators import title
from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject
from amati.validators.reference_object import Reference, ReferenceModel

oas_reference: Reference = ReferenceModel(
    title=title,
    url='https://spec.openapis.org/oas/v3.1.1.html#license-object',
    section='License Object'
)

spdx_reference: Reference = ReferenceModel(
    title='SPDX License List',
    url='https://spdx.org/licenses/',
)

references: Reference = [oas_reference, spdx_reference]


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
        LogMixin.log(Log(f'{value} is not a valid SPDX licence identifier.', Warning, spdx_reference))

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

    LogMixin.log(Log(f'{value} is not associated with any identifier.', Warning, spdx_reference))

    return value


SPDXURL = Annotated[
    Optional[AnyUrl],
    AfterValidator(_validate_after_spdx_url)
]


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
    _reference: Reference = references # type: ignore

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
