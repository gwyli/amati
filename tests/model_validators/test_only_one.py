from typing import ClassVar, Optional
from sys import float_info
from pydantic import BaseModel, ValidationError
from hypothesis import given, strategies as st
import pytest
from amati import model_validators as mv, Reference

from tests.helpers import text_excluding_empty_string

MIN = int(float_info.min)


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


# Using a min_value forces integers to be not-None
@given(
    text_excluding_empty_string(),
    st.integers(min_value=MIN),
    st.lists(st.integers(min_value=MIN), min_size=1),
)
def test_only_one_of_no_restrictions(name: str, age: int, music: list[int]):
    """Test when at least one field is not empty. Uses both None and falsy values."""

    # Tests with None
    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name=name, age=age, music=music)

    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name=None, age=age, music=music)

    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name=name, age=None, music=music)

    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name=name, age=age, music=None)

    model = OnlyOneNoRestrictions(name=None, age=None, music=music)
    assert model.music

    model = OnlyOneNoRestrictions(name=name, age=None, music=None)
    assert model.name

    model = OnlyOneNoRestrictions(name=None, age=age, music=None)
    assert model.age == age

    # Tests with falsy values
    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name="", age=age, music=music)

    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name=name, age=None, music=music)

    with pytest.raises(ValidationError):
        model = OnlyOneNoRestrictions(name=name, age=age, music=[])

    model = OnlyOneNoRestrictions(name="", age=None, music=music)
    assert model.music

    model = OnlyOneNoRestrictions(name=name, age=None, music=[])
    assert model.name

    model = OnlyOneNoRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name="", age=None, music=[])


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
    with pytest.raises(ValidationError):
        model = OnlyOneWithRestrictions(name=name, age=age, music=music)

    model = OnlyOneWithRestrictions(name=None, age=age, music=music)
    assert model.age == age and model.music

    model = OnlyOneWithRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    with pytest.raises(ValidationError):
        model = OnlyOneWithRestrictions(name=name, age=age, music=None)

    with pytest.raises(ValidationError):
        model = OnlyOneWithRestrictions(name=None, age=None, music=music)

    model = OnlyOneWithRestrictions(name=name, age=None, music=None)
    assert model.name

    model = OnlyOneWithRestrictions(name=None, age=age, music=None)
    assert model.age == age

    # Tests with falsy values
    model = OnlyOneWithRestrictions(name="", age=age, music=music)
    assert model.age == age and model.music

    model = OnlyOneWithRestrictions(name=name, age=None, music=music)
    assert model.name and model.music

    with pytest.raises(ValidationError):
        model = OnlyOneWithRestrictions(name=name, age=age, music=[])

    with pytest.raises(ValidationError):
        model = OnlyOneWithRestrictions(name="", age=None, music=music)

    model = OnlyOneWithRestrictions(name=name, age=None, music=[])
    assert model.name

    model = OnlyOneWithRestrictions(name="", age=age, music=[])
    assert model.age == age

    # Test when no fields are provided
    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name=None, age=None, music=None)

    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name="", age=None, music=None)

    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name=None, age=None, music=[])

    with pytest.raises(ValidationError):
        OnlyOneNoRestrictions(name="", age=None, music=[])
