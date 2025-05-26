"""
Tests amati/fields/spdx_licences.py
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls

from amati import AmatiValueError
from amati.fields.spdx_licences import (
    SPDXURL,
    VALID_LICENCES,
    VALID_URLS,
    SPDXIdentifier,
)

VALID_IDENTIFIERS = list(VALID_LICENCES.keys())

INVALID_URLS = urls().filter(lambda x: x not in VALID_URLS)
INVALID_IDENTIFIERS = st.text().filter(lambda x: x not in VALID_IDENTIFIERS)


@given(st.sampled_from(VALID_IDENTIFIERS))
def test_spdx_identifier_valid(value: str):
    SPDXIdentifier(value)


@given(st.text())
def test_spdx_identifier_invalid(value: str):
    with pytest.raises(AmatiValueError):
        SPDXIdentifier(value)


@given(st.sampled_from(VALID_URLS))
def test_spdx_url_valid(value: str):
    # Expecting that the URL is passed as a string from JSON
    SPDXURL(value)


@given(urls())
def test_spdx_url_invalid(value: str):
    with pytest.raises(AmatiValueError):
        SPDXURL(value)
