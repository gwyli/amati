"""
Fields from the OpenAPI Specification (OAS)
"""

from typing import ClassVar

from abnf import ParseError

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str
from amati.grammars import oas

OPENAPI_VERSIONS: list[str] = [
    "3.0",
    "3.0.0",
    "3.0.1",
    "3.0.2",
    "3.0.3",
    "3.0.4",
    "3.1",
    "3.1.0",
    "3.1.1",
]


class RuntimeExpression(_Str):
    """
    A class representing a runtime expression as defined in the OpenAPI Specification.
    This class validates the runtime expression format according to the OpenAPI grammar.

    It is validated against the ABNF grammar in the OpenAPI spec.
    """

    _reference: ClassVar[Reference] = Reference(
        title="OpenAPI Specification v3.1.1",
        section="Runtime Expressions",
        url="https://spec.openapis.org/oas/v3.1.1.html#runtime-expressions",
    )

    def __init__(self, value: str):
        """
        Initialize a RunTimeExpression instance.

        Args:
            value: The runtime expression to validate
        """

        try:
            oas.Rule("expression").parse_all(value)
        except ParseError as e:
            raise AmatiValueError(
                f"{value} is not a valid runtime expression",
                reference=self._reference,
            ) from e


class OpenAPI(_Str):
    """
    Represents an OpenAPI version string.s
    """

    _reference: ClassVar[Reference] = Reference(
        title="OpenAPI Initiative Publications",
        url="https://spec.openapis.org/#openapi-specification",
        section="OpenAPI Specification ",
    )

    def __init__(self, value: str):
        """
        Initialize an OpenAPI instance.

        Args:
            value: The OpenAPI version string to validate
        """
        if value not in OPENAPI_VERSIONS:
            raise AmatiValueError(
                f"{value} is not a valid OpenAPI version",
                reference=self._reference,
            )
