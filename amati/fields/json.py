"""
Defines a JSON datatype
"""

from types import NoneType
from typing import Union

JSONPrimitive = Union[str, int, float, bool, NoneType]
JSONArray = list['JSONValue']
JSONObject = dict[str, 'JSONValue']
JSONValue = Union[JSONPrimitive, JSONArray, JSONObject]

# Type alias for cleaner usage
JSON = JSONValue
