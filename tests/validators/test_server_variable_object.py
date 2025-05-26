"""
Tests amati/validators/oas311.py - ServerVariableObject
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from amati.logging import LogMixin
from amati.validators.oas311 import ServerVariableObject
from tests import helpers


@st.composite
def valid_server_variable(draw: st.DrawFn) -> dict[str, list[str] | str]:

    enum: list[str] = draw(st.lists(helpers.text_excluding_empty_string(), min_size=1))
    default: str = draw(st.sampled_from(enum))
    return {"enum": enum, "default": default, "description": draw(st.text())}


@given(valid_server_variable())
def test_server_variable_object(xserver_variable: dict[str, list[str] | str]):
    with LogMixin.context():
        ServerVariableObject(**xserver_variable)  # type: ignore
        assert not LogMixin.logs


@given(st.text())
def test_empty_enum(default: str):
    with pytest.raises(ValidationError):
        ServerVariableObject(enum=[], default=default)


@st.composite
def invalid_server_variable(draw: st.DrawFn) -> tuple[list[str], str]:

    enum: list[str] = draw(st.lists(helpers.text_excluding_empty_string(), min_size=1))
    default: str = draw(st.text().filter(lambda x: x not in enum and x != ""))
    return enum, default


@given(invalid_server_variable())
def test_invalid_default(xserver_variable: tuple[list[str], str]):
    enum, default = xserver_variable
    with LogMixin.context():
        ServerVariableObject(enum=enum, default=default)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
