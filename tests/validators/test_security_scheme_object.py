"""
Tests amati/validators/oas311.py - ServerVariableObject
and the sub-objects OAuthFlowsObject and OAuthFlowObject
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from amati.fields.iso9110 import HTTP_AUTHENTICATION_SCHEMES
from amati.logging import LogMixin
from amati.validators.oas311 import (
    SECURITY_SCHEME_TYPES,
    OAuthFlowsObject,
    SecuritySchemeObject,
)
from tests.helpers import text_excluding_empty_string

VALID_SECURITY_SCHEME_TYPES: list[str] = list(SECURITY_SCHEME_TYPES)
INVALID_SECURITY_SCHEME_TYPES: st.SearchStrategy[str] = st.text().filter(
    lambda x: x not in VALID_SECURITY_SCHEME_TYPES
)

VALID_HTTP_AUTHENTICATION_SCHEMES: list[str] = list(HTTP_AUTHENTICATION_SCHEMES)
INVALID_HTTP_AUTHENTICATION_SCHEMES: st.SearchStrategy[str] = st.text().filter(
    lambda x: x not in VALID_HTTP_AUTHENTICATION_SCHEMES
)


@given(INVALID_SECURITY_SCHEME_TYPES.filter(lambda x: x != ""))
def test_security_scheme_invalid(scheme_type: str):

    with LogMixin.context():
        SecuritySchemeObject(type=scheme_type)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError


@given(st.none())
def test_security_scheme_none(scheme_type: str):
    with pytest.raises(ValidationError):
        SecuritySchemeObject(type=scheme_type)


@given(
    st.text(),
    text_excluding_empty_string(),
    st.sampled_from(("query", "header", "cookie")),
)
def test_security_scheme_apikey_valid(description: str, name: str, in_: str):
    with LogMixin.context():
        SecuritySchemeObject(type="apiKey", description=description, name=name, in_=in_)
        assert not LogMixin.logs


@given(st.text(), st.text(), st.text(), st.text())
def test_security_scheme_apikey_invalid(
    type_: str, description: str, name: str, in_: str
):
    with LogMixin.context():
        SecuritySchemeObject(type=type_, description=description, name=name, in_=in_)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError


@given(st.text(), st.sampled_from(VALID_HTTP_AUTHENTICATION_SCHEMES), st.text())
def test_security_scheme_http_valid(description: str, scheme: str, bearer_format: str):
    with LogMixin.context():
        SecuritySchemeObject(
            type="http",
            description=description,
            scheme=scheme,
            bearerFormat=bearer_format,
        )
        assert not LogMixin.logs


@given(st.text(), st.text(), INVALID_HTTP_AUTHENTICATION_SCHEMES, st.text())
def test_security_scheme_http_invalid(
    type_: str, description: str, scheme: str, bearer_format: str
):
    with LogMixin.context():
        SecuritySchemeObject(
            type=type_,
            description=description,
            scheme=scheme,
            bearerFormat=bearer_format,
        )
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError


@given(st.text(), st.sampled_from(VALID_HTTP_AUTHENTICATION_SCHEMES), st.text())
def test_security_scheme_oauth2_valid(
    description: str, scheme: str, bearer_format: str
):
    with LogMixin.context():
        SecuritySchemeObject(
            type="oauth2",
            description=description,
            scheme=scheme,
            bearerFormat=bearer_format,
            flows=OAuthFlowsObject(),
        )
        assert not LogMixin.logs


@given(st.text(), st.text(), INVALID_HTTP_AUTHENTICATION_SCHEMES, st.text())
def test_security_scheme_oauth2_invalid(
    type_: str, description: str, scheme: str, bearer_format: str
):
    with LogMixin.context():
        SecuritySchemeObject(
            type=type_,
            description=description,
            scheme=scheme,
            bearerFormat=bearer_format,
        )
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
