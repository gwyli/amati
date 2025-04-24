"""
Validates the Hypertext Transfer Protocol (HTTP) Authentication Scheme Registry
(ISO 9110, section 16.4.1) from IANA.
"""

import json
import pathlib
from typing import Annotated, Optional

from pydantic import AfterValidator

from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title="Hypertext Transfer Protocol (HTTP) Authentication Scheme Registry (ISO9110)",
    url="https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml",
)


DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "iso9110.json", "r", encoding="utf-8") as f:
    data = json.loads(f.read())


HTTP_AUTHENTICATION_SCHEMES: set[str] = set(
    [x["Authentication Scheme Name"] for x in data]
)


def _validate_after(value: Optional[str]) -> Optional[str]:
    """
    Validate the HTTP authentication scheme exists in ISO 9110.

    Args:
        v: The authentication scheme to validate

    Returns:
        The validated authentication scheme or None if not provided

    Raises:
        ValueError: If the identifier is not a valid authentication scheme
    """
    if value is None:
        return None

    if value not in HTTP_AUTHENTICATION_SCHEMES:
        message = f"{value} is not a valid HTTP authentication schema."
        LogMixin.log(Log(message=message, type=ValueError, reference=reference))

    return value


HTTPAuthenticationScheme = Annotated[Optional[str], AfterValidator(_validate_after)]
