# This will change significantly over time, and currently only serves
# as a placeholder to demonstrate that the strategy taken in this project
# theoretically works

from pydantic import ValidationError
from specs.validators.licence_object import LicenceObject
from specs.validators.http_status_codes import HTTPStatusCode
from specs.validators.http_verbs import HTTPVerb
from specs.validators.generic import GenericObject
import yaml
import pytest
import json

class HTTP(GenericObject):
    verb: HTTPVerb
    status: HTTPStatusCode

class Everything(GenericObject):
    licence: LicenceObject
    http: HTTP

def test_everything_works():
    with open('tests/data/good_spec.yaml') as f:
        data = yaml.safe_load(f)
    
    model = Everything(**data)
    assert json.loads(model.model_dump_json()) == data

def test_everything_fails():
    with open('tests/data/bad_spec.yaml') as f:
        data = yaml.safe_load(f)
    
    with pytest.raises(ValidationError):
        Everything(**data)