"""
Tests amati/fields/uri.py
"""

from urllib.parse import urlparse

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls

from amati.fields.uri import URI, AbsoluteURI, RelativeURI, URIWithVariables
from amati.validators.generic import GenericObject


class URIModel(GenericObject):
    uri: URI


class AbsoluteURIModel(GenericObject):
    uri: AbsoluteURI


class RelativeURIModel(GenericObject):
    uri: RelativeURI


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
    AbsoluteURIModel(uri=uri)


@st.composite
def relative_uris(draw: st.DrawFn) -> str:
    uri = draw(urls())
    return get_uri_path_and_query(uri)


@given(relative_uris())
def test_relative_uri_valid(uri: str):
    RelativeURIModel(uri=uri)


@given(urls())
def test_uri_valid(uri: str):
    URIModel(uri=uri)
    get_uri_path_and_query(uri)
    URIModel(uri=uri)


def test_uri_with_variables_valid():
    URIWithVariablesModel(uri=r"https://{subdomain}.example.com/api/v1/users/{user_id}")
    URIWithVariablesModel(uri=r"/api/v1/users/{user_id}")
    URIWithVariablesModel(uri=r"/api/v1/users/{user_id}/")


def test_uri_with_variables_invalid():
    with pytest.raises(ValueError):
        URIWithVariablesModel(
            uri=r"https://{{subdomain}.example.com/api/v1/users/{user_id}"
        )

    with pytest.raises(ValueError):
        URIWithVariablesModel(uri=r"/api/v1/users/{user_id}}")

    with pytest.raises(ValueError):
        URIWithVariablesModel(uri=r"/api/v1/users/{user_id}{abc/")

    with pytest.raises(ValueError):
        URIWithVariablesModel(uri=r"/api/v1/users/{user_{id}}/")
