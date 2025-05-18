"""
Tests amati/references.py
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import AnyUrl

from amati.validators.reference_object import Reference, ReferenceModel
from tests.helpers import text_excluding_empty_string


@given(st.text(), st.text(), urls())
def test_valid_reference_object(title: str, section: str, url: str):
    ReferenceModel(title=title, url=url)  # type: ignore
    ref: Reference = ReferenceModel(title=title, section=section, url=str(url))

    assert ref.title == title
    assert ref.section == section
    assert ref.url == str(AnyUrl(url))


@given(text_excluding_empty_string())
def test_invalid_reference_object(url: str):

    with pytest.raises(ValueError):
        ReferenceModel(url=url)  # type: ignore

    with pytest.raises(ValueError):
        ReferenceModel(title=url, url=None)  # type: ignore
