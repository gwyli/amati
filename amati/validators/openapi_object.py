"""
Validates the OpenAPI Object - §4.8.1:

"""

from typing import Annotated

from pydantic import Field, AfterValidator

from amati.validators.generic import GenericObject
from amati.validators.info_object import InfoObject

OPENAPI_VERSIONS = ['1.0', '1.1', '1.2', '2.0', '3.0', '3.0.1', '3.0.2', '3.0.3', '3.1', '3.1.1']


def _validate_after_openapi(value: str) -> str:
    if value not in OPENAPI_VERSIONS:
        raise ValueError(f"{value} is not a valid OpenAPI version.")
    return value

OpenAPI = Annotated[
    str,
    Field(strict=True), 
    AfterValidator(_validate_after_openapi)
    ]


class OpenAPIObject(GenericObject):
    openapi: OpenAPI
    info: InfoObject
