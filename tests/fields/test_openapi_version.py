"""
Tests amati/fields/oas.py
"""

import pytest
from abnf.parser import ParseError
from hypothesis import given
from hypothesis import strategies as st

from amati.fields.oas import OPENAPI_VERSIONS, OpenAPI, RuntimeExpression
from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class OpenAPIModel(GenericObject):
    value: OpenAPI


class RuntimExpressionModel(GenericObject):
    value: RuntimeExpression


@given(st.text().filter(lambda x: x not in OPENAPI_VERSIONS))
def test_invalid_openapi_version(value: str):
    with LogMixin.context():
        OpenAPIModel(value=value)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
        assert LogMixin.logs[0].reference is not None


@given(st.sampled_from(OPENAPI_VERSIONS))
def test_valid_openapi_version(value: str):
    model = OpenAPIModel(value=value)
    assert model.value == value


def test_valid_runtime_expression():
    expressions = [
        "$url",
        "$method",
        "$statusCode",
        "$request.header.content-type",
        "$request.query.userId",
        "$request.query./name",
        "$response.path.itemId",
        "$response.body",
        "$response.body#/users/0/name",
        "$request.body#/data/items~1products/0",
        "$response.header.x-rate-limit_remaining",
        "$request.header..double-dot",
        "$request.header.token.",
    ]

    for expression in expressions:
        assert RuntimExpressionModel(value=expression).value == expression


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
        print(expression)
        with pytest.raises(ParseError):
            RuntimExpressionModel(value=expression)
