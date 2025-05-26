"""
Tests amati/references.py
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls

from amati import AmatiReferenceException, Reference


@given(st.text(), st.text(), urls())
def test_valid_reference_object(title: str, section: str, url: str):
    ref = Reference(title, section, url)

    assert ref.title == title
    assert ref.section == section
    assert ref.url == url


def test_invalid_reference_object():

    with pytest.raises(AmatiReferenceException):
        Reference()
