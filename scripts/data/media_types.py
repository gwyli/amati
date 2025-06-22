"""
Script to download the HTTP Authentication Schemes (ISO 9110) from IANA
"""

import csv
import io
import json
import pathlib

import requests

if __name__ == "__main__":

    raw_data: dict[str, str] = {
        "application": "https://www.iana.org/assignments/media-types/application.csv",
        "audio": "https://www.iana.org/assignments/media-types/audio.csv",
        # "example":
        "font": "https://www.iana.org/assignments/media-types/font.csv",
        "haptics": "https://www.iana.org/assignments/media-types/haptics.csv",
        "image": "https://www.iana.org/assignments/media-types/image.csv",
        "message": "https://www.iana.org/assignments/media-types/message.csv",
        "model": "https://www.iana.org/assignments/media-types/model.csv",
        "multipart": "https://www.iana.org/assignments/media-types/multipart.csv",
        "text": "https://www.iana.org/assignments/media-types/text.csv",
        "video": "https://www.iana.org/assignments/media-types/video.csv",
    }

    # Example has no valid values at the moment
    data: dict[str, list[str]] = {"example": []}

    for registry, file in raw_data.items():
        response = requests.get(
            file,
            timeout=20,
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        reader = csv.DictReader(io.StringIO(response.text))

        data[registry] = []

        for row in reader:
            data[registry].append(row["Name"])

    write_to = (
        pathlib.Path(__file__).parent.parent.resolve() / "amati/data/media-types.json"
    )

    with write_to.open("w") as f:
        f.write(json.dumps(data))
