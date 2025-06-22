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
        "https://www.iana.org/assignments/http-authschemes/authschemes.csv",
        timeout=20,
    )
    response.raise_for_status()  # Raise an exception for HTTP errors

    reader = csv.DictReader(io.StringIO(response.text))

    data: list[dict[str, str]] = []

    for row in reader:
        data.append(row)

    write_to = (
        pathlib.Path(__file__).parent.parent.resolve() / "amati/data/iso9110.json"
    )

    with write_to.open("w") as f:
        f.write(json.dumps(data))
