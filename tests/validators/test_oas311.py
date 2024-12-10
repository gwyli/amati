"""
Tests amati/validators/oas311.py
"""

from hypothesis import given, settings, strategies as st
from hypothesis.provisional import urls

from amati.validators.oas311 import ContactObject

@given(st.text(), urls(), st.emails())
@settings(deadline=1000)
def test_contact_object(name: str, url: str, email: str):
    ContactObject(name=name, url=url, email=email) # type: ignore