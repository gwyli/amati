"""
Tests amati/validators/openapi_object.py
"""

from hypothesis import given, strategies as st

from amati.logging import LogMixin
from amati.fields.openapi_versions import OpenAPI, OPENAPI_VERSIONS
from amati.validators.generic import GenericObject


class Model(GenericObject):
    value: OpenAPI


@given(st.text().filter(lambda x: x not in OPENAPI_VERSIONS))
def test_invalid_openapi_version(value: str):
    with LogMixin.context():
        Model(value=value)
        assert LogMixin.logs


@given(st.sampled_from(OPENAPI_VERSIONS))
def test_valid_openapi_version(value: str):
    model = Model(value=value)
    assert model.value == value
