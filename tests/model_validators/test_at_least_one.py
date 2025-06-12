from typing import ClassVar, Optional
from sys import float_info
from pydantic import BaseModel, ValidationError
from hypothesis import given, strategies as st
import pytest
from amati import model_validators as mv, Reference

from tests.helpers import text_excluding_empty_string

MIN = int(float_info.min)


class AtLeastOneNoRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _at_least_one = mv.at_least_one()
    _reference: ClassVar[Reference] = Reference(title="test")


class AtLeastOneWithRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _at_least_one = mv.at_least_one(fields=["name", "age"])
    _reference: ClassVar[Reference] = Reference(title="test")


class AtLeastOneWithTwoRestrictions(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    music: Optional[list[int]] = None
    _at_least_one_name = mv.at_least_one(fields=["name"])
    _at_least_one_age = mv.at_least_one(fields=["age"])
    _reference: ClassVar[Reference] = Reference(title="test")


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_at_least_one_no_restrictions(name: str, age: int, music: list[int]):
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
    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name="", age=None, music=[])


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_at_least_one_with_restrictions(
    name: str, age: int, music: list[int]
):
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

    with pytest.raises(ValidationError):
        model = AtLeastOneWithRestrictions(name=None, age=None, music=music)

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

    with pytest.raises(ValidationError):
        model = AtLeastOneWithRestrictions(name="", age=None, music=music)

    model = AtLeastOneWithRestrictions(name=name, age=None, music=[])
    assert model.name

    model = AtLeastOneWithRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name="", age=None, music=[])

# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_at_least_one_with_two_restrictions(
    name: str, age: int, music: list[int]
):
    """Test when at least two fields are not empty with a field restriction.
    Uses both None and falsy values."""

    # Tests with None
    model = AtLeastOneWithTwoRestrictions(name=name, age=age, music=music)
    assert model.name and model.age == age and model.music

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=None, age=age, music=music)

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=music)

    model = AtLeastOneWithTwoRestrictions(name=name, age=age, music=None)
    assert model.name and model.age == age

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=None, age=None, music=music)

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=None)

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=None, age=age, music=None)

    # Tests with falsy values
    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name="", age=age, music=music)

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=music)

    model = AtLeastOneWithTwoRestrictions(name=name, age=age, music=[])
    assert model.name and model.age == age

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name="", age=None, music=music)

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name=name, age=None, music=[])

    with pytest.raises(ValidationError):
        model = AtLeastOneWithTwoRestrictions(name="", age=age, music=[])

    # Test when no fields are provided
    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        AtLeastOneNoRestrictions(name="", age=None, music=[])
