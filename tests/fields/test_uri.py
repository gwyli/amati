"""
Tests amati/fields/uri.py
"""

import re
from unittest import mock
from urllib.parse import urlparse

import pytest
from abnf.parser import Matches, ParseError, Parser
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati.fields.uri import URI, URIType, URIWithVariables
from amati.grammars import rfc6901
from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class URIModel(GenericObject):
    uri: URI


class URIWithVariablesModel(GenericObject):
    uri: URIWithVariables


def get_uri_path_and_query(value: str) -> str:
    """Extract everything after the domain from a URI."""
    parsed = urlparse(value)
    # urlparse incorrectly parses the URI http://a.com// with
    # a path of //, which is indicates that the succeeding
    # item is the authority in RFC 2986
    path = f"/{parsed.path.lstrip("/")}"
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{path}{query}{fragment}"


@given(urls())
def test_uri_path_extraction(value: str):
    result = get_uri_path_and_query(value)
    assert result.startswith("/")
    assert not result.startswith("//")


@given(urls())
def test_absolute_uri_valid(value: str):
    with LogMixin.context():
        model = URIModel(uri=value)  # type: ignore
        assert not LogMixin.logs
        assert model.uri.type == URIType.ABSOLUTE


@st.composite
def relative_uris(draw: st.DrawFn) -> str:

    candidate = get_uri_path_and_query(draw(urls()))

    return candidate


@st.composite
def json_pointers(draw: st.DrawFn) -> str:

    while True:
        pointer = get_uri_path_and_query(draw(urls()))
        try:
            candidate = rfc6901.Rule("json-pointer").parse_all(pointer).value
            break
        except ParseError:
            continue

    return f"#{candidate}"


@given(relative_uris())
def test_relative_uri_valid(value: str):
    with LogMixin.context():
        model = URIModel(uri=value)  # type: ignore
        assert not LogMixin.logs
        assert model.uri.type == URIType.RELATIVE


@given(json_pointers())
def test_relative_uri_with_hash(value: str):
    with LogMixin.context():
        model = URIModel(uri=value)  # type: ignore
        assert not LogMixin.logs
        assert model.uri == value
        assert model.uri.type == URIType.JSON_POINTER


@given(urls())
def test_uri_authority(value: str):

    candidate: str = f"//{re.split("//", value)[1]}"

    with LogMixin.context():
        model = URIModel(uri=candidate)  # type: ignore
        assert model.uri.type == URIType.AUTHORITY


def test_rfc3986_parser_errors():

    class MockParser(Parser):
        def lparse(self, source: str, start: int) -> Matches: ...  # pragma: no cover

    # Create a mock Rule class that raises an exception when parse_all is called
    mock_rule = mock.Mock()
    mock_rule.parse_all.side_effect = ParseError(parser=MockParser(), start=1)

    # Mock the Rule constructor to return our mock rule
    mock.patch("abnf.grammars.rfc3986.Rule", return_value=mock_rule)

    with mock.patch("abnf.grammars.rfc3986.Rule", return_value=mock_rule):
        # Test that validation fails when parser fails
        with LogMixin.context():
            URIModel(uri="https://example.com")  # type: ignore
            assert LogMixin.logs
            assert LogMixin.logs[0].message is not None
            assert LogMixin.logs[0].type == ValueError


def test_uri_none():
    with pytest.raises(ValidationError):
        URIModel(uri=None)  # type: ignore


def test_uri_with_variables_valid():

    with LogMixin.context():
        uri = r"https://{subdomain}.example.com/api/v1/users/{user_id}"
        model = URIWithVariablesModel(uri=uri)  # type: ignore
        assert model.uri == uri
        assert model.uri.type == URIType.ABSOLUTE

        uri = r"/api/v1/users/{user_id}"
        model = URIWithVariablesModel(uri=uri)  # type: ignore
        assert model.uri == uri
        assert model.uri.type == URIType.RELATIVE

        assert not LogMixin.logs


def test_uri_with_variables_invalid():

    with LogMixin.context():
        model = URIWithVariablesModel(
            uri=r"https://{{subdomain}.example.com/api/users/{user_id}"  # type: ignore
        )
        assert model.uri.type == URIType.UNKNOWN
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        model = URIWithVariablesModel(uri=r"https://{}.example.com")  # type: ignore
        assert model.uri.type == URIType.UNKNOWN
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        model = URIWithVariablesModel(uri=r"/api/users/{user_id}}")  # type: ignore
        assert model.uri.type == URIType.UNKNOWN
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        model = URIWithVariablesModel(uri=r"/api/users/{user_id}{abc/")  # type: ignore
        assert model.uri.type == URIType.UNKNOWN
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        model = URIWithVariablesModel(uri=r"/api/users/{user_{id}}/")  # type: ignore
        assert model.uri.type == URIType.UNKNOWN
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
