"""
Script to download the HTTP Authentication Schemes (ISO 9110) from IANA
"""

import csv
import io
import json
import pathlib

import requests

if __name__ == "__main__":
    response = requests.get(
        "https://www.iana.org/assignments/uri-schemes/uri-schemes-1.csv",
        timeout=20,
    )
    response.raise_for_status()  # Raise an exception for HTTP errors

    reader = csv.DictReader(io.StringIO(response.text))

    data: dict[str, str] = {}

    for row in reader:
        data[row["URI Scheme"]] = row["Status"]

    write_to = (
        pathlib.Path(__file__).parent.parent.resolve() / "amati/data/schemes.json"
    )

    with write_to.open("w") as f:
        f.write(json.dumps(data))
