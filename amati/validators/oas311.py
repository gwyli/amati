"""
Validates the OpenAPI Specification version 3.1.1

Note that per https://spec.openapis.org/oas/v3.1.1.html#relative-references-in-api-description-uris  # pylint: disable=line-too-long

> URIs used as references within an OpenAPI Description, or to external documentation
> or other supplementary information such as a license, are resolved as identifiers, 
> and described by this specification as URIs. 

> Note that some URI fields are named url for historical reasons, but the descriptive 
> text for those fields uses the correct “URI” terminology.

"""

from typing import Optional
from typing_extensions import Self

from pydantic import Field, model_validator

from amati.fields.commonmark import CommonMark
from amati.fields.email import Email
from amati.fields.openapi_versions import OpenAPI
from amati.fields.spdx_licences import SPDXURL, VALID_LICENCES, SPDXIdentifier
from amati.fields.uri import URI, URIWithVariables
from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject
from amati.validators.reference_object import Reference, ReferenceModel

TITLE = "OpenAPI Specification v3.1.1"


class ContactObject(GenericObject):
    """
    Validates the OpenAPI Specification contact object - §4.8.3
    """

    name: Optional[str] = None
    url: Optional[URI] = None
    email: Optional[Email] = None
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#contact-object",
        section="Contact Object",
    )


class LicenceObject(GenericObject):
    """
    A model representing the OpenAPI Specification licence object §4.8.4

    OAS uses the SPDX licence list.
    """

    name: str = Field(min_length=1)
    # What difference does Optional make here?
    identifier: SPDXIdentifier = None
    url: SPDXURL = None
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#license-object",
        section="License Object",
    )

    @model_validator(mode="after")
    def check_uri_associated_with_identifier(self: Self) -> Self:
        """
        Validate that the URL matches the provided licence identifier.

        This validator checks if the URL is listed among the known URLs for the
        specified licence identifier.

        Returns:
            The validated licence object
        """
        if self.url is None:
            return self

        # Checked in the type AfterValidator, not necessary to raise a warning here.
        # only done to avoid an unnecessary KeyError
        if self.identifier not in VALID_LICENCES:
            return self

        if str(self.url) not in VALID_LICENCES[self.identifier]:
            LogMixin.log(
                Log(
                    message=f"{self.url} is not associated with the identifier {self.identifier}",  # pylint: disable=line-too-long
                    type=Warning,
                    reference=self._reference,
                )
            )

        return self


class InfoObject(GenericObject):
    """
    Validates the OpenAPI Specification info object - §4.8.2:
    """

    title: str
    summary: Optional[str] = None
    description: Optional[CommonMark] = None
    termsOfService: Optional[str] = None  # pylint: disable=invalid-name
    contact: Optional[ContactObject] = None
    license: Optional[LicenceObject] = None
    version: str
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#info-object",
        section="Info Object",
    )


class ServerVariableObject(GenericObject):
    """
    Validates the OpenAPI Specification server variable object - §4.8.6
    """

    enum: Optional[list[str]] = Field(None, min_length=1)
    default: str = Field(min_length=1)
    description: Optional[CommonMark] = None
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#server-variable-object",
        section="Server Variable Object",
    )

    @model_validator(mode="after")
    def check_enum_default(self: Self) -> Self:
        """
        Validate that the default value is in the enum list.

        Returns:
            The validated server variable object
        """
        if self.enum is None:
            return self

        if self.default not in self.enum:
            LogMixin.log(
                Log(
                    message=f"The default value {self.default} is not in the enum list {self.enum}",  # pylint: disable=line-too-long
                    type=ValueError,
                    reference=self._reference,
                )
            )

        return self


class ServerObject(GenericObject):
    """
    Validates the OpenAPI Specification server object - §4.8.5
    """

    url: URIWithVariables | URI
    description: Optional[CommonMark] = None
    variables: Optional[dict[str, ServerVariableObject]] = None
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#server-object",
        section="Server Object",
    )


class ExternalDocumentationObject(GenericObject):
    """
    Validates the OpenAPI Specification external documentation object - §4.8.22
    """

    description: Optional[CommonMark] = None
    url: URI
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#external-documentation-object",
        section="External Documentation Object",
    )


class TagObject(GenericObject):
    """
    Validates the OpenAPI Specification tag object - §4.8.22
    """

    name: str
    description: Optional[CommonMark] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#tag-object",
        section="Tag Object",
    )


class OpenAPIObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.1
    """

    openapi: OpenAPI
    info: InfoObject
    servers: list[ServerObject] = []
    _reference: Reference = ReferenceModel(  # type: ignore
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#openapi-object",
        section="OpenAPI Object",
    )
