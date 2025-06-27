"""
High-level access to amati functionality.
"""

import importlib
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError

# pylint: disable=wrong-import-position

sys.path.insert(0, str(Path(__file__).parent.parent))
from amati._error_handler import handle_errors
from amati._resolve_forward_references import resolve_forward_references
from amati.file_handler import load_file
from amati.logging import Log, LogMixin

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


def dispatch(data: JSONObject) -> tuple[BaseModel | None, list[JSONObject] | None]:
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
        return None, json.loads(e.json())

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


def run(
    file_path: str | Path,
    consistency_check: bool = False,
    local: bool = False,
    html_report: bool = False,
):
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

    spec = Path(file_path)

    data = load_file(spec)

    logs: list[Log] = []

    with LogMixin.context():
        result, errors = dispatch(data)
        logs.extend(LogMixin.logs)

    if errors or logs:

        handled_errors: list[JSONObject] = handle_errors(errors, logs)

        file_name = Path(Path(file_path).parts[-1])
        error_file = file_name.with_suffix(file_name.suffix + ".errors")
        error_path = spec.parent

        if local:
            error_path = Path(".amati")

            if not error_path.exists():
                error_path.mkdir()

        with open(
            error_path / error_file.with_suffix(error_file.suffix + ".json"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(handled_errors))

        if html_report:
            env = Environment(
                loader=FileSystemLoader(".")
            )  # Assumes template is in the same directory
            template = env.get_template("TEMPLATE.html")

            # Render the template with your data
            html_output = template.render(errors=handled_errors)

            # Save the output to a file
            with open(
                error_path / error_file.with_suffix(error_file.suffix + ".html"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(html_output)

    if result and consistency_check:
        return check(data, result)


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
        
        Creates a file <filename>.errors.json alongside the original specification
        containing a JSON representation of all the errors.
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
        help="Runs a consistency check between the input specification and the"
        " parsed specification",
    )

    parser.add_argument(
        "-d",
        "--discover",
        required=False,
        default=".",
        help="Searches the specified directory tree for openapi.yaml or openapi.json.",
    )

    parser.add_argument(
        "-l",
        "--local",
        required=False,
        action="store_true",
        help="Store errors local to the caller in a file called <file-name>.errors.json"
        "; a .amati/ directory will be created.",
    )

    parser.add_argument(
        "-hr",
        "--html-report",
        required=False,
        action="store_true",
        help="Creates an HTML report of the errors, called <file-name>.errors.html,"
        " alongside the original file or in a .amati/ directory if the --local switch"
        " is used",
    )

    args = parser.parse_args()

    if args.spec:
        specifications: list[Path] = [Path(args.spec)]
    else:
        specifications = discover(args.discover)

    for specification in specifications:
        if successful_check := run(
            specification, args.consistency_check, args.local, args.html_report
        ):
            print("Consistency check successful for {specification}")
        else:
            print("Consistency check failed for {specification}")
