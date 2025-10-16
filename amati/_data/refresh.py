import importlib
import json
import time
from pathlib import Path
from typing import Literal

from loguru import logger
from requests.exceptions import HTTPError

data_types = Literal[
    "http_status_code",
    "iso9110",
    "media_types",
    "schemes",
    "spdx_licences",
    "tlds",
    "all",
]

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


def refresh_module(module_: data_types) -> None:
    module = importlib.import_module(f"amati._data.{module_}")

    if not hasattr(module, "get"):
        raise ImportError(f"{module_} does not have a 'get' function.")

    if not hasattr(module, "DATA_FILE"):
        raise ImportError(f"{module_} does not have a 'DATA_FILE' attribute")

    if not hasattr(module, "DATA_SOURCE"):
        raise ImportError(f"{module_} does not have a 'DATA_SOURCE' attribute")

    logger.info(f"Refreshing data from {module_}")

    try:
        data = module.get()
    except HTTPError as e:
        logger.error(
            f"Failed to fetch data from {module.DATA_SOURCE}: {e}. "
            "Please check your internet connection or the availability of the data."
        )
        return

    if data is None:
        raise ValueError(
            f"Get {module_} returned None. Please check whether "
            f"{module.DATA_SOURCE} remains available."
        )

    current_path = Path(__file__).parent / "files"
    write_to = current_path / module.DATA_FILE

    with write_to.open("w") as f:
        json.dump(data, f, indent=2)


def _handle_data_types(data_type: data_types | list[data_types]) -> list[data_types]:
    """
    Double checks that the presented data_type is valid.

    Args:
        data_type: A string or a list of strings representing the data types to refresh.

    Returns:
        A list of valid data types.

    Raises:
        TypeError: If data_type is not a string or a list of strings.
        ValueError: If any of the provided data types are not valid.

    >>> _handle_data_types("http_status_code")
    ['http_status_code']
    >>> _handle_data_types(["http_status_code", "media_types"])
    ['http_status_code', 'media_types']
    >>> _handle_data_types("all")
    ['http_status_code', 'iso9110', 'media_types', 'schemes', 'spdx_licences', 'tlds']
    """

    if isinstance(data_type, str):
        if data_type == "all":
            data_type = [x for x in data_types.__args__ if x != "all"]
        else:
            data_type = [data_type]

    if not isinstance(data_type, list):  # type: ignore
        raise TypeError("data_type must be a string or a list of strings.")

    for module in data_type:
        if module not in data_types.__args__:
            raise ValueError(
                f"Invalid data type: {module}. Must be one of {data_types}."
            )

    return data_type


def refresh(data_type: data_types | list[data_types]) -> None:
    """
    Refreshes the data for the specified data type(s).
    Args:
        data_type: A string or a list of strings representing the data types to refresh.
            Can be one of:
            - "http_status_code"
            - "iso9110"
            - "media_types"
            - "schemes"
            - "spdx_licences"
            - "tlds"
            - "all" (to refresh all data types)
    Returns:
        None
    Raises:
        TypeError: If data_type is not a string or a list of strings.
        ValueError: If any of the provided data types are not valid.
    """
    to_refresh = _handle_data_types(data_type)

    for module in to_refresh:
        refresh_module(module)

        time.sleep(1)  # To avoid hitting IANA too hard


def get(data_type: data_types) -> dict[str, JSONValue] | list[JSONValue] | None:
    """
    Returns the data for a specified data type.

    Args:
        data_type: A string representing the data type to retrieve. Can be one of:
            - "http_status_code"
            - "iso9110"
            - "media_types"
            - "schemes"
            - "spdx_licences"
            - "tlds"

    Returns:
        A generator yielding JSON data for the specified data type.
    Raises:
        TypeError: If data_type is not a string.
        ValueError: If data_type is not one of the valid types.

    """
    to_get = _handle_data_types(data_type)

    if len(to_get) != 1:
        raise ValueError("get() can only retrieve one data type at a time. ")

    data = None
    current_path = Path(__file__).parent / "files"

    for module_ in to_get:
        module = importlib.import_module(f"amati._data.{module_}")

        data_file: Path = current_path / module.DATA_FILE

        with data_file.open(encoding="utf-8") as f:
            data = json.loads(f.read())

        if not data:
            logger.error(
                f"No data found for {module_}. "
                "Please ensure the data has been refreshed."
            )

    return data
