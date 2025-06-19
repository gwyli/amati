"""
High-level access to amati functionality.
"""

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from amati._resolve_forward_references import (  # pylint: disable=wrong-import-position
    resolve_forward_references,
)
from amati.logging import Log, LogMixin  # pylint: disable=wrong-import-position


def file_handler(file: Path) -> dict[str, Any]:
    """
    Creates a format suitable for Amati from a provided file.

    Args:
        file: An existing file in a Path

    Returns:
        A dict suitable to be used by Amati

    Raises:
        ValueError: If the file does not exist or is not a valid type
    """

    if not file.exists():
        raise ValueError(f"{file} does not exist")

    if file.suffix in (".yaml", ".yml"):
        with open(file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    if file.suffix == ".json":
        with open(file, "r", encoding="utf-8") as f:
            return json.loads(f.read())

    raise ValueError(f"{file} is not a JSON or YAML file")


def dispatch(data: dict[str, Any]) -> BaseModel:
    """
    Returns the correct model for the passed spec

    Args:
        data: A dictionary representing an OpenAPI specification

    Returns:
        A pydantic model representing the API specification
    """

    version: str | None = data.get("openapi")

    if not version:
        raise ValueError("An OpenAPI Specfication must contain a version.")

    version_map: dict[str, str] = {
        "3.1.1": "311",
        "3.1.0": "311",
        "3.0.4": "304",
        "3.0.3": "304",
        "3.0.2": "304",
        "3.0.1": "304",
        "3.0.0": "304",
    }

    module = importlib.import_module(f"amati.validators.oas{version_map[version]}")

    resolve_forward_references(module)

    try:
        model = module.OpenAPIObject(**data)
    except Exception as e:
        LogMixin.log(Log(message=e.args[1], type=e.args[0]))
        raise

    return model


def validate(original: dict[str, Any], validated: BaseModel) -> bool:
    """
    Confirms whether a Pydantic model is the same a a dictionary.

    Args:
        original: The dictionary representation of the original file
        validated: A Pydantic model representing the original file

    Returns:
        Whether original and validated are the same.
    """

    original_ = json.dumps(original, sort_keys=True)

    json_dump = validated.model_dump_json(exclude_unset=True, by_alias=True)
    new_ = json.dumps(json.loads(json_dump), sort_keys=True)

    return original_ == new_


def run(file_path: str):

    file = Path(file_path)

    data = file_handler(file)

    model = dispatch(data)

    print(validate(data, model))
    print(LogMixin.logs)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        prog="amati",
        description="Test whether a OpenAPI specification is valid.",
    )

    parser.add_argument(
        "-s", "--spec", required=True, help="The specification to be parsed"
    )

    args = parser.parse_args()

    run(args.spec)
