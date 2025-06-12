from typing import ClassVar, Optional
from sys import float_info
from pydantic import BaseModel, ValidationError
from hypothesis import given, strategies as st
import pytest
from amati import model_validators as mv, Reference

from tests.helpers import text_excluding_empty_string

MIN = int(float_info.min)


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

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=age, music=music)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=name, age=None, music=music)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=name, age=age, music=None)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=None, music=music)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=name, age=None, music=None)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=age, music=None)

    # Tests with falsy values
    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=age, music=music)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=name, age=None, music=music)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=name, age=age, music=[])

    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=None, music=music)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=name, age=None, music=[])

    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=age, music=[])

    # Test when no fields are provided
    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=None, music=[])


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

    with pytest.raises(ValidationError):
        AllWithRestrictions(name=None, age=age, music=music)

    with pytest.raises(ValidationError):
        AllWithRestrictions(name=name, age=None, music=music)

    model = AllWithRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    with pytest.raises(ValidationError):
        model = AllWithRestrictions(name=None, age=None, music=music)

    with pytest.raises(ValidationError):
        AllWithRestrictions(name=name, age=None, music=None)

    with pytest.raises(ValidationError):
        AllWithRestrictions(name=None, age=age, music=None)

    # Tests with falsy values
    with pytest.raises(ValidationError):
        AllWithRestrictions(name="", age=age, music=music)

    with pytest.raises(ValidationError):
        AllWithRestrictions(name=name, age=None, music=music)

    model = AllWithRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    with pytest.raises(ValidationError):
        model = AllWithRestrictions(name="", age=None, music=music)

    with pytest.raises(ValidationError):
        AllWithRestrictions(name=name, age=None, music=[])

    with pytest.raises(ValidationError):
        AllWithRestrictions(name="", age=age, music=[])

    # Test when no fields are provided
    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        AllNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        AllNoRestrictions(name="", age=None, music=[])
