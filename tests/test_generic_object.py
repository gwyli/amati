"""
Tests amati/validators/generic.py
"""

from typing import Any

from hypothesis import given, strategies as st

from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class Model(GenericObject):
    value: Any

@given(st.dictionaries(keys=st.text(), values=st.text()).filter(lambda x: x != {}), st.data())
def test_invalid_generic_object(data: dict[str, str], data_strategy: st.DataObject):

    if 'value' not in data.keys():
        data['value'] = data_strategy.draw(st.text())

    with LogMixin.context():
        Model(**data)
        assert LogMixin.logs


@given(st.dictionaries(keys=st.just('value'), values=st.text()).filter(lambda x: x != {}))
def test_valid_generic_object(data: dict[str, str]):
    Model(**data)
