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

from amati.fields.uri import URI, URIType, URIWithVariables
from amati.grammars import rfc6901

ABSOLUTE_URIS = [
    "https://пример.рф/документы/файл.html",
    "https://مثال.مصر/صفحة/رئيسية.html",
    "https://例子.中国/文件/索引.html",
    "https://דוגמה.ישראל/עמוד/ראשי.html",
    "https://ตัวอย่าง.ไทย/หน้า/หลัก.html",
]

RELATIVE_URIS = [
    "/київ/вулиця/площа-незалежності.html",
    "/القاهرة/شارع/الأهرام.html",
    "/東京/通り/渋谷.html",
    "/αθήνα/οδός/ακρόπολη.html",
    "/서울/거리/남대문.html",
]

NON_RELATIVE_URIS = [
    "//пример.бг/софия/страница.html",
    "//مثال.ایران/تهران/صفحه.html",
    "//उदाहरण.भारत/दिल्ली/पृष्ठ.html",
    "//օրինակ.հայ/երեվան/էջ.html",
    "//উদাহরণ.বাংলা/ঢাকা/পৃষ্ঠা.html",
]


JSON_POINTERS = [
    "#/київ/вулиця/площа-незалежності.html",
    "#/القاهرة/شارع/الأهرام.html",
    "#/東京/通り/渋谷.html",
    "#/αθήνα/οδός/ακρόπολη.html",
    "#/서울/거리/남대문.html",
]


@st.composite
def relative_uris(draw: st.DrawFn) -> str:
    """
    Generate relative URIs
    """

    candidate = draw(urls())

    parsed = urlparse(candidate)
    # urlparse incorrectly parses the URI http://a.com// with
    # a path of //, which is indicates that the succeeding
    # item is the authority in RFC 2986
    path = f"/{parsed.path.lstrip("/")}"
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""

    return f"{path}{query}{fragment}"


@st.composite
def json_pointers(draw: st.DrawFn) -> str:

    while True:
        pointer = draw(relative_uris())
        try:
            candidate = rfc6901.Rule("json-pointer").parse_all(pointer).value
            break
        except ParseError:
            continue

    return f"#{candidate}"


@given(st.one_of(urls(), st.sampled_from(ABSOLUTE_URIS)))
def test_absolute_uri_valid(value: str):
    result = URI(value)
    assert result == value
    assert result.type == URIType.ABSOLUTE


@given(st.one_of(relative_uris(), st.sampled_from(RELATIVE_URIS)))
def test_relative_uri_valid(value: str):
    result = URI(value)
    assert result == value
    assert result.type == URIType.RELATIVE


@given(st.one_of(json_pointers(), st.sampled_from(JSON_POINTERS)))
def test_json_pointer(value: str):
    result = URI(value)
    assert result == value
    assert result.type == URIType.JSON_POINTER


@given(st.one_of(urls(), st.sampled_from(NON_RELATIVE_URIS)))
def test_uri_non_relative(value: str):

    candidate: str = f"//{re.split("//", value)[1]}"

    result = URI(candidate)
    assert result == candidate
    assert result.type == URIType.AUTHORITY


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
        with pytest.raises(ValueError):
            URI("https://example.com")


def test_uri_none():
    with pytest.raises(ValueError):
        URI(None)  # type: ignore
        URIWithVariables(None)  # type: ignore


def test_uri_with_variables_valid():

    uri = r"https://{subdomain}.example.com/api/v1/users/{user_id}"
    result = URIWithVariables(uri)
    assert result == uri
    assert result.type == URIType.ABSOLUTE

    uri = r"/api/v1/users/{user_id}"
    result = URIWithVariables(uri)
    assert result == uri
    assert result.type == URIType.RELATIVE


def test_uri_with_variables_invalid():

    with pytest.raises(ValueError):
        result = URIWithVariables(
            r"https://{{subdomain}.example.com/api/users/{user_id}"
        )
        assert result.type == URIType.UNKNOWN

    with pytest.raises(ValueError):
        result = URIWithVariables(r"https://{}.example.com")
        assert result.type == URIType.UNKNOWN

    with pytest.raises(ValueError):
        result = URIWithVariables(r"/api/users/{user_id}}")
        assert result.type == URIType.UNKNOWN

    with pytest.raises(ValueError):
        result = URIWithVariables(r"/api/users/{user_id}{abc/")
        assert result.type == URIType.UNKNOWN

    with pytest.raises(ValueError):
        result = URIWithVariables(r"/api/users/{user_{id}}/")
        assert result.type == URIType.UNKNOWN
