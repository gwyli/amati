"""
Tests amati/validators/http_status_codes.py
"""

import pytest

from hypothesis import given
from hypothesis.strategies import integers, sampled_from
from pydantic import ValidationError

from amati.logging import LogMixin
from amati.validators.generic import GenericObject
from amati.validators.http_status_codes import HTTPStatusCode, ASSIGNED_HTTP_STATUS_CODES

from tests.helpers import helpers


class Model(GenericObject):
    value: HTTPStatusCode


UNASSIGNED_HTTP_STATUS_CODES = set(range(100, 599)) - ASSIGNED_HTTP_STATUS_CODES


@given(sampled_from(list(ASSIGNED_HTTP_STATUS_CODES)))
def test_assigned_status_code(status_code: int):
    Model(value=status_code)


@given(sampled_from(list(UNASSIGNED_HTTP_STATUS_CODES)))
def test_unassigned_status_codes(status_code: int):
    with LogMixin.context():
        Model(value=status_code)
        assert LogMixin.logs


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
