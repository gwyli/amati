"""
High-level access to amati functionality.
"""

import importlib
import json
import sys
from pathlib import Path

import jsonpickle
from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

# pylint: disable=wrong-import-position

sys.path.insert(0, str(Path(__file__).parent.parent))
from amati._resolve_forward_references import resolve_forward_references
from amati.file_handler import load_file

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


def dispatch(data: JSONObject) -> tuple[BaseModel | None, list[ErrorDetails] | None]:
    """
    Returns the correct model for the passed spec

    Args:
        data: A dictionary representing an OpenAPI specification

    Returns:
        A pydantic model representing the API specification
    """

    version: JSONValue = data.get("openapi")

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
    except ValidationError as e:
        return None, e.errors()

    return model, None


def check(original: JSONObject, validated: BaseModel) -> bool:
    """
    Runs a consistency check on the output of amati.
    Determines whether the validated model is the same as the
    originally provided API Specification

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


def run(file_path: str, consistency_check: bool = False, store_errors: bool = False):
    """
    Runs the full amati process
    """

    data = load_file(file_path)

    result, errors = dispatch(data)

    if result and consistency_check:
        if check(data, result):
            print("Consistency check successful")
        else:
            print("Consistency check failed")

    if errors and store_errors:
        if not Path(".amati").exists():
            Path(".amati").mkdir()

        with open(".amati/pydantic.json", "w", encoding="utf-8") as f:
            f.write(jsonpickle.encode(errors, unpicklable=False))  # type: ignore


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        prog="amati",
        description="Test whether a OpenAPI specification is valid.",
    )

    parser.add_argument(
        "-s", "--spec", required=True, help="The specification to be parsed"
    )

    parser.add_argument(
        "-cc",
        "--consistency-check",
        required=False,
        action="store_true",
        help="Runs a consistency check between the input specification and amati",
    )

    parser.add_argument(
        "-se",
        "--store-errors",
        required=False,
        action="store_true",
        help="Stores and errors in a file for visibility.",
    )

    args = parser.parse_args()

    run(args.spec, args.consistency_check, args.store_errors)
