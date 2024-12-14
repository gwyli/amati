"""
Tests amati/fields/email.py
"""

import pytest
from abnf import ParseError
from hypothesis import given, settings
from hypothesis import strategies as st

from amati.fields.email import Email
from amati.validators.generic import GenericObject


class EmailModel(GenericObject):
    email: Email


# I believe that there's an issue with the Hypothesis domain strategy
# as emails() and urls() unreliably exceeds deadlines. In this file there
# are several deadline extensions to prevent these failures.


@given(st.emails())
@settings(deadline=300)
def test_email_valid(email: str):
    EmailModel(email=email)


@st.composite
def strings_except_emails(draw: st.DrawFn) -> str:
    # Draw both a string and an email
    candidate: str = draw(st.text())
    email: str = draw(st.emails())

    # If our candidate matches any possible email, draw again; highly unlikely.
    while candidate == email:
        candidate = draw(st.text())  # pragma: no cover

    return candidate


@given(strings_except_emails())
def test_email_invalid(email: str):
    with pytest.raises(ParseError):
        EmailModel(email=email)
