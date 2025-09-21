import json
from pathlib import Path
from typing import Any

import requests

DATA_FILE = Path("spdx-licences.json")
DATA_SOURCE = "https://raw.githubusercontent.com/spdx/license-list-data/refs/heads/main/json/licenses.json"


def get() -> Any:
    """Downloads the SPDX licence list from GitHub and saves it as a JSON file."""
    response = requests.get(DATA_SOURCE, timeout=20)
    response.raise_for_status()

    # Removes licenseListVersion
    data = json.loads(json.dumps(response.json()))["licenses"]

    # The reference number keeps changing
    for item in data:
        item.pop("referenceNumber")

    return data
