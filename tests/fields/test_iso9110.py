"""
Tests amati/fields/spdx_licences.py
"""

from hypothesis import given
from hypothesis import strategies as st

from amati.fields.iso9110 import HTTP_AUTHENTICATION_SCHEMES, HTTPAuthenticationScheme
from amati.logging import LogMixin
from amati.validators.generic import GenericObject

VALID_HTTP_AUTHENTICATION_SCHEMES: list[str] = list(HTTP_AUTHENTICATION_SCHEMES)
INVALID_HTTP_AUTHENTICATION_SCHEMES = st.text().filter(
    lambda x: x not in HTTP_AUTHENTICATION_SCHEMES
)


class HTTPAuthenticationSchemeModel(GenericObject):
    http_authentication_scheme: HTTPAuthenticationScheme


@given(st.sampled_from(VALID_HTTP_AUTHENTICATION_SCHEMES))
def test_http_authentication_scheme_valid(http_authentication_scheme: str):
    HTTPAuthenticationSchemeModel(http_authentication_scheme=http_authentication_scheme)


@st.composite
def strings_without_valid_http_authentication_schemes(draw: st.DrawFn) -> str:
    candidate: str = draw(st.text())

    # The Hypothesis string shrinking algorithm ends up producing a valid RFC 5322 email
    # email sometimes. Exclude them.
    while candidate in VALID_HTTP_AUTHENTICATION_SCHEMES:
        candidate = draw(st.text())  # pragma: no cover

    return candidate


@given(strings_without_valid_http_authentication_schemes())
def test_http_authentication_scheme_invalid(http_authentication_scheme: str):
    with LogMixin.context():
        HTTPAuthenticationSchemeModel(
            http_authentication_scheme=http_authentication_scheme
        )
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
        assert LogMixin.logs[0].reference is not None
