"""
Tests amati/validators/generic.py
"""

from typing import Any, ClassVar

from hypothesis import given
from hypothesis import strategies as st

from amati._logging import Logger
from amati.validators.generic import GenericObject, allow_extra_fields


class Model(GenericObject):
    value: Any
    _reference_uri: ClassVar[str] = "https://example.com"


@allow_extra_fields()
class ModelExtra(GenericObject):
    value: Any
    _reference_uri: ClassVar[str] = "https://example.com"


@allow_extra_fields(pattern=r"^x-")
class ModelExtraPattern(GenericObject):
    value: Any
    _reference_uri: ClassVar[str] = "https://example.com"


@given(
    st.dictionaries(keys=st.text(), values=st.text()).filter(lambda x: x != {}),
    st.data(),
)
def test_invalid_generic_object(data: dict[str, str], data_strategy: st.DataObject):
    if "value" not in data:
        data["value"] = data_strategy.draw(st.text())

    with Logger.context():
        Model(**data)
        assert Logger.logs
        assert Logger.logs[0]["msg"] is not None
        assert Logger.logs[0]["type"] == "value_error"


@given(
    st.dictionaries(keys=st.just("value"), values=st.text()).filter(lambda x: x != {})
)
def test_valid_generic_object(data: dict[str, str]):
    Model(**data)


@given(
    st.dictionaries(keys=st.text(), values=st.text()).filter(lambda x: x != {}),
    st.data(),
)
def test_allow_extra_fields(data: dict[str, str], data_strategy: st.DataObject):
    if "value" not in data:
        data["value"] = data_strategy.draw(st.text())

    with Logger.context():
        ModelExtra(**data)
        assert not Logger.logs


@st.composite
def text_matching_pattern(draw: st.DrawFn) -> dict[str, str]:
    """
    Assumes that the pattern will be 'x-'
    """
    key = f"x-{draw(st.text())}"
    value = draw(st.text())

    return {key: value}


@given(text_matching_pattern(), st.data())
def test_allow_extra_fields_with_pattern(
    data: dict[str, str], data_strategy: st.DataObject
):
    if "value" not in data:
        data["value"] = data_strategy.draw(st.text())

    with Logger.context():
        ModelExtraPattern(**data)
        assert not Logger.logs


@given(text_matching_pattern(), st.data())
def test_allow_extra_fields_with_pattern_and_extra(
    data: dict[str, str], data_strategy: st.DataObject
):
    if "value" not in data:
        data["value"] = data_strategy.draw(st.text())

    # Add another field not begining with 'x-'
    data["extra"] = data_strategy.draw(st.text())

    with Logger.context():
        ModelExtraPattern(**data)
        assert Logger.logs
