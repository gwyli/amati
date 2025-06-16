"""
Tests amati/validators/oas311.py - LicenceObject
"""

import random

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati.fields.spdx_licences import VALID_LICENCES, VALID_URLS
from amati.logging import LogMixin
from amati.validators.oas311 import LicenceObject
from tests.helpers import none_and_empty_string, text_excluding_empty_string

VALID_IDENTIFIERS = list(VALID_LICENCES.keys())
VALID_IDENTIFIERS_WITH_URLS = [k for k, v in VALID_LICENCES.items() if v]

INVALID_URLS = urls().filter(lambda x: x not in VALID_URLS)
INVALID_IDENTIFIERS = st.text().filter(lambda x: x not in VALID_IDENTIFIERS)


@given(
    text_excluding_empty_string(),
    st.sampled_from(VALID_IDENTIFIERS),
    st.sampled_from(VALID_URLS),
)
def test_name_valid(name: str, identifier: str, url: str):
    with LogMixin.context():
        LicenceObject(name=name, identifier=identifier)  # type: ignore
        LicenceObject(name=name, url=url)  # type: ignore
        assert not LogMixin.logs


@given(
    none_and_empty_string(str),
    st.sampled_from(VALID_IDENTIFIERS),
    st.sampled_from(VALID_URLS),
)
def test_name_invalid(name: str, identifier: str, url: str):

    with pytest.raises(ValidationError):
        LicenceObject(name=name, identifier=identifier)  # type: ignore

    with pytest.raises(ValidationError):
        LicenceObject(name=name, url=url)  # type: ignore


@given(text_excluding_empty_string())
def test_case_1(name: str):
    """
    No URL or identifier
    """
    with LogMixin.context():
        LicenceObject(name=name, identifier=None, url=None)
        assert LogMixin.logs
        assert LogMixin.logs[0].message
        assert LogMixin.logs[0].type == ValueError

    # URI('') will error as the empty string is an invalid URI
    with pytest.raises(ValidationError):
        LicenceObject(name=name, identifier="", url=None)  # type: ignore

    # URI('') will error as the empty string is an invalid URI
    with pytest.raises(ValidationError):
        LicenceObject(name=name, identifier=None, url="")  # type: ignore


@given(text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS))
def test_case_2_valid(name: str, identifier: str):
    """Identifier only"""
    with LogMixin.context():
        LicenceObject(name=name, identifier=identifier)  # type: ignore
        assert not LogMixin.logs


@given(text_excluding_empty_string(), INVALID_IDENTIFIERS)
def test_case_2_invalid(name: str, identifier: str):
    """Identifier only"""
    with pytest.raises(ValidationError):
        LicenceObject(name=name, identifier=identifier)  # type: ignore


@given(text_excluding_empty_string(), st.sampled_from(VALID_URLS))
def test_case_3_valid(name: str, url: str):
    """URI only"""
    with LogMixin.context():
        LicenceObject(name=name, url=url)  # type: ignore
        assert not LogMixin.logs


@given(text_excluding_empty_string(), INVALID_URLS)
def test_case_3_invalid(name: str, url: str):
    """URI only"""
    with LogMixin.context():
        LicenceObject(name=name, url=url)  # type: ignore
        assert LogMixin.logs
        assert LogMixin.logs[0].message
        assert LogMixin.logs[0].type == Warning


def unassociated_url(identifier: str) -> str:  # type: ignore
    """
    Generates SPDX URLs which are unassociated
    with the identifier
    """

    while id_ := random.choice(VALID_IDENTIFIERS):
        # Exist just in case the random choice is the same
        # as the choice being examined.
        if id_ == identifier:  # pragma: no cover
            continue

        try:
            choices = VALID_LICENCES.get(id_)

            if choices:
                return random.choice(choices)

        # Won't always be hit, but some identifiers
        # don't have any associated URLs
        except IndexError:  # pragma: no cover
            continue


@given(text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS_WITH_URLS))
def test_case_4_id_url_match(name: str, identifier: str):
    url = random.choice(VALID_LICENCES[identifier])

    with LogMixin.context():
        LicenceObject(name=name, identifier=identifier, url=url)  # type: ignore
        assert LogMixin.logs
        assert LogMixin.logs[0].message
        assert LogMixin.logs[0].type == ValueError


@given(text_excluding_empty_string(), st.sampled_from(VALID_IDENTIFIERS_WITH_URLS))
def test_case_4_id_url_match_no(name: str, identifier: str):
    url = unassociated_url(identifier)
    with LogMixin.context():
        LicenceObject(name=name, identifier=identifier, url=url)  # type: ignore
        assert LogMixin.logs[0].message
        assert LogMixin.logs[0].type == ValueError
        assert (
            LogMixin.logs[1].message
            == f"{url} is not associated with the identifier {identifier}"
        )
        assert LogMixin.logs[1].type == Warning
