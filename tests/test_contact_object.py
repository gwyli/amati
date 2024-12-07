"""
Tests amati/validators/contact_object.py
"""

from hypothesis import given, strategies as st
from hypothesis.provisional import urls

from amati.validators.contact_object import ContactObject, Email
from amati.validators.generic import GenericObject


class EmailModel(GenericObject):
    email: Email


@given(st.emails())
def test_email_valid(email: str):
    EmailModel(email=email)


@given(st.text(), urls(), st.emails())
def test_contact_object(name: str, url: str, email: str):
    ContactObject(name=name, url=url, email=email) # type: ignore
