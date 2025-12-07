"""
High-level access to amati functionality.
"""

import importlib
import json
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from loguru import logger
from pydantic import BaseModel, ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))
from amati._data.refresh import refresh
from amati._error_handler import ErrorHandler
from amati._logging import Log, Logger
from amati._references import URIRegistry
from amati._resolve_forward_references import resolve_forward_references
from amati.fields import URIType
from amati.file_handler import load_file

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


def _determine_version(data: JSONObject) -> str:
    """
    Determines the OpenAPI specification version from the provided data.

    Args:
        data: A dictionary representing an OpenAPI specification

    Returns:
        The OpenAPI specification version as a string
    """

    version: JSONValue = data.get("openapi")

    if not isinstance(version, str):
        raise TypeError("A OpenAPI specification version must be a string.")

    if not version:
        raise TypeError("An OpenAPI Specfication must contain a version.")

    return version


def dispatch(
    data: JSONObject,
    context: dict[str, Any],
    version: str,
    obj: str = "OpenAPIObject",
) -> tuple[BaseModel | None, list[JSONObject] | None]:
    """
    Returns the correct model for the passed spec

    Args:
        data: A dictionary representing an OpenAPI specification
        version: An optional Open API version string to override automatic detection.
            The most common reason to provide the version is when validating references
            outside of the context of a full specification document.

    Returns:
        A pydantic model representing the API specification
    """

    version_map: dict[str, str] = {
        "3.1.1": "311",
        "3.1.0": "311",
        "3.0.4": "304",
        "3.0.3": "304",
        "3.0.2": "304",
        "3.0.1": "304",
        "3.0.0": "304",
    }

    module_name: str = f"amati.validators.oas{version_map[version]}"

    module = importlib.import_module(module_name)
    resolve_forward_references(module)

    try:
        model = getattr(module, obj).model_validate(data, context=context)
    except ValidationError as e:
        return None, json.loads(e.json())

    return model, None


def dispatch_all(spec: Path) -> tuple[BaseModel | None, ErrorHandler]:
    """ """

    registry = URIRegistry.get_instance()
    registry.reset()

    error_handler = ErrorHandler()
    result: BaseModel | None = None
    version: str | None = None

    to_process: list[tuple[Path, str]] = [(spec, "OpenAPIObject")]

    while to_process:
        doc_path, obj = to_process.pop(0)

        # Skip if already validated (handles circular references)
        if registry.is_processed(doc_path):
            continue

        logger.info(f"Validating: {doc_path}")

        data: JSONObject = load_file(spec)

        # Create validation context with current document path
        context = {"current_document": str(doc_path)}

        if obj == "OpenAPIObject":
            version = _determine_version(data)
        elif version is None:
            raise ValueError("Version must be set in the OpenAPI object")

        with Logger.context():
            result, errors = dispatch(data, context, version, obj)

            if errors:
                error_handler.register_errors(errors)

            error_handler.register_logs(Logger.logs)

        registry.mark_processed(doc_path)

        references = registry.get_all_references()

        # Find references that originated from the document we just validated
        # and haven't been processed yet
        for ref in references:
            if ref.source_document != doc_path:
                continue

            resolved_path = ref.resolve()

            if registry.is_processed(resolved_path):
                continue

            if resolved_path.exists() and ref.uri.type != URIType.ABSOLUTE:
                to_process.append((resolved_path, ref.target_model.__name__))
            else:
                # File doesn't exist - record error
                error_handler.register_log(
                    Log(
                        type="missing_reference",
                        loc=(ref.source_document.name,),
                        msg=f"Could not locate {ref.uri.type.value} URI",
                        input=ref.uri,
                    )
                )

        references = registry.get_all_references()

    return result, error_handler


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
) -> bool:
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
        local: Whether or not to store the errors in the .amati/ directory
        html_report: Whether or not to create an HTML report of the errors
    """

    spec = Path(file_path)

    data = load_file(spec)

    result, handled_errors = dispatch_all(spec)
    handled_errors.deduplicate()

    if handled_errors.errors:
        file_name = Path(Path(file_path).parts[-1])
        error_file = file_name.with_suffix(file_name.suffix + ".errors")
        error_path = spec.parent

        if local:
            error_path = Path(".amati")

            if not error_path.exists():
                error_path.mkdir()

        json_error_file: Path = error_path / error_file.with_suffix(
            error_file.suffix + ".json"
        )

        with json_error_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(handled_errors.errors))

        if html_report:
            env = Environment(
                loader=FileSystemLoader("."),
                autoescape=True,
            )  # Assumes template is in the same directory
            template = env.get_template("TEMPLATE.html")

            # Render the template with your data
            html_output = template.render(errors=handled_errors.errors)

            # Save the output to a file

            html_error_file: Path = error_path / error_file.with_suffix(
                error_file.suffix + ".html"
            )
            with html_error_file.open("w", encoding="utf-8") as f:
                f.write(html_output)

    if result and consistency_check:
        return check(data, result)

    return True


if __name__ == "__main__":
    logger.remove()  # Remove the default logger
    # Add a new logger that outputs to stderr with a specific format
    logger.add(sys.stderr, format="{time} | {level} | {message}")

    import argparse

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="amati",
        description="""
        Tests whether a OpenAPI specification is valid. Creates a file
        <filename>.errors.json alongside the original specification containing
        a JSON representation of all the errors.

        Optionally creates an HTML report of the errors, and performs an internal
        consistency check to verify that the output of the validation is identical
        to the input.
        """,
        suggest_on_error=True,
    )

    subparsers: argparse.Action = parser.add_subparsers(required=True, dest="command")

    validation: argparse.ArgumentParser = subparsers.add_parser("validate")

    validation.add_argument(
        "-s",
        "--spec",
        required=True,
        help="The specification to be validated",
    )

    validation.add_argument(
        "--consistency-check",
        required=False,
        action="store_true",
        help="Runs a consistency check between the input specification and the"
        " parsed specification",
    )

    validation.add_argument(
        "--local",
        required=False,
        action="store_true",
        help="Store errors local to the caller in .amati/<file-name>.errors.json",
    )

    validation.add_argument(
        "--html-report",
        required=False,
        action="store_true",
        help="Creates an HTML report of the errors, called <file-name>.errors.html,"
        " alongside <filename>.errors.json",
    )

    refreshment: argparse.ArgumentParser = subparsers.add_parser("refresh")

    refreshment.add_argument(
        "--type",
        required=False,
        default="all",
        choices=[
            "all",
            "http_status_code",
            "iso9110",
            "media_types",
            "schemes",
            "spdx_licences",
            "tlds",
        ],
        help="The type of data to refresh. Defaults to all.",
    )

    args: argparse.Namespace = parser.parse_args()

    logger.info("Starting amati")

    if args.command == "refresh":
        logger.info("Refreshing data.")
        try:
            refresh("all")
            logger.info("Data refreshed successfully.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            sys.exit(1)

    specification: Path = Path(args.spec)
    logger.info(f"Processing specification {specification}")

    # Top-level try/except to ensure one failed spec doesn't stop the rest
    # from being processed.
    e: Exception
    try:
        successful_check: bool = run(
            specification, args.consistency_check, args.local, args.html_report
        )
        logger.info(f"Specification {specification} processed successfully.")
    except Exception as e:
        logger.error(f"Error processing {specification}, {e}")
        sys.exit(1)

    if args.consistency_check and successful_check:
        logger.info(f"Consistency check successful for {specification}")
    elif args.consistency_check:
        logger.info(f"Consistency check failed for {specification}")

    logger.info("Stopping amati.")
