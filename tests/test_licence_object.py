from pydantic import ValidationError

from hypothesis import given, strategies as st
from hypothesis.provisional import urls

from specs.validators import licence_object as ho

import pytest


@given(st.text().filter(lambda x: x != ''), st.sampled_from(list(ho.VALID_LICENCES.keys())), urls())
def test_all_variables(name, identifier, url):
    model = ho.LicenceObject(name=name, identifier=identifier, url=url)

@given(st.text().filter(lambda x: x != ''), st.none(), urls())
def test_identifier_none(name, identifier, url):
    with pytest.warns(ho.InconsistencyWarning):
        model = ho.LicenceObject(name=name, identifier=identifier, url=url)

@given(st.text().filter(lambda x: x != ''), st.sampled_from(list(ho.VALID_LICENCES.keys())), st.none())
def test_url_none(name, identifier, url):
    model = ho.LicenceObject(name=name, identifier=identifier, url=url)

@given(st.text().filter(lambda x: x != ''), st.none(), st.none())
def test_identifier_url_none(name, identifier, url):
    model = ho.LicenceObject(name=name, identifier=identifier, url=url)

@given(st.text().filter(lambda x: x != ''))
def test_identifier_url_empty(name):
    model = ho.LicenceObject(name=name)

@given(st.text().filter(lambda x: x != ''), st.text())
def test_identifier_invalid(name, identifier):
    if identifier in ho.VALID_LICENCES: return
    with pytest.raises(ValueError):
        ho.LicenceObject(name=name, identifier=identifier)

@given(st.just('')) # This is the only case where name is empty
def test_name_invalid(name):
    with pytest.raises(ValidationError):
        ho.LicenceObject(name=name)
