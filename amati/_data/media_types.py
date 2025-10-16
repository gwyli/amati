import csv
import io
from pathlib import Path

import requests

DATA_FILE = Path("media-types.json")
DATA_SOURCE: dict[str, str] = {
    "application": "https://www.iana.org/assignments/media-types/application.csv",
    "audio": "https://www.iana.org/assignments/media-types/audio.csv",
    # "example": "currently no valid values", # noqa ERA001
    "font": "https://www.iana.org/assignments/media-types/font.csv",
    "haptics": "https://www.iana.org/assignments/media-types/haptics.csv",
    "image": "https://www.iana.org/assignments/media-types/image.csv",
    "message": "https://www.iana.org/assignments/media-types/message.csv",
    "model": "https://www.iana.org/assignments/media-types/model.csv",
    "multipart": "https://www.iana.org/assignments/media-types/multipart.csv",
    "text": "https://www.iana.org/assignments/media-types/text.csv",
    "video": "https://www.iana.org/assignments/media-types/video.csv",
}


def get() -> dict[str, list[str]]:
    """Downloads the HTTP Authentication Schemes (ISO 9110) from IANA and saves
    it as a JSON file.
    """

    # Example has no valid values at the moment
    data: dict[str, list[str]] = {"example": []}

    for registry, file in DATA_SOURCE.items():
        response = requests.get(file, timeout=20)
        response.raise_for_status()

        reader = csv.DictReader(io.StringIO(response.text))

        data[registry] = []

        for row in reader:
            data[registry].append(row["Name"])

    return data
