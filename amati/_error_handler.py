"""
Handles Pydantic errors and amati logs to provide a consistent view to the user.
"""

import json
from typing import cast

from amati._logging import Log

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


def remove_duplicates(data: list[JSONObject]) -> list[JSONObject]:
    """
    Remove duplicates by converting each dict to a JSON string for comparison.
    """
    seen: set[str] = set()
    unique_data: list[JSONObject] = []

    for item in data:
        # Convert to JSON string with sorted keys for consistent hashing
        item_json = json.dumps(item, sort_keys=True, separators=(",", ":"))
        if item_json not in seen:
            seen.add(item_json)
            unique_data.append(item)

    return unique_data


def handle_errors(errors: list[JSONObject] | None, logs: list[Log]) -> list[JSONObject]:
    """
    Makes errors and logs consistent for user consumption.
    """

    result: list[JSONObject] = []

    if errors:
        result.extend(errors)

    if logs:
        result.extend(cast(list[JSONObject], logs))

    result = remove_duplicates(result)

    return result
