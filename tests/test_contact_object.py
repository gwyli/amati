"""
Tests amati/validators/contact_object.py
"""

import pytest
from abnf import ParseError
from hypothesis import given, strategies as st
from hypothesis.provisional import urls

from amati.validators.contact_object import ContactObject, Email
from amati.validators.generic import GenericObject


class EmailModel(GenericObject):
    email: Email


@given(st.emails())
def test_email_valid(email: str):
    EmailModel(email=email)


@st.composite
def strings_except_emails(draw: st.DrawFn) -> str:
    # Draw both a string and an email
    candidate: str = draw(st.text())
    email: str = draw(st.emails())

    # If our candidate matches any possible email, draw again; highly unlikely.
    while candidate == email:
        candidate = draw(st.text()) # pragma: no cover

    return candidate


@given(strings_except_emails())
def test_email_invalid(email: str):
    with pytest.raises(ParseError):
        EmailModel(email=email)


@given(st.text(), urls(), st.emails())
def test_contact_object(name: str, url: str, email: str):
    ContactObject(name=name, url=url, email=email) # type: ignore
