from pydantic import ValidationError

from hypothesis import given, strategies as st
from hypothesis.provisional import urls

from specs.validators import licence_object as lo
from specs.warnings import InconsistencyWarning

from tests.helpers import helpers

import pytest

VALID_IDENTIFIERS = list(lo.VALID_LICENCES.keys())
VALID_URLS = lo.VALID_URLS

INVALID_URLS = urls().filter(lambda x: x not in VALID_URLS)
INVALID_IDENTIFIERS = st.text().filter(lambda x: x not in VALID_IDENTIFIERS)


@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_all_variables_correct(name, identifier):
    url = helpers.random_choice_empty(lo.VALID_LICENCES[identifier])
    lo.LicenceObject(name=name, identifier=identifier, url=url)

@given(helpers.text_excluding_empty_string(), st.text(), st.sampled_from(VALID_URLS))
def test_all_variables_random_identifier(name, identifier, url):
    with pytest.raises(ValueError):
            model = lo.LicenceObject(name=name, identifier=identifier, url=url)

@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS), INVALID_URLS)
def test_all_variables_random_url(name, identifier, url):
    with pytest.warns(InconsistencyWarning):
            model = lo.LicenceObject(name=name, identifier=identifier, url=url)

@given(helpers.text_excluding_empty_string(), INVALID_IDENTIFIERS, INVALID_URLS)
def test_all_variables_random(name, identifier, url):
    with pytest.raises(ValidationError):
            with pytest.warns(InconsistencyWarning):
                model = lo.LicenceObject(name=name, identifier=identifier, url=url)

@given(st.just('')) # This is the only case where name is empty
def test_name_invalid(name):
    with pytest.raises(ValidationError):
        lo.LicenceObject(name=name)

def test_no_name():
    with pytest.raises(ValidationError):
        lo.LicenceObject()

@given(helpers.text_excluding_empty_string(), INVALID_URLS)
def test_no_identifier_invalid_url(name, url):
    with pytest.warns(InconsistencyWarning):
        model = lo.LicenceObject(name=name, url=url)

@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_URLS))
def test_no_identifier_valid_url(name, url):
    model = lo.LicenceObject(name=name, url=url)

@given(helpers.text_excluding_empty_string(), INVALID_IDENTIFIERS)
def test_invalid_identifier_no_url(name, identifier):
    with pytest.raises(ValueError):
         model = lo.LicenceObject(name=name, identifier=identifier)

@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_valid_identifier_no_url(name, identifier):
    model = lo.LicenceObject(name=name, identifier=identifier)

@given(helpers.text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS), st.sampled_from(VALID_URLS))
def test_valid_identifier_invalid_url(name, identifier, url):
    # This line is only reached when the identifier has a URL and the URL is not associated with the identifier
    if url in lo.VALID_LICENCES[identifier]: return
    if not lo.VALID_LICENCES[identifier]: return
    with pytest.warns(InconsistencyWarning):
         model = lo.LicenceObject(name=name, identifier=identifier, url=url)

@given(helpers.text_excluding_empty_string(), st.none(), st.none())
def test_identifier_url_none(name, identifier, url):
    model = lo.LicenceObject(name=name, identifier=identifier, url=url)

@given(helpers.text_excluding_empty_string())
def test_name_only(name):
    model = lo.LicenceObject(name=name)