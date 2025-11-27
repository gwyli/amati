from typing import Any


def reference_object_disciminator(data: Any) -> str:
    if isinstance(data, dict) and "$ref" in data:
        return "ref"

    return "other"
