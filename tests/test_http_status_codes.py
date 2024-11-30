import pytest
from pydantic import ValidationError
from validators import http_status_codes as hsc
from pydantic import BaseModel
from hypothesis import given
from hypothesis.strategies import integers, sampled_from, from_type
from itertools import chain
import warnings

warnings.simplefilter("always")

class MyModel(BaseModel):
    status_code: hsc.HTTPStatusCode


UNASSIGNED_HTTP_STATUS_CODES = set(range(100, 599)) - hsc.ASSIGNED_HTTP_STATUS_CODES

def everything_except(excluded_types):
    return (
        from_type(type)
        .flatmap(from_type)
        .filter(lambda x: not isinstance(x, excluded_types))
    )

@given(sampled_from(list(hsc.ASSIGNED_HTTP_STATUS_CODES)))
def test_assigned_status_code(status_code):
    model = MyModel(status_code=status_code)
    assert model.status_code == status_code

@given(sampled_from(list(UNASSIGNED_HTTP_STATUS_CODES)))
def test_unassigned_status_codes(status_code):
    with pytest.warns(UserWarning, match=f"Status code {status_code} is unassigned or invalid."):
        model = MyModel(status_code=status_code)
    assert model.status_code == status_code

@given(integers(max_value=99))
def test_invalid_status_code_below_range(status_code):
    with pytest.raises(ValidationError):
        MyModel(status_code=status_code)

@given(integers(min_value=600))
def test_invalid_status_code_above_range(status_code):
    with pytest.raises(ValidationError):
        MyModel(status_code=status_code)

@given(everything_except(int))
def test_everything_except_integers(status_code):
    with pytest.raises(ValidationError):
        MyModel(status_code=status_code)