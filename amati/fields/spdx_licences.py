"""
Validates the Open API Specification licence object - §4.8.4.
"""

import json
import pathlib
from typing import Annotated, Optional

from pydantic import AfterValidator, AnyUrl

from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference, ReferenceModel


spdx_reference: Reference = ReferenceModel(
    title='SPDX License List',
    url='https://spdx.org/licenses/',
)


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


