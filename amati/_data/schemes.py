import csv
import io
from pathlib import Path

import requests

DATA_FILE = Path("schemes.json")
DATA_SOURCE = "https://www.iana.org/assignments/uri-schemes/uri-schemes-1.csv"


def get() -> dict[str, str]:
    """Downloads the URI Schemes Registry from IANA and saves it as a JSON file."""
    response = requests.get(DATA_SOURCE, timeout=20)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))

    data: dict[str, str] = {}

    for row in reader:
        data[row["URI Scheme"]] = row["Status"]

    return data
