"""
Script to download the Hypertext Transfer Protocol (HTTP) Status Code Registry from IANA
"""

import csv
import io
import json
import pathlib
import re

import requests

if __name__ == "__main__":
    response = requests.get(
        "https://www.iana.org/assignments/http-status-codes/http-status-codes-1.csv",
        timeout=20,
    )

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

    write_to = (
        pathlib.Path(__file__).parent.parent.resolve()
        / "amati/data/http-status-codes.json"
    )

    with write_to.open("w") as f:
        f.write(json.dumps(data))
