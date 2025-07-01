import csv
import io
import re
from pathlib import Path

import requests

DATA_FILE = Path("http-status-codes.json")
DATA_SOURCE = (
    "https://www.iana.org/assignments/http-status-codes/http-status-codes-1.csv"
)


def get() -> dict[str, str]:
    """Downloads the HTTP Status Code Registry from IANA and saves it as a JSON file."""
    response = requests.get(DATA_SOURCE, timeout=20)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))

    data: dict[str, str] = {}
    pattern = re.compile(r"^(\d{3})-*(\d{3})$")

    for row in reader:
        if match := pattern.match(row["Value"]):
            start, stop = match.groups()
            for value in range(int(start), int(stop) + 1):
                data[str(value)] = row["Description"]
        else:
            data[row["Value"]] = row["Description"]

    return data
