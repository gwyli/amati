import csv
import io
from pathlib import Path

import requests

DATA_FILE = Path("iso9110.json")
DATA_SOURCE = "https://www.iana.org/assignments/http-authschemes/authschemes.csv"


def get() -> list[dict[str, str]]:
    """Downloads the HTTP Authentication Scheme Registry from IANA and saves it as
    a JSON file.
    """
    response = requests.get(DATA_SOURCE, timeout=20)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))

    data: list[dict[str, str]] = []

    for row in reader:
        data.append(row)

    return data
