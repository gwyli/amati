"""
Tests amati/validators/openapi_object.py
"""

import json
import pytest
import yaml

from hypothesis import given, strategies as st
from pydantic import ValidationError

from amati.validators.generic import GenericObject
from amati.validators.openapi_object import OpenAPIObject, OpenAPI, OPENAPI_VERSIONS


class Model(GenericObject):
    value: OpenAPI


def test_valid_openapi_object():
    with open('tests/data/good_spec.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    model = OpenAPIObject(**data)
    assert json.loads(model.model_dump_json(exclude_unset=True)) == data


def test_invalid_openapi_object():
    with open('tests/data/bad_spec.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    with pytest.raises(ValidationError):
        OpenAPIObject(**data)


@given(st.text().filter(lambda x: x not in OPENAPI_VERSIONS))
def test_invalid_openapi_version(value: str):
    with pytest.raises(ValidationError):
        Model(value=value)


@given(st.sampled_from(OPENAPI_VERSIONS))
def test_valid_openapi_version(value: str):
    model = Model(value=value)
    assert model.value == value
