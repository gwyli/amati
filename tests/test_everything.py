"""
This will change significantly over time, and currently only serves
as a placeholder to demonstrate that the strategy taken in this project
theoretically works
"""

import json
import pytest
import yaml

from pydantic import ValidationError

from amati.validators.generic import GenericObject
from amati.validators.http_status_codes import HTTPStatusCode, HTTPStatusCodeX
from amati.validators.http_verbs import HTTPVerb
from amati.validators.licence_object import LicenceObject


class HTTP(GenericObject):
    verb: HTTPVerb
    status: HTTPStatusCode | HTTPStatusCodeX


class Everything(GenericObject):
    licence: LicenceObject
    http: HTTP
    http: HTTP


def test_everything_works():
    with open('tests/data/good_spec.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    model = Everything(**data)
    assert json.loads(model.model_dump_json()) == data


def test_everything_fails():
    with open('tests/data/bad_spec.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    with pytest.raises(ValidationError):
        Everything(**data)
