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
        raise TypeError("A OpenAPI specification version must be a string.")

    if not version:
        raise TypeError("An OpenAPI Specfication must contain a version.")

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


def run(file_path: str | Path, consistency_check: bool = False):
    """
    Runs the full amati process on a specific specification file.

     * Parses the YAML or JSON specification, gunzipping if necessary.
     * Validates the specification.
     * Runs a consistency check on the ouput of the validation to verify
       that the output is identical to the input.
     * Stores any errors found during validation.

    Args:
        file_path: The specification to be validated
        consistency_check: Whether or not to verify the output against the input
    """

    data = load_file(file_path)

    result, errors = dispatch(data)

    if result and consistency_check:
        if check(data, result):
            print("Consistency check successful")
        else:
            print("Consistency check failed")

    if errors:
        if not Path(".amati").exists():
            Path(".amati").mkdir()

        error_file = Path(file_path).parts[-1]

        with open(f".amati/{error_file}.json", "w", encoding="utf-8") as f:
            f.write(jsonpickle.encode(errors, unpicklable=False))  # type: ignore


def discover(discover_dir: str = ".") -> list[Path]:
    """
    Finds OpenAPI Specification files to validate

    Args:
        discover_dir: The directory to search through.
    Returns:
        A list of paths to validate.
    """

    specs: list[Path] = []

    if Path("openapi.json").exists():
        specs.append(Path("openapi.json"))

    if Path("openapi.yaml").exists():
        specs.append(Path("openapi.yaml"))

    if specs:
        return specs

    if discover_dir == ".":
        raise FileNotFoundError(
            "openapi.json or openapi.yaml can't be found, use --discover or --spec."
        )

    specs = specs + list(Path(discover_dir).glob("**/openapi.json"))
    specs = specs + list(Path(discover_dir).glob("**/openapi.yaml"))

    if not specs:
        raise FileNotFoundError(
            "openapi.json or openapi.yaml can't be found, use --spec."
        )

    return specs


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        prog="amati",
        description="""
        Tests whether a OpenAPI specification is valid. Will look an openapi.json
        or openapi.yaml file in the directory that amati is called from. If 
        --discover is set will search the directory tree. If the specification
        does not follow the naming recommendation the --spec switch should be
        used.
        """,
    )

    parser.add_argument(
        "-s",
        "--spec",
        required=False,
        help="The specification to be parsed",
    )

    parser.add_argument(
        "-cc",
        "--consistency-check",
        required=False,
        action="store_true",
        help="Runs a consistency check between the input specification and amati",
    )

    parser.add_argument(
        "-d",
        "--discover",
        required=False,
        default=".",
        help="Searches the specified directory tree for openapi.yaml or openapi.json.",
    )

    args = parser.parse_args()

    if args.spec:
        specifications: list[Path] = [Path(args.spec)]
    else:
        specifications = discover(args.discover)

    for specification in specifications:
        run(specification, args.consistency_check)
