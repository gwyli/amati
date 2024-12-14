"""
Tests amati/validators/oas311.py - LicenceObject
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati.fields.spdx_licences import VALID_LICENCES, VALID_URLS
from amati.logging import LogMixin
from amati.validators.oas311 import LicenceObject
from tests import helpers

VALID_IDENTIFIERS = list(VALID_LICENCES.keys())

INVALID_URLS = urls().filter(lambda x: x not in VALID_URLS)
INVALID_IDENTIFIERS = st.text().filter(lambda x: x not in VALID_IDENTIFIERS)


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_all_variables_correct(name: str, identifier: str):
    url = helpers.random_choice_empty(VALID_LICENCES[identifier])
    LicenceObject(name=name, identifier=identifier, url=url)


@given(helpers.text_excluding_empty_string(), INVALID_IDENTIFIERS, INVALID_URLS)
def test_all_variables_random(name: str, identifier: str, url: str):
    with LogMixin.context():
        LicenceObject(name=name, identifier=identifier, url=url)
        assert LogMixin.logs


@given(st.just(""))  # This is the only case where name is empty
def test_name_invalid(name: str):
    with pytest.raises(ValidationError):
        LicenceObject(name=name)


def test_no_name():
    with pytest.raises(ValidationError):
        LicenceObject()  # type: ignore


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_valid_identifier_no_url(name: str, identifier: str):
    LicenceObject(name=name, identifier=identifier)


@given(
    helpers.text_excluding_empty_string(),
    st.sampled_from(VALID_IDENTIFIERS),
    st.sampled_from(VALID_URLS),
)
def test_valid_identifier_invalid_url(name: str, identifier: str, url: str):
    # These lines are only reached when the identifier has a URL and the URL is
    # not associated with the identifier
    if url in VALID_LICENCES[identifier]:
        return
    if not VALID_LICENCES[identifier]:
        return

    with LogMixin.context():
        LicenceObject(name=name, identifier=identifier, url=url)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == Warning


@given(helpers.text_excluding_empty_string(), st.none(), st.none())
def test_identifier_url_none(name: str, identifier: str, url: str):
    LicenceObject(name=name, identifier=identifier, url=url)


@given(helpers.text_excluding_empty_string())
def test_name_only(name: str):
    LicenceObject(name=name)
