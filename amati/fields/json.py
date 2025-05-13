"""
Defines a JSON datatype
"""

from types import NoneType

type JSONPrimitive = str | int | float | bool | NoneType
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject

# Type alias for cleaner usage
type JSON = JSONValue
