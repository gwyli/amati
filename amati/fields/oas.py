"""
Fields from the OpenAPI Specification (OAS)
"""

from typing import Annotated

from pydantic import AfterValidator, Field

from amati.grammars import oas
from amati.logging import Log, LogMixin
from amati.validators.reference_object import Reference, ReferenceModel

runtime_expression_reference: Reference = ReferenceModel(
    title="OpenAPI Specification v3.1.1",
    section="Runtime Expressions",
    url="https://spec.openapis.org/oas/v3.1.1.html#runtime-expressions",
)


def _validate_after_runtime_expression(value: str) -> str:
    """
    Validate that the runtime expression is a valid runtime expression.

    Args:
        value: The runtime expression to validate
    """
    return oas.Rule("expression").parse_all(value).value


RuntimeExpression = Annotated[
    str,
    AfterValidator(_validate_after_runtime_expression),
]

reference: Reference = ReferenceModel(
    title="OpenAPI Initiative Publications",
    url="https://spec.openapis.org/#openapi-specification",
    section="OpenAPI Specification ",
)

OPENAPI_VERSIONS = ["3.0", "3.0.1", "3.0.2", "3.0.3", "3.0.4", "3.1", "3.1.1"]


def _validate_after_openapi(value: str) -> str:
    if value not in OPENAPI_VERSIONS:
        message = f"{value} is not a valid OpenAPI version."
        LogMixin.log(Log(message=message, type=ValueError, reference=reference))
    return value


OpenAPI = Annotated[str, Field(strict=True), AfterValidator(_validate_after_openapi)]
