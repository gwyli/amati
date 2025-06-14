"""
Tests amati.model_validators.all_of
"""

from sys import float_info
from typing import ClassVar, Optional

from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from amati import Reference
from amati import model_validators as mv
from amati.logging import LogMixin
from tests.helpers import text_excluding_empty_string

MIN = int(float_info.min)


class EmptyObject(BaseModel):
    _at_least_one_of = mv.all_of()
    _reference: Reference = Reference(title="test")


class AllNoRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _all_of = mv.all_of()
    _reference: ClassVar[Reference] = Reference(title="test")


class AllWithRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _all_of = mv.all_of(fields=["name", "age"])
    _reference: ClassVar[Reference] = Reference(title="test")


def test_empty_object():
    with LogMixin.context():
        EmptyObject()
        assert not LogMixin.logs


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_all_of_no_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty. Uses both None and falsy values."""

    # Tests with None
    model = AllNoRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    with LogMixin.context():
        AllNoRestrictions(name=None, age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=name, age=age, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=None, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=name, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=None, age=age, music=None)
        assert LogMixin.logs

    # Tests with falsy values
    with LogMixin.context():
        AllNoRestrictions(name="", age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=name, age=age, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name="", age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=name, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name="", age=age, music=[])
        assert LogMixin.logs

    # Test when no fields are provided
    with LogMixin.context():
        AllNoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_all_of_with_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty with a field restriction.
    Uses both None and falsy values."""

    # Tests with None
    model = AllWithRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    with LogMixin.context():
        AllWithRestrictions(name=None, age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllWithRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    model = AllWithRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    with LogMixin.context():
        model = AllWithRestrictions(name=None, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllWithRestrictions(name=name, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllWithRestrictions(name=None, age=age, music=None)
        assert LogMixin.logs

    # Tests with falsy values
    with LogMixin.context():
        AllWithRestrictions(name="", age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllWithRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    model = AllWithRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    with LogMixin.context():
        model = AllWithRestrictions(name="", age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        AllWithRestrictions(name=name, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AllWithRestrictions(name="", age=age, music=[])
        assert LogMixin.logs

    # Test when no fields are provided
    with LogMixin.context():
        AllNoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AllNoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs
