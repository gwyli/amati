"""
Script to download the HTTP Authentication Schemes (ISO 9110) from IANA
"""

import json
import pathlib

import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    response = requests.get(
        "https://www.iana.org/domains/root/db",
        timeout=20,
    )
    response.raise_for_status()  # Raise an exception for HTTP errors

    data: list[str] = []

    soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", id="tld-table")

    for row in table.find_all("tr")[1:]:  # type: ignore # Skip the header row
        data.append(row.find_all("td")[0].text.strip())  # type: ignore

    write_to = pathlib.Path(__file__).parent.parent.resolve() / "amati/data/tlds.json"

    with write_to.open("w") as f:
        f.write(json.dumps(data))
