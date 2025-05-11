"""
Tests amati/fields/uri.py
"""

from unittest import mock
from urllib.parse import urlparse

import pytest
from abnf.parser import Matches, ParseError, Parser
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati.fields.uri import URI, URIWithVariables
from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class URIModel(GenericObject):
    uri: URI


URIModel(uri="#/components/schemas/Pet")


class URIWithVariablesModel(GenericObject):
    uri: URIWithVariables


def get_uri_path_and_query(uri: str) -> str:
    """Extract everything after the domain from a URI."""
    parsed = urlparse(uri)
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{path}{query}{fragment}"


@given(urls())
def test_uri_path_extraction(uri: str):
    result = get_uri_path_and_query(uri)
    assert result.startswith("/")


@given(urls())
def test_absolute_uri_valid(uri: str):
    with LogMixin.context():
        URIModel(uri=uri)
        assert not LogMixin.logs


@st.composite
def relative_uris(draw: st.DrawFn) -> str:
    uri = draw(urls())
    return get_uri_path_and_query(uri)


@given(relative_uris())
def test_relative_uri_valid(uri: str):
    with LogMixin.context():
        URIModel(uri=uri)
        assert not LogMixin.logs


@given(urls())
def test_uri_valid(uri: str):
    with LogMixin.context():
        URIModel(uri=uri)
        get_uri_path_and_query(uri)
        URIModel(uri=uri)
        assert not LogMixin.logs


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
        with pytest.raises(ParseError):
            URIModel(uri="https://example.com")


def test_uri_none():
    with pytest.raises(ValidationError):
        URIModel(uri=None)  # type: ignore


def test_uri_with_variables_valid():

    with LogMixin.context():
        uri = r"https://{subdomain}.example.com/api/v1/users/{user_id}"
        model = URIWithVariablesModel(uri=uri)
        assert model.uri == uri

        uri = r"/api/v1/users/{user_id}"
        model = URIWithVariablesModel(uri=uri)
        assert model.uri == uri

        uri = r"/api/v1/users/{user_id}/"
        model = URIWithVariablesModel(uri=uri)
        assert model.uri == uri
        assert not LogMixin.logs


def test_uri_with_variables_invalid():

    with LogMixin.context():
        URIWithVariablesModel(
            uri=r"https://{{subdomain}.example.com/api/v1/users/{user_id}"
        )
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        URIWithVariablesModel(uri=r"https://{}.example.com")
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        URIWithVariablesModel(uri=r"/api/v1/users/{user_id}}")
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        URIWithVariablesModel(uri=r"/api/v1/users/{user_id}{abc/")
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError

    with LogMixin.context():
        URIWithVariablesModel(uri=r"/api/v1/users/{user_{id}}/")
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
