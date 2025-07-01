from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_FILE = Path("tlds.json")
DATA_SOURCE = "https://www.iana.org/domains/root/db"


def get() -> list[str]:
    """Downloads the TLD list from IANA and saves it as a JSON file."""
    response = requests.get(DATA_SOURCE, timeout=20)
    response.raise_for_status()

    data: list[str] = []

    soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", id="tld-table")

    for row in table.find_all("tr")[1:]:  # type: ignore # Skip the header row
        data.append(row.find_all("td")[0].text.strip())  # type: ignore

    return data
