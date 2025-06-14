"""
Tests amati.model_validators.at_least_one_of
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
    _at_least_one_of = mv.at_least_one_of()


class AtLeastOneNoRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _at_least_one_of = mv.at_least_one_of()
    _reference: ClassVar[Reference] = Reference(title="test")


class AtLeastOneWithRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _at_least_one_of = mv.at_least_one_of(fields=["name", "age"])
    _reference: ClassVar[Reference] = Reference(title="test")


class AtLeastOneWithTwoRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _at_least_one_of_name = mv.at_least_one_of(fields=["name"])
    _at_least_one_of_age = mv.at_least_one_of(fields=["age"])
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
def test_at_least_one_of_no_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty. Uses both None and falsy values."""

    # Tests with None
    model = AtLeastOneNoRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    model = AtLeastOneNoRestrictions(name=None, age=age, music=music)
    assert model.age == age and model.music

    model = AtLeastOneNoRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    model = AtLeastOneNoRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    model = AtLeastOneNoRestrictions(name=None, age=None, music=music)
    assert model.music

    model = AtLeastOneNoRestrictions(name=name, age=None, music=None)
    assert model.name

    model = AtLeastOneNoRestrictions(name=None, age=age, music=None)
    assert model.age == age

    # Tests with falsy values
    model = AtLeastOneNoRestrictions(name="", age=age, music=music)
    assert model.age == age and model.music

    model = AtLeastOneNoRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    model = AtLeastOneNoRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    model = AtLeastOneNoRestrictions(name="", age=None, music=music)
    assert model.music

    model = AtLeastOneNoRestrictions(name=name, age=None, music=[])
    assert model.name

    model = AtLeastOneNoRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with LogMixin.context():
        AtLeastOneNoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneNoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneNoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneNoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_at_least_one_of_with_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty with a field restriction.
    Uses both None and falsy values."""

    # Tests with None
    model = AtLeastOneWithRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    model = AtLeastOneWithRestrictions(name=None, age=age, music=music)
    assert model.age == age and model.music

    model = AtLeastOneWithRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    model = AtLeastOneWithRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    with LogMixin.context():
        model = AtLeastOneWithRestrictions(name=None, age=None, music=music)
        assert LogMixin.logs

    model = AtLeastOneWithRestrictions(name=name, age=None, music=None)
    assert model.name

    model = AtLeastOneWithRestrictions(name=None, age=age, music=None)
    assert model.age == age

    # Tests with falsy values
    model = AtLeastOneWithRestrictions(name="", age=age, music=music)
    assert model.age == age and model.music

    model = AtLeastOneWithRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    model = AtLeastOneWithRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    with LogMixin.context():
        model = AtLeastOneWithRestrictions(name="", age=None, music=music)
        assert LogMixin.logs

    model = AtLeastOneWithRestrictions(name=name, age=None, music=[])
    assert model.name

    model = AtLeastOneWithRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with LogMixin.context():
        AtLeastOneNoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneNoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneNoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneNoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_at_least_one_of_with_two_restrictions(name: str, age: int, music: list[int]):
    """Test when at least two fields are not empty with a field restriction.
    Uses both None and falsy values."""

    # Tests with None
    model = AtLeastOneWithTwoRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=None, age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    model = AtLeastOneWithTwoRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=None, age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=None, age=age, music=None)
        assert LogMixin.logs

    # Tests with falsy values
    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name="", age=age, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=music)
        assert LogMixin.logs

    model = AtLeastOneWithTwoRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name="", age=None, music=music)
        assert LogMixin.logs

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        model = AtLeastOneWithTwoRestrictions(name="", age=age, music=[])
        assert LogMixin.logs

    # Test when no fields are provided
    with LogMixin.context():
        AtLeastOneWithTwoRestrictions(name=None, age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneWithTwoRestrictions(name="", age=None, music=None)
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneWithTwoRestrictions(name=None, age=None, music=[])
        assert LogMixin.logs

    with LogMixin.context():
        AtLeastOneWithTwoRestrictions(name="", age=None, music=[])
        assert LogMixin.logs
