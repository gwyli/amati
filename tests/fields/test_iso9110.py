"""
Tests amati/fields/spdx_licences.py
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from amati import AmatiValueError
from amati.fields.iso9110 import HTTP_AUTHENTICATION_SCHEMES, HTTPAuthenticationScheme

VALID_HTTP_AUTHENTICATION_SCHEMES: list[str] = list(HTTP_AUTHENTICATION_SCHEMES)
INVALID_HTTP_AUTHENTICATION_SCHEMES = st.text().filter(
    lambda x: x not in HTTP_AUTHENTICATION_SCHEMES
)


@given(st.sampled_from(VALID_HTTP_AUTHENTICATION_SCHEMES))
def test_http_authentication_scheme_valid(value: str):
    HTTPAuthenticationScheme(value)


@st.composite
def strings_without_valid_http_authentication_schemes(draw: st.DrawFn) -> str:
    candidate: str = draw(st.text())

    # The Hypothesis string shrinking algorithm ends up producing a valid RFC 5322 email
    # email sometimes. Exclude them.
    while candidate in VALID_HTTP_AUTHENTICATION_SCHEMES:
        candidate = draw(st.text())  # pragma: no cover

    return candidate


@given(strings_without_valid_http_authentication_schemes())
def test_http_authentication_scheme_invalid(value: str):
    with pytest.raises(AmatiValueError):
        HTTPAuthenticationScheme(value)
