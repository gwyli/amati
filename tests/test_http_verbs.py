from pydantic import BaseModel, ValidationError
from hypothesis import given, strategies as st

from specs.validators import http_verbs as hv

from tests.helpers import helpers

import pytest

class HTTPVerbModel(BaseModel):
    verb: hv.HTTPVerb

@pytest.mark.parametrize("verb", hv.HTTP_VERBS)
def test_valid_http_verbs(verb):
    model = HTTPVerbModel(verb=verb)
    assert model.verb == verb

@given(st.text().filter(lambda x: x not in hv.HTTP_VERBS))
def test_random_strings(verb):
    with pytest.raises(ValidationError):
            HTTPVerbModel(verb=verb)

@given(helpers.everything_except(str))
def test_everything_else(verb):
    with pytest.raises(ValidationError):
        HTTPVerbModel(verb=verb)