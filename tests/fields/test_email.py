"""
Tests amati/fields/email.py
"""

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from amati import AmatiValueError
from amati.fields.email import Email

# I believe that there's an issue with the Hypothesis domain strategy
# as emails() and urls() unreliably exceeds deadlines. In this file there
# are several deadline extensions to prevent these failures.
# See https://github.com/HypothesisWorks/hypothesis/issues/4201.


@given(st.emails())
@settings(deadline=300)
def test_email_valid(email: str):
    Email(email)


@st.composite
def strings_except_emails(draw: st.DrawFn) -> str:
    candidate: str = draw(st.text())

    # The Hypothesis string shrinking algorithm ends up producing a valid RFC 5322 email
    # email sometimes. Exclude them.
    while re.match("[a-z0-9]+@[a-z0-9]+", candidate, flags=re.IGNORECASE):
        candidate = draw(st.text())  # pragma: no cover

    return candidate


@given(strings_except_emails())
def test_email_invalid(email: str):
    with pytest.raises(AmatiValueError):
        Email(email)
