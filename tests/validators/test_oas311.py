"""
Tests amati/validators/oas311.py
"""

import json
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import AnyUrl, ValidationError

from amati import _resolve_forward_references, amati
from amati.fields.json import JSON
from amati.logging import LogMixin
from amati.validators import oas311
from tests.helpers import text_excluding_empty_string


@given(st.text(), st.text(), urls())
def test_example_object(summary: str, description: str, external_value: AnyUrl):
    with LogMixin.context():
        value: JSON = {"value": "value"}
        oas311.ExampleObject(
            summary=summary,
            description=description,
            value=value,
            externalValue=external_value,  # type: ignore
        )
        assert LogMixin.logs[0].type == ValueError


@given(urls(), text_excluding_empty_string())
def test_link_object(operation_ref: AnyUrl, operation_id: str):
    with LogMixin.context():
        oas311.LinkObject(
            operationRef=operation_ref, operationId=operation_id  # type: ignore
        )
        assert LogMixin.logs[0].type == ValueError


@given(st.text(), urls(), st.emails())
@settings(deadline=1000)
def test_contact_object(name: str, url: str, email: str):
    with LogMixin.context():
        oas311.ContactObject(name=name, url=url, email=email)  # type: ignore
        assert not LogMixin.logs


def test_valid_openapi_object():

    _resolve_forward_references.resolve_forward_references(oas311)

    with open("tests/data/good_spec.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with LogMixin.context():
        model = oas311.OpenAPIObject(**data)
        assert not LogMixin.logs

        assert json.loads(model.model_dump_json(exclude_unset=True)) == data


def test_petstore():

    data = amati.file_handler(Path("tests/data/openapi.yaml"))

    with LogMixin.context():
        model = amati.dispatch(data)
        assert not LogMixin.logs

    assert amati.validate(data, model)


def test_invalid_openapi_object():

    _resolve_forward_references.resolve_forward_references(oas311)

    with open("tests/data/bad_spec.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with pytest.raises(ValidationError):
        oas311.OpenAPIObject(**data)
