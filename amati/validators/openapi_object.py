"""
Validates the OpenAPI Object - §4.8.1:

"""

from typing import Annotated

from pydantic import Field, AfterValidator

from amati.validators.generic import GenericObject
from amati.validators.info_object import InfoObject

OPENAPI_VERSIONS = ['1.0', '1.1', '1.2', '2.0', '3.0', '3.0.1', '3.0.2', '3.0.3', '3.1', '3.1.1']



OpenAPI = Annotated[
    str,
    Field(strict=True), 
    AfterValidator(lambda v: v in OPENAPI_VERSIONS)
    ]


class OpenAPIObject(GenericObject):
    openapi: OpenAPI
    info: InfoObject
