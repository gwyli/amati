"""
Tests amati/fields/spdx_licences.py
"""

from hypothesis import given, strategies as st
from hypothesis.provisional import urls

from amati.fields.spdx_licences import SPDXIdentifier, SPDXURL, VALID_LICENCES, VALID_URLS
from amati.logging import LogMixin
from amati.validators.generic import GenericObject

VALID_IDENTIFIERS = list(VALID_LICENCES.keys())

INVALID_URLS = urls().filter(lambda x: x not in VALID_URLS)
INVALID_IDENTIFIERS = st.text().filter(lambda x: x not in VALID_IDENTIFIERS)

class IdentifierModel(GenericObject):
    identifier: SPDXIdentifier

class URLModel(GenericObject):
    url: SPDXURL


@given(st.sampled_from(VALID_IDENTIFIERS))
def test_spdx_identifier_valid(identifier: str):
    IdentifierModel(identifier=identifier)


@given(st.text())
def test_spdx_identifier_invalid(identifier: str):
    with LogMixin.context():
        IdentifierModel(identifier=identifier)
        assert LogMixin.logs


@given(st.sampled_from(VALID_URLS))
def test_spdx_url_valid(url: str):
    # Expecting that the URL is passed as a string from JSON
    URLModel(url=url)


@given(urls())
def test_spdx_url_invalid(url: str):
    with LogMixin.context():
        URLModel(url=url)
        assert LogMixin.logs
