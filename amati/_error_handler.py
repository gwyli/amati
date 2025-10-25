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


class ErrorHandler:
    def __init__(self) -> None:
        self._errors: list[JSONObject] = []

    def register_logs(self, logs: list[Log]):
        self._errors.extend(cast(list[JSONObject], logs))

    def register_log(self, log: Log):
        self._errors.append(cast(JSONObject, log))

    def register_errors(self, errors: list[JSONObject]):
        self._errors.extend(errors)

    def deduplicate(self):
        """
        Remove duplicates by converting each dict to a JSON string for comparison.
        """
        seen: set[str] = set()
        unique_data: list[JSONObject] = []

        item: JSONObject
        for item in self._errors:
            # Convert to JSON string with sorted keys for consistent hashing
            item_json = json.dumps(item, sort_keys=True, separators=(",", ":"))
            if item_json not in seen:
                seen.add(item_json)
                unique_data.append(item)

        self._errors = unique_data

    @property
    def errors(self) -> list[JSONObject]:
        return self._errors
