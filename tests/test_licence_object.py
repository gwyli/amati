"""
Tests specs/validation/licence_object.py
"""

import pytest

from hypothesis import given, strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati.validators.licence_object import LicenceObject, VALID_LICENCES, VALID_URLS
from amati.warnings import InconsistencyWarning

from tests.helpers import helpers


VALID_IDENTIFIERS = list(VALID_LICENCES.keys())

INVALID_URLS = urls().filter(lambda x: x not in VALID_URLS)
INVALID_IDENTIFIERS = st.text().filter(lambda x: x not in VALID_IDENTIFIERS)


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_all_variables_correct(name: str, identifier: str):
    url = helpers.random_choice_empty(VALID_LICENCES[identifier])
    LicenceObject(name=name, identifier=identifier, url=url)


@given(helpers.text_excluding_empty_string(), st.text(), st.sampled_from(VALID_URLS))
def test_all_variables_random_identifier(name: str, identifier: str, url: str):
    with pytest.raises(ValueError):
        LicenceObject(name=name, identifier=identifier, url=url) # type: ignore


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS), INVALID_URLS)
def test_all_variables_random_url(name: str, identifier: str, url: str):
    with pytest.warns(InconsistencyWarning):
        LicenceObject(name=name, identifier=identifier, url=url) # type: ignore


@given(helpers.text_excluding_empty_string(), INVALID_IDENTIFIERS, INVALID_URLS)
def test_all_variables_random(name: str, identifier: str, url: str):
    with pytest.raises(ValidationError):
        with pytest.warns(InconsistencyWarning):
            LicenceObject(name=name, identifier=identifier, url=url) # type: ignore


@given(st.just('')) # This is the only case where name is empty
def test_name_invalid(name: str):
    with pytest.raises(ValidationError):
        LicenceObject(name=name)


def test_no_name():
    with pytest.raises(ValidationError):
        LicenceObject() # type: ignore


@given(helpers.text_excluding_empty_string(), INVALID_URLS)
def test_no_identifier_invalid_url(name: str, url: str):
    with pytest.warns(InconsistencyWarning):
        LicenceObject(name=name, url=url) # type: ignore


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_URLS))
def test_no_identifier_valid_url(name: str, url: str):
    LicenceObject(name=name, url=url) # type: ignore


@given(helpers.text_excluding_empty_string(), INVALID_IDENTIFIERS)
def test_invalid_identifier_no_url(name: str, identifier: str):
    with pytest.raises(ValueError):
        LicenceObject(name=name, identifier=identifier)


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_valid_identifier_no_url(name: str, identifier: str):
    LicenceObject(name=name, identifier=identifier)


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS),
       st.sampled_from(VALID_URLS))
def test_valid_identifier_invalid_url(name: str, identifier: str, url: str):
    # These lines are only reached when the identifier has a URL and the URL is
    # not associated with the identifier
    if url in VALID_LICENCES[identifier]: return
    if not VALID_LICENCES[identifier]: return

    with pytest.warns(InconsistencyWarning):
        LicenceObject(name=name, identifier=identifier, url=url) # type: ignore


@given(helpers.text_excluding_empty_string(), st.none(), st.none())
def test_identifier_url_none(name: str, identifier: str, url: str):
    LicenceObject(name=name, identifier=identifier, url=url) # type: ignore


@given(helpers.text_excluding_empty_string())
def test_name_only(name: str):
    LicenceObject(name=name)
