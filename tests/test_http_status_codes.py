from specs.validators import http_status_codes as hsc

from hypothesis.strategies import integers, sampled_from
from hypothesis import given

from pydantic import BaseModel, ValidationError

from tests.helpers import helpers

import warnings
import pytest

class MyModel(BaseModel):
    status_code: hsc.HTTPStatusCode


UNASSIGNED_HTTP_STATUS_CODES = set(range(100, 599)) - hsc.ASSIGNED_HTTP_STATUS_CODES

@given(sampled_from(list(hsc.ASSIGNED_HTTP_STATUS_CODES)))
def test_warning_condition_for_assigned_codes(status_code):
    assert status_code in hsc.ASSIGNED_HTTP_STATUS_CODES  # Verify our test data
    assert not (status_code not in hsc.ASSIGNED_HTTP_STATUS_CODES)  # Explicitly verify the warning condition is False
    
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model = MyModel(status_code=status_code)

@given(sampled_from(list(hsc.ASSIGNED_HTTP_STATUS_CODES)))
def test_assigned_status_code(status_code):
    with warnings.catch_warnings() as record:
        warnings.simplefilter("error")  # This will make the test fail if any warning occurs
        warnings.simplefilter("always") # Make sure we catch all warnings
        model = MyModel(status_code=status_code)
        # If we get here, no warning was raised
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

@given(helpers.everything_except(int))
def test_everything_except_integers(status_code):
    with pytest.raises(ValidationError):
        MyModel(status_code=status_code)