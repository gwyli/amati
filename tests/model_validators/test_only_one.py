"""
Tests amati.model_validators.only_one_of
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
    _only_one = mv.only_one_of(fields=[])
    _reference: Reference = Reference(title="test")


class OnlyOneNoRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _only_one_of = mv.only_one_of()
    _reference: ClassVar[Reference] = Reference(title="test")


class OnlyOneWithRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _only_one_of = mv.only_one_of(fields=["name", "age"])
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
def test_only_one_of_no_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty. Uses both None and falsy values."""

    # Tests with None
    with LogMixin.context():
        model = OnlyOneNoRestrictions(name=name, age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneNoRestrictions(name=None, age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneNoRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneNoRestrictions(name=name, age=age, music=None)
        assert LogMixin.logs

    model = OnlyOneNoRestrictions(name=None, age=None, music=music)
    assert model.music

    model = OnlyOneNoRestrictions(name=name, age=None, music=None)
    assert model.name

    model = OnlyOneNoRestrictions(name=None, age=age, music=None)
    assert model.age == age

    # Tests with falsy values
    with LogMixin.context():
        model = OnlyOneNoRestrictions(name="", age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneNoRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneNoRestrictions(name=name, age=age, music=[])
        assert LogMixin.logs

    model = OnlyOneNoRestrictions(name="", age=None, music=music)
    assert model.music

    model = OnlyOneNoRestrictions(name=name, age=None, music=[])
    assert model.name

    model = OnlyOneNoRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with LogMixin.context():
        OnlyOneNoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        OnlyOneNoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        OnlyOneNoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        OnlyOneNoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_only_one_of_with_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty with a field restriction.
    Uses both None and falsy values."""

    # Tests with None
    with LogMixin.context():
        model = OnlyOneWithRestrictions(name=name, age=age, music=music)
        assert LogMixin.logs

    model = OnlyOneWithRestrictions(name=None, age=age, music=music)
    assert model.age == age and model.music

    model = OnlyOneWithRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    with LogMixin.context():
        model = OnlyOneWithRestrictions(name=name, age=age, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneWithRestrictions(name=None, age=None, music=music)
        assert LogMixin.logs

    model = OnlyOneWithRestrictions(name=name, age=None, music=None)
    assert model.name

    model = OnlyOneWithRestrictions(name=None, age=age, music=None)
    assert model.age == age

    # Tests with falsy values
    model = OnlyOneWithRestrictions(name="", age=age, music=music)
    assert model.age == age and model.music

    model = OnlyOneWithRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    with LogMixin.context():
        model = OnlyOneWithRestrictions(name=name, age=age, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        model = OnlyOneWithRestrictions(name="", age=None, music=music)
        assert LogMixin.logs

    model = OnlyOneWithRestrictions(name=name, age=None, music=[])
    assert model.name

    model = OnlyOneWithRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with LogMixin.context():
        OnlyOneNoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        OnlyOneNoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        OnlyOneNoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        OnlyOneNoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs
