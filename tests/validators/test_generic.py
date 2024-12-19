"""
Tests amati/validators/generic.py
"""

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from amati.logging import LogMixin
from amati.validators.generic import GenericObject, allow_extra_fields


class Model(GenericObject):
    value: Any


@allow_extra_fields()
class ModelExtra(GenericObject):
    value: Any


@allow_extra_fields(pattern=r"^x-")
class ModelExtraPattern(GenericObject):
    value: Any


@given(
    st.dictionaries(keys=st.text(), values=st.text()).filter(lambda x: x != {}),
    st.data(),
)
def test_invalid_generic_object(data: dict[str, str], data_strategy: st.DataObject):

    if "value" not in data.keys():
        data["value"] = data_strategy.draw(st.text())

    with LogMixin.context():
        Model(**data)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
        assert LogMixin.logs[0].reference is None


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

    if "value" not in data.keys():
        data["value"] = data_strategy.draw(st.text())

    with LogMixin.context():
        ModelExtra(**data)
        assert not LogMixin.logs


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

    if "value" not in data.keys():
        data["value"] = data_strategy.draw(st.text())

    with LogMixin.context():
        ModelExtraPattern(**data)
        assert not LogMixin.logs


@given(text_matching_pattern(), st.data())
def test_allow_extra_fields_with_pattern_and_extra(
    data: dict[str, str], data_strategy: st.DataObject
):
    if "value" not in data.keys():
        data["value"] = data_strategy.draw(st.text())

    # Add another field not begining with 'x-'
    data["extra"] = data_strategy.draw(st.text())

    with LogMixin.context():
        ModelExtraPattern(**data)
        assert LogMixin.logs
