"""
Tests amati/fields/uri.py
"""

import re
from urllib.parse import urlparse

import pytest
from abnf.parser import ParseError
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls

from amati import AmatiValueError
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
    # urlparse parses the URI http://a.com// with a path of //, which indicates that
    # the succeeding item is the authority in RFC 2986 when actual authority/netloc
    # is removed.
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


@given(urls())
def test_json_pointer_invalid(value: str):

    if value.startswith("/"):
        return

    value_ = f"#{value}"
    with pytest.raises(AmatiValueError):
        URI(value_)


@given(st.one_of(urls(), st.sampled_from(NON_RELATIVE_URIS)))
def test_uri_non_relative(value: str):

    # the urls() strategy doesn't necessarily provide absolute URIs
    candidate: str = f"//{re.split("//", value)[1]}"

    result = URI(candidate)
    assert result == candidate
    assert result.type == URIType.NON_RELATIVE


def test_uri_none():
    with pytest.raises(AmatiValueError):
        URI(None)  # type: ignore

    with pytest.raises(AmatiValueError):
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
        URIWithVariables(r"https://{{subdomain}.example.com/api/users/{user_id}")

    with pytest.raises(ValueError):
        URIWithVariables(r"https://{}.example.com")

    with pytest.raises(ValueError):
        URIWithVariables(r"/api/users/{user_id}}")

    with pytest.raises(ValueError):
        URIWithVariables(r"/api/users/{user_id}{abc/")

    with pytest.raises(ValueError):
        URIWithVariables(r"/api/users/{user_{id}}/")
