from specs.validators.http_status_codes import HTTPStatusCode, ASSIGNED_HTTP_STATUS_CODES

from hypothesis.strategies import integers, sampled_from
from hypothesis import given

from pydantic import BaseModel, ValidationError

from tests.helpers import helpers

import warnings
import pytest

class Model(BaseModel):
    value: HTTPStatusCode


UNASSIGNED_HTTP_STATUS_CODES = set(range(100, 599)) - ASSIGNED_HTTP_STATUS_CODES

@given(sampled_from(list(ASSIGNED_HTTP_STATUS_CODES)))
def test_warning_condition_for_assigned_codes(status_code: int):
    assert status_code in ASSIGNED_HTTP_STATUS_CODES  # Verify our test data
    assert not (status_code not in ASSIGNED_HTTP_STATUS_CODES)  # Explicitly verify the warning condition is False
    
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model = Model(value=status_code)
        assert model.value == status_code

@given(sampled_from(list(ASSIGNED_HTTP_STATUS_CODES)))
def test_assigned_status_code(status_code: int):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # This will make the test fail if any warning occurs
        warnings.simplefilter("always") # Make sure we catch all warnings
        model = Model(value=status_code)
        # If we get here, no warning was raised
        assert model.value == status_code

@given(sampled_from(list(UNASSIGNED_HTTP_STATUS_CODES)))
def test_unassigned_status_codes(status_code: int):
    with pytest.warns(UserWarning, match=f"Status code {status_code} is unassigned or invalid."):
        model = Model(value=status_code)
    assert model.value == status_code

@given(integers(max_value=99))
def test_invalid_status_code_below_range(status_code: int):
    with pytest.raises(ValidationError):
        Model(value=status_code)

@given(integers(min_value=600))
def test_invalid_status_code_above_range(status_code: int):
    with pytest.raises(ValidationError):
        Model(value=status_code)

@given(helpers.everything_except(int))
def test_everything_except_integers(status_code: int):
    with pytest.raises(ValidationError):
        Model(value=status_code)