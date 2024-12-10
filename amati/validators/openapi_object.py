"""
Validates the OpenAPI Object - §4.8.1:

"""

from typing import Annotated

from pydantic import AfterValidator, Field

from amati.logging import Log, LogMixin
from amati.validators import title
from amati.validators.generic import GenericObject
from amati.validators.info_object import InfoObject
from amati.validators.reference_object import Reference, ReferenceModel

reference: Reference = ReferenceModel(
    title=title,
    url='https://spec.openapis.org/oas/latest.html#openapi-object',
    section='OpenAPI Object'
)

OPENAPI_VERSIONS = ['1.0', '1.1', '1.2', '2.0', '3.0', '3.0.1', '3.0.2', '3.0.3', '3.1', '3.1.1']


def _validate_after_openapi(value: str) -> str:
    if value not in OPENAPI_VERSIONS:
        LogMixin.log(Log(f"{value} is not a valid OpenAPI version.", ValueError))
    return value

OpenAPI = Annotated[
    str,
    Field(strict=True),
    AfterValidator(_validate_after_openapi)
    ]


class OpenAPIObject(GenericObject):
    openapi: OpenAPI
    info: InfoObject
    _reference: Reference = reference # type: ignore
