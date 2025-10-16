"""
Tests amati.model_validators.all_of
"""

from sys import float_info
from typing import ClassVar

from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from amati import model_validators as mv
from amati._logging import Logger
from tests.helpers import text_excluding_empty_string

MIN = int(float_info.min)


class EmptyObject(BaseModel):
    _at_least_one_of = mv.all_of()
    _reference_uri: ClassVar[str] = "https://example.com"


class AllNoRestrictions(BaseModel):
    name: str | None = None
    age: int | None = None
    music: list[int] | None = None
    _all_of = mv.all_of()
    _reference_uri: ClassVar[str] = "https://example.com"


class AllWithRestrictions(BaseModel):
    name: str | None = None
    age: int | None = None
    music: list[int] | None = None
    _all_of = mv.all_of(fields=["name", "age"])
    _reference_uri: ClassVar[str] = "https://example.com"


def test_empty_object():
    with Logger.context():
        EmptyObject()
        assert not Logger.logs


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_all_of_no_restrictions(name: str, age: int, music: list[int]):  # noqa: PLR0915
    """Test when at least one field is not empty. Uses both None and falsy values."""

    # Tests with None
    model = AllNoRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    with Logger.context():
        AllNoRestrictions(name=None, age=age, music=music)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=name, age=None, music=music)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=name, age=age, music=None)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=None, age=None, music=music)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=name, age=None, music=None)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=None, age=age, music=None)
        assert Logger.logs

    # Tests with falsy values
    with Logger.context():
        AllNoRestrictions(name="", age=age, music=music)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=name, age=None, music=music)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=name, age=age, music=[])
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name="", age=None, music=music)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=name, age=None, music=[])
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name="", age=age, music=[])
        assert Logger.logs

    # Test when no fields are provided
    with Logger.context():
        AllNoRestrictions(name=None, age=None, music=None)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name="", age=None, music=None)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=None, age=None, music=[])
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name="", age=None, music=[])
        assert Logger.logs


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

    with Logger.context():
        AllWithRestrictions(name=None, age=age, music=music)
        assert Logger.logs

    with Logger.context():
        AllWithRestrictions(name=name, age=None, music=music)
        assert Logger.logs

    model = AllWithRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    with Logger.context():
        AllWithRestrictions(name=None, age=None, music=music)
        assert Logger.logs

    with Logger.context():
        AllWithRestrictions(name=name, age=None, music=None)
        assert Logger.logs

    with Logger.context():
        AllWithRestrictions(name=None, age=age, music=None)
        assert Logger.logs

    # Tests with falsy values
    with Logger.context():
        AllWithRestrictions(name="", age=age, music=music)
        assert Logger.logs

    with Logger.context():
        AllWithRestrictions(name=name, age=None, music=music)
        assert Logger.logs

    model = AllWithRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    with Logger.context():
        AllWithRestrictions(name="", age=None, music=music)
        assert Logger.logs

    with Logger.context():
        AllWithRestrictions(name=name, age=None, music=[])
        assert Logger.logs

    with Logger.context():
        AllWithRestrictions(name="", age=age, music=[])
        assert Logger.logs

    # Test when no fields are provided
    with Logger.context():
        AllNoRestrictions(name=None, age=None, music=None)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name="", age=None, music=None)
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name=None, age=None, music=[])
        assert Logger.logs

    with Logger.context():
        AllNoRestrictions(name="", age=None, music=[])
        assert Logger.logs
