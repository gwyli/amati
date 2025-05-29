"""
Tests amati/fields/oas.py
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from amati import AmatiValueError
from amati.fields.oas import OPENAPI_VERSIONS, OpenAPI, RuntimeExpression


@given(st.text().filter(lambda x: x not in OPENAPI_VERSIONS))
def test_invalid_openapi_version(value: str):
    with pytest.raises(AmatiValueError):
        OpenAPI(value)


@given(st.sampled_from(OPENAPI_VERSIONS))
def test_valid_openapi_version(value: str):
    OpenAPI(value)


def test_valid_runtime_expression():
    expressions = [
        # Basic root expressions
        "$url",
        "$method",
        "$statusCode",
        # Header references
        "$request.header.content-type",  # Common header format
        "$request.header.x-rate-limit_remaining",  # Header with underscore
        "$request.header..double-dot",  # Multiple dots in token
        "$request.header.token.",  # Trailing dot
        "$request.header.!#$%&'",  # Special characters at start
        "$response.header.*+-.^_`|~",  # Special characters throughout
        "$request.header.123ABC",  # Digits and letters
        # Query references
        "$request.query.userId",  # Simple query param
        "$request.query./name",  # With leading slash
        "$request.query.with space",  # Space in name
        "$response.query.with/slash",  # Slash in name
        "$request.query.with{brackets}",  # Special chars in name
        # Path references
        "$response.path.itemId",  # Simple path param
        "$response.path.param_123",  # Underscores and numbers
        "$request.path.with@special#chars",  # Special characters in name
        # Body references
        "$response.body",  # Simple body reference
        "$request.body#/data/items~1products/0",  # Escaped forward slash
        "$response.body#/users/0/name",  # Array indexing
        "$request.body#/deeply/nested/array/0/field",  # Deep nesting
        "$response.body#/~0~1",  # Escaped ~ and /
        "$request.body#/special*chars/in.pointer",  # Special chars in pointer
        "$response.body#/with~0tilde",  # Escaped tilde mid-string
        # Mixing maximum character sets
        "$request.header.~.-_*+$%",  # Mix of allowed special chars in token
        "$response.query.\u0394\u0395\u0396",  # Unicode chars in name
        "$request.path.éèêëēėę",  # Accented chars in name
        "$response.body#/\u2603/\u2600",  # Unicode in json pointer
    ]

    for expression in expressions:
        assert RuntimeExpression(expression) == expression


def test_invalid_runtime_expression():
    expressions = [
        # Root expression errors
        "url",  # missing $ prefix
        "$invalid",  # not a valid root token
        "$REQUEST",  # case sensitive, must be lowercase
        "$request",  # missing source after dot
        "$response",  # missing source after dot
        # Source type errors
        "$request.invalid",  # invalid source type
        "$response.cookies",  # invalid source type
        "$request.json",  # invalid source type
        # Header reference errors
        "$request.header",  # missing token after header
        "$response.header.@invalid",  # invalid character in token
        "$request.header.{invalid}",  # curly braces not allowed in token
        "$response.header.[brackets]",  # brackets not allowed in token
        "$request.header.<angle>",  # angle brackets not allowed in token
        # Query/Path reference errors
        "$response.query",  # missing name part
        "$request.path",  # missing name part
        # Body reference errors
        "$response.body#abc",  # json-pointer must start with /
        "$request.body#invalid",  # json-pointer must start with /
        "$response.body#/~",  # incomplete escape sequence
        "$request.body#/~2",  # invalid escape sequence (only ~0 and ~1 allowed)
        "$response.body#/test~~test",  # invalid escape sequence
        # Structure errors
        "$.response.body",  # invalid structure
        "$response..body",  # double dots not allowed here
        "$request.header:",  # invalid character
        "$response.header,name",  # invalid character
    ]

    for expression in expressions:
        with pytest.raises(AmatiValueError):
            RuntimeExpression(expression)
