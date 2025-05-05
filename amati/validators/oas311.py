"""
Validates the OpenAPI Specification version 3.1.1

Note that per https://spec.openapis.org/oas/v3.1.1.html#relative-references-in-api-description-uris  # pylint: disable=line-too-long

> URIs used as references within an OpenAPI Description, or to external documentation
> or other supplementary information such as a license, are resolved as identifiers,
> and described by this specification as URIs.

> Note that some URI fields are named url for historical reasons, but the descriptive
> text for those fields uses the correct “URI” terminology.

"""

from typing import Any, ClassVar, Optional
from typing_extensions import Self

from pydantic import ConfigDict, Field, model_validator
from pydantic.json_schema import JsonSchemaValue

from amati.fields.commonmark import CommonMark
from amati.fields.email import Email
from amati.fields.iso9110 import HTTPAuthenticationScheme
from amati.fields.oas import OpenAPI, RuntimeExpression
from amati.fields.spdx_licences import SPDXURL, VALID_LICENCES, SPDXIdentifier
from amati.fields.uri import URI, RelativeURI, URIWithVariables
from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject, allow_extra_fields
from amati.validators.reference_object import Reference, ReferenceModel

TITLE = "OpenAPI Specification v3.1.1"

# Convenience naming to ensure that it's clear what's happening.
# https://spec.openapis.org/oas/v3.1.1.html#specification-extensions
specification_extensions = allow_extra_fields


@specification_extensions("x-")
class ContactObject(GenericObject):
    """
    Validates the OpenAPI Specification contact object - §4.8.3
    """

    name: Optional[str] = None
    url: Optional[URI] = None
    email: Optional[Email] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#contact-object",
        section="Contact Object",
    )


@specification_extensions("x-")
class LicenceObject(GenericObject):
    """
    A model representing the OpenAPI Specification licence object §4.8.4

    OAS uses the SPDX licence list.
    """

    name: str = Field(min_length=1)
    # What difference does Optional make here?
    identifier: SPDXIdentifier = None
    url: SPDXURL = None
    _reference: ClassVar[Reference] = ReferenceModel(
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


@specification_extensions("x-")
class InfoObject(GenericObject):
    """
    Validates the OpenAPI Specification info object - §4.8.2:
    """

    title: str
    summary: Optional[str] = None
    description: Optional[str | CommonMark] = None
    termsOfService: Optional[str] = None  # pylint: disable=invalid-name
    contact: Optional[ContactObject] = None
    license: Optional[LicenceObject] = None
    version: str
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#info-object",
        section="Info Object",
    )


@specification_extensions("x-")
class ServerVariableObject(GenericObject):
    """
    Validates the OpenAPI Specification server variable object - §4.8.6
    """

    enum: Optional[list[str]] = Field(None, min_length=1)
    default: str = Field(min_length=1)
    description: Optional[str | CommonMark] = None
    _reference: ClassVar[Reference] = ReferenceModel(
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


@specification_extensions("x-")
class ServerObject(GenericObject):
    """
    Validates the OpenAPI Specification server object - §4.8.5
    """

    url: URIWithVariables | URI
    description: Optional[str | CommonMark] = None
    variables: Optional[dict[str, ServerVariableObject]] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#server-object",
        section="Server Object",
    )


@specification_extensions("x-")
class ExternalDocumentationObject(GenericObject):
    """
    Validates the OpenAPI Specification external documentation object - §4.8.22
    """

    description: Optional[str | CommonMark] = None
    url: URI
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#external-documentation-object",
        section="External Documentation Object",
    )


@specification_extensions("x-")
class TagObject(GenericObject):
    """
    Validates the OpenAPI Specification tag object - §4.8.22
    """

    name: str
    description: Optional[str | CommonMark] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#tag-object",
        section="Tag Object",
    )


@specification_extensions("x-")
class ExampleObject(GenericObject):
    """
    Validates the OpenAPI Specification example object - §4.8.19
    """

    summary: Optional[str] = None
    description: Optional[str | CommonMark] = None
    value: Optional[JsonSchemaValue] = None
    externalValue: Optional[URI] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#example-object",
        section="Example Object",
    )

    @model_validator(mode="after")
    def check_values_mutually_exclusive(self: Self) -> Self:
        """
        Validate that only one of value or externalValue is provided.

        Returns:
            The validated example object
        """
        if self.value is not None and self.externalValue is not None:
            LogMixin.log(
                Log(
                    message="Only one of value or externalValue can be provided",
                    type=ValueError,
                    reference=self._reference,
                )
            )

        return self


ExampleObject.model_rebuild()


@specification_extensions("x-")
class LinkObject(GenericObject):
    """
    Validates the OpenAPI Specification link object - §4.8.20
    """

    operationRef: Optional[URI] = None
    operationId: Optional[str] = None
    parameters: Optional[dict[str, RuntimeExpression]] = None
    requestBody: Optional[Any | RuntimeExpression] = None
    description: Optional[str | CommonMark] = None
    server: Optional[ServerObject] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#link-object",
        section="Link Object",
    )

    @model_validator(mode="after")
    def _validate_operation_ref_id_mutually_exclusive(self: Self) -> Self:
        """
        Validate that only one of operationRef or operationId is provided.

        Returns:
            The validated link object
        """
        if self.operationRef is not None and self.operationId is not None:
            LogMixin.log(
                Log(
                    message="Only one of operationRef or operationId can be provided",
                    type=ValueError,
                    reference=self._reference,
                )
            )

        return self


@specification_extensions("x-")
class OAuthFlowObject(GenericObject):
    """
    Validates the OpenAPI OAuth Flow object - §4.8.29
    """

    authorizationUrl: Optional[URI] = None
    tokenUrl: Optional[URI] = None
    refreshUrl: Optional[URI] = None
    scopes: dict[str, str] = {}
    type: Optional[str] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#oauth-flow-object",
        section="OAuth Flow Object",
    )

    @model_validator(mode="after")
    def _validate_after(self: Self) -> Self:
        """
        Validates that the correct type of OAuth2 flow has the correct fields.
        """
        if self.type == "implicit":
            if not self.authorizationUrl:
                message = f"{self.type} requires an authorizationUrl."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )
            if self.tokenUrl:
                message = f"{self.type} must not have a tokenUrl."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )
        if self.type == "authorizationCode":
            if not self.authorizationUrl:
                message = f"{self.type} requires an authorizationUrl."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )
            if not self.tokenUrl:
                message = f"{self.type} requires a tokenUrl."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )

        if self.type in ("clientCredentials", "password"):

            if self.authorizationUrl:
                message = f"{self.type} must not have an authorizationUrl."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )
            if not self.tokenUrl:
                message = f"{self.type} requires a tokenUrl."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )

        return self


@specification_extensions("-x")
class OAuthFlowsObject(GenericObject):
    """
    Validates the OpenAPI OAuth Flows object - §4.8.28

    SPECFIX: Not all of these should be optional as an OAuth2 workflow
    without any credentials will not do anything.
    """

    implicit: Optional[OAuthFlowObject] = None
    password: Optional[OAuthFlowObject] = None
    clientCredentials: Optional[OAuthFlowObject] = None
    authorizationCode: Optional[OAuthFlowObject] = None
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#oauth-flow-object",
        section="OAuth Flows Object",
    )

    @model_validator(mode="before")
    @classmethod
    def _push_down_type(cls, data: Any) -> Any:
        """
        Adds the type of OAuth2 flow, e.g. implicit, password to the child
        OAuthFlowObject so that additional validation can be done on this object.
        """

        for k in data.keys():
            data[k].type = k

        return data


SECURITY_SCHEME_TYPES: set[str] = {
    "apiKey",
    "http",
    "mutualTLS",
    "oauth2",
    "openIdConnect",
}


class SecuritySchemeObject(GenericObject):
    """
    Validates the OpenAPI Security Scheme object - §4.8.27
    """

    # Ensure that passing `in_` to the object works.
    model_config = ConfigDict(populate_by_name=True)

    type: str
    description: Optional[str | CommonMark] = None
    name: Optional[str] = None
    in_: Optional[str] = Field(default=None, alias="in")
    scheme: Optional[HTTPAuthenticationScheme] = None
    bearerFormat: Optional[str] = None
    flows: Optional[OAuthFlowsObject] = None
    openIdConnectUrl: Optional[RelativeURI] = None

    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#security-scheme-object-0",
        section="Security Scheme Object",
    )

    @model_validator(mode="after")
    def _validate_after(self: Self) -> Self:
        """
        Validates the conditional logic of the security scheme
        """

        # Security schemes must be one of the valid schemes
        if self.type not in SECURITY_SCHEME_TYPES:
            message = f"{self.type} is not a valid Security Scheme type."
            LogMixin.log(
                Log(message=message, type=ValueError, reference=self._reference)
            )

        if self.type == "apiKey":
            if self.name is None or self.name == "":
                message = "The name of the header, query or cookie parameter to be used is required if the security type is apiKey"  # pylint: disable=line-too-long
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )
            if self.in_ not in ("query", "header", "cookie"):
                message = f"The location, {self.in_} of the API key is not valid."
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )

        if self.type == "http":
            if self.scheme is None or self.scheme == "":
                message = "The scheme is required if the security type is http"
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )

        if self.type == "oauth2":
            if self.flows is None:
                message = (
                    "The OAuth Flows Object is required if the security type is oauth2"
                )
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )

        if self.type == "openIdConnect":
            if self.openIdConnectUrl is None or self.openIdConnectUrl == "":
                message = "The openIdConnectUrl is required if the security type is openIdConnect"  # pylint: disable=line-too-long
                LogMixin.log(
                    Log(message=message, type=ValueError, reference=self._reference)
                )

        if self.flows and self.type != "oauth2":
            message = "The flows object should only be used with OAuth2"  # pylint: disable=line-too-long
            LogMixin.log(
                Log(message=message, type=ValueError, reference=self._reference)
            )

        return self


@specification_extensions("x-")
class OpenAPIObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.1
    """

    openapi: OpenAPI
    info: InfoObject
    servers: list[ServerObject] = []
    _reference: ClassVar[Reference] = ReferenceModel(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#openapi-object",
        section="OpenAPI Object",
    )
