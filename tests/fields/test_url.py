"""
Tests amati/fields/url.py
"""

from urllib.parse import urlparse

import pytest
from hypothesis import given, strategies as st
from hypothesis.provisional import urls

from amati.validators.generic import GenericObject
from amati.fields.url import URL, AbsoluteURL, RelativeURL, URLWithVariables


class URLModel(GenericObject):
    url: URL


class AbsoluteURLModel(GenericObject):
    url: AbsoluteURL


class RelativeURLModel(GenericObject):
    url: RelativeURL


class URLWithVariablesModel(GenericObject):
    url: URLWithVariables


def get_url_path_and_query(url: str) -> str:
    """Extract everything after the domain from a URL."""
    parsed = urlparse(url)
    path = parsed.path or '/'
    query = f'?{parsed.query}' if parsed.query else ''
    fragment = f'#{parsed.fragment}' if parsed.fragment else ''
    return f"{path}{query}{fragment}"


@given(urls())
def test_url_path_extraction(url: str):
    result = get_url_path_and_query(url)
    assert result.startswith('/')


@given(urls())
def test_absolute_url_valid(url: str):
    AbsoluteURLModel(url=url)


@st.composite
def relative_urls(draw: st.DrawFn) -> str:
    url = draw(urls())
    return get_url_path_and_query(url)


@given(relative_urls())
def test_relative_url_valid(url: str):
    RelativeURLModel(url=url)


@given(urls())
def test_url_valid(url: str):
    URLModel(url=url)
    get_url_path_and_query(url)
    URLModel(url=url)


def test_url_with_variables_valid():
    URLWithVariablesModel(url=r'https://{subdomain}.example.com/api/v1/users/{user_id}')
    URLWithVariablesModel(url=r'/api/v1/users/{user_id}')
    URLWithVariablesModel(url=r'/api/v1/users/{user_id}/')

def test_url_with_variables_invalid():
    with pytest.raises(ValueError):
        URLWithVariablesModel(url=r'https://{{subdomain}.example.com/api/v1/users/{user_id}')

    with pytest.raises(ValueError):
        URLWithVariablesModel(url=r'/api/v1/users/{user_id}}')

    with pytest.raises(ValueError):
        URLWithVariablesModel(url=r'/api/v1/users/{user_{id}}/')
