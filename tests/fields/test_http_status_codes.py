"""
Tests amati/fields/http_status_codes.py
"""

from typing import Any

import pytest
from hypothesis import given
from hypothesis.strategies import integers, sampled_from

from amati import AmatiValueError
from amati.fields.http_status_codes import HTTP_STATUS_CODES, HTTPStatusCode
from tests import helpers

REGISTERED_HTTP_STATUS_CODES = list(HTTP_STATUS_CODES.keys())
HTTP_STATUS_CODE_RANGES = ["1XX", "2XX", "3XX", "4XX", "5XX"]


@given(sampled_from(REGISTERED_HTTP_STATUS_CODES))
def test_registered_status_code(value: str):
    result = HTTPStatusCode(value)

    if HTTP_STATUS_CODES[value] == "Unassigned":
        assert result.is_assigned is False

    assert result.is_registered is True


@given(integers(max_value=99))
def test_invalid_status_code_below_range(value: str):
    with pytest.raises(AmatiValueError):
        HTTPStatusCode(value)


@given(integers(min_value=600))
def test_invalid_status_code_above_range(value: str):
    with pytest.raises(AmatiValueError):
        HTTPStatusCode(value)


@given(sampled_from(HTTP_STATUS_CODE_RANGES))
def test_status_code_range(value: str):
    result = HTTPStatusCode(value)

    assert result.is_registered is False
    assert result.is_range is True


@given(helpers.everything_except(int))
def test_everything_except_integers(value: Any):
    with pytest.raises(AmatiValueError):
        HTTPStatusCode(value)  # type: ignore
