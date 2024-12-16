"""
Tests amati/fields/openapi_versions.py
"""

from hypothesis import given
from hypothesis import strategies as st

from amati.fields.oas import OPENAPI_VERSIONS, OpenAPI
from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class Model(GenericObject):
    value: OpenAPI


@given(st.text().filter(lambda x: x not in OPENAPI_VERSIONS))
def test_invalid_openapi_version(value: str):
    with LogMixin.context():
        Model(value=value)
        assert LogMixin.logs
        assert LogMixin.logs[0].message is not None
        assert LogMixin.logs[0].type == ValueError
        assert LogMixin.logs[0].reference is not None


@given(st.sampled_from(OPENAPI_VERSIONS))
def test_valid_openapi_version(value: str):
    model = Model(value=value)
    assert model.value == value
