"""
Tests amati/validators/oas311.py
"""

import json

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati.validators.oas311 import ContactObject, OpenAPIObject


@given(st.text(), urls(), st.emails())
@settings(deadline=1000)
def test_contact_object(name: str, url: str, email: str):
    ContactObject(name=name, url=url, email=email)  # type: ignore


def test_valid_openapi_object():
    with open("tests/data/good_spec.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    model = OpenAPIObject(**data)
    assert json.loads(model.model_dump_json(exclude_unset=True)) == data


def test_invalid_openapi_object():
    with open("tests/data/bad_spec.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with pytest.raises(ValidationError):
        OpenAPIObject(**data)
