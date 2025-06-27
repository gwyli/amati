"""
Handles Pydantic errors and amati logs to provide a consistent view to the user.
"""

import json
from amati.logging import Log
from typing import Generator

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


def reformat_logs(logs: list[Log]) -> Generator[JSONObject]:

    for log in logs:

        url = getattr(getattr(log, "reference", None), "url", None)

        yield {
            "type": str(log.type),
            "loc": [None],
            "msg": log.message,
            "input": {},
            "url": url,
        }


def handle_errors(errors: list[JSONObject] | None, logs: list[Log]) -> list[JSONObject]:

    result: list[JSONObject] = []

    if errors:
        result.extend(errors)

    if logs:
        result.extend(reformat_logs(logs))

    result = remove_duplicates(result)

    return result
