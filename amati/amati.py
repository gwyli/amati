"""
High-level access to amati functionality.
"""

import importlib
import json
import sys
from pathlib import Path

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from amati._resolve_forward_references import (  # pylint: disable=wrong-import-position
    resolve_forward_references,
)
from amati.file_handler import load_file  # pylint: disable=wrong-import-position
from amati.logging import Log, LogMixin  # pylint: disable=wrong-import-position

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


def dispatch(data: JSONObject) -> BaseModel:
    """
    Returns the correct model for the passed spec

    Args:
        data: A dictionary representing an OpenAPI specification

    Returns:
        A pydantic model representing the API specification
    """

    version: JSONValue | None = data.get("openapi")

    if not isinstance(version, str):
        raise ValueError("A OpenAPI specification version must be a string.")

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


def validate(original: JSONObject, validated: BaseModel) -> bool:
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

    data = load_file(file_path)

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
