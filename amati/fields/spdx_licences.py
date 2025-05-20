"""
Validates the idenfitier and licences from the System Package Data
Exchange (SPDX) licence list.
"""

import json
import pathlib

from amati import AmatiValueError, Reference
from amati.fields import URI, _Str

reference = Reference(
    title="SPDX License List",
    url="https://spdx.org/licenses/",
)


DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "spdx-licences.json", "r", encoding="utf-8") as f:
    data = json.loads(f.read())

# `seeAlso` is the list of URLs associated with each licence
VALID_LICENCES: dict[str, list[str]] = {
    licence["licenseId"]: licence["seeAlso"] for licence in data["licenses"]
}
VALID_URLS: list[str] = [url for urls in VALID_LICENCES.values() for url in urls]


class SPDXIdentifier(_Str):

    def __init__(self, value: str):

        if value not in VALID_LICENCES:
            raise AmatiValueError(
                f"{value} is not a valid SPDX licence identifier", reference=reference
            )


class SPDXURL(URI):  # pylint: disable=invalid-name

    def __init__(self, value: str):

        super().__init__(value)

        if value not in VALID_URLS:
            raise AmatiValueError(
                f"{value} is not associated with any identifier.", reference=reference
            )
