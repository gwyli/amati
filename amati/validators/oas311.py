"""
Validates the OpenAPI Specification version 3.1.1

Note that per https://spec.openapis.org/oas/v3.1.1.html#relative-references-in-api-description-uris  # pylint: disable=line-too-long

> URIs used as references within an OpenAPI Description, or to external documentation
> or other supplementary information such as a license, are resolved as identifiers,
> and described by this specification as URIs.

> Note that some URI fields are named url for historical reasons, but the descriptive
> text for those fields uses the correct “URI” terminology.

"""

import re
from typing import Any, ClassVar, Optional
from typing_extensions import Self

from jsonschema.exceptions import ValidationError as JSONVSchemeValidationError
from jsonschema.protocols import Validator as JSONSchemaValidator
from jsonschema.validators import validator_for  # type: ignore
from pydantic import (
    ConfigDict,
    Field,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue

from amati import AmatiValueError, Reference
from amati.fields import (
    SPDXURL,
    URI,
    Email,
    HTTPAuthenticationScheme,
    HTTPStatusCode,
    MediaType,
    SPDXIdentifier,
    URIType,
    URIWithVariables,
)
from amati.fields.commonmark import CommonMark
from amati.fields.json import JSON
from amati.fields.oas import OpenAPI, RuntimeExpression
from amati.fields.spdx_licences import VALID_LICENCES
from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject, allow_extra_fields

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
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#contact-object",
        section="Contact Object",
    )


@specification_extensions("x-")
class LicenceObject(GenericObject):
    """
    A model representing the OpenAPI Specification licence object §4.8.4

    OAS uses the SPDX licence list.

    # SPECFIX: The URI is mutually exclusive of the identifier. I don't see
    the purpose of this; if the identifier is a SPDX Identifier where's the
    harm in also including the URI
    """

    name: str = Field(min_length=1)
    # What difference does Optional make here?
    identifier: Optional[SPDXIdentifier] = None
    url: Optional[URI] = None
    _reference: ClassVar[Reference] = Reference(
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

        # There are 4 cases
        # 1. No URL or identifier - invalid
        # 2. Identifier only - covered in type checking
        # 3. URI only - should warn if not SPDX
        # 4. Both Identifier and URI, technically invalid, but should check if
        # consistent

        # Case 1
        if not self.url and not self.identifier:
            LogMixin.log(
                Log(
                    message="A Licence object requires a URL or an Identifier.",  # pylint: disable=line-too-long
                    type=ValueError,
                    reference=self._reference,
                )
            )

            return self

        # Case 3
        if self.url:
            try:
                SPDXURL(self.url)
            except AmatiValueError:
                LogMixin.log(
                    Log(
                        message=f"{self.url} is not a valid SPDX URL",
                        type=Warning,
                        reference=self._reference,
                    )
                )

        # Case 4

        if self.url and self.identifier:
            LogMixin.log(
                Log(
                    message="The Identifier and URL are mutually exclusive",
                    type=Warning,
                    reference=self._reference,
                )
            )

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
    _reference: ClassVar[Reference] = Reference(
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
    _reference: ClassVar[Reference] = Reference(
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
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#server-object",
        section="Server Object",
    )

class PathItemObject(GenericObject):
    """
    Placeholder whilst other objects are defined.
    """
    pass

@specification_extensions("x-")
class ExternalDocumentationObject(GenericObject):
    """
    Validates the OpenAPI Specification external documentation object - §4.8.22
    """

    description: Optional[str | CommonMark] = None
    url: URI
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#external-documentation-object",
        section="External Documentation Object",
    )


@specification_extensions("x-")
class RequestBodyObject(GenericObject):
    """
    Validates the OpenAPI Specification request body object - §4.8.13
    """

    description: Optional[CommonMark | str] = None
    content: dict[str, "MediaTypeObject"]
    required: Optional[bool] = False
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#request-body-object",
        section="Request Body Object",
    )


@specification_extensions("x-")
class MediaTypeObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.14
    """

    schema_: "Optional[SchemaObject]" = Field(alias="schema", default=None)
    # FIXME: Define example
    example: Optional[Any] = None
    examples: "Optional[dict[str, ExampleObject | ReferenceObject]]" = None
    encoding: "Optional[EncodingObject]" = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#media-type-object",
        section="Tag Object",
    )


@specification_extensions("x-")
class EncodingObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.15
    """

    contentType: Optional[str] = None
    headers: "Optional[dict[str, HeaderObject | ReferenceObject]]" = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#encoding object-object",
        section="Encoding Object",
    )

    @field_validator("contentType", mode="after")
    @classmethod
    def check_content_type(cls, value: str) -> str:
        """
        contentType is a comma-separated list of media types.
        Check that they are all valid

        raises: ValueError
        """

        for media_type in value.split(","):
            MediaType(media_type.strip())

        return value


type _ResponsesObjectReturnType = "dict[str, ReferenceObject | ResponseObject]"


@specification_extensions("x-")
class ResponsesObject(GenericObject):
    """
    Validates the OpenAPI Specification responses object - §4.8.16
    """

    model_config = ConfigDict(
        extra="allow",
    )

    default: "Optional[ResponseObject | ReferenceObject]" = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#responses-object",
        section="Responses Object",
    )

    @classmethod
    def _choose_model(
        cls, value: Any, field_name: str
    ) -> "ReferenceObject | ResponseObject":
        """
        Choose the model to use for validation based on the type of value.

        Args:
            value: The value to validate.

        Returns:
            The model class to use for validation.
        """

        message = f"{field_name} must be a ResponseObject or ReferenceObject, got {type(value)}"  # pylint: disable=line-too-long

        try:
            return ResponseObject.model_validate(value)
        except ValidationError:
            try:
                return ReferenceObject.model_validate(value)
            except ValidationError as e:
                raise ValueError(message, ResponsesObject._reference) from e

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, data: dict[str, Any]) -> _ResponsesObjectReturnType:
        """
        Validates the responses object.
        """

        validated_data: _ResponsesObjectReturnType = {}

        for field_name, value in data.items():

            # If the value is a specification extension, allow it
            if field_name.startswith("x-"):
                validated_data[field_name] = value
                continue

            # If the value is the fixed field, "default", allow it
            if field_name == "default":
                if isinstance(value, dict):
                    validated_data[field_name] = ResponsesObject._choose_model(
                        value, field_name
                    )
                continue

            # Otherwise, if the field appears like a valid HTTP status code or a range
            if re.match(r"^[1-5]([0-9]{2}|XX)+$", str(field_name)):

                # Double check and raise a value error if not
                HTTPStatusCode(field_name)

                # and validate as a ResponseObject or ReferenceObject
                validated_data[field_name] = ResponsesObject._choose_model(
                    value, field_name
                )

                continue

            # If the field is not a valid HTTP status code or "default"
            raise ValueError(f"Invalid type for numeric field '{field_name}'")

        return validated_data


@specification_extensions("x-")
class ResponseObject(GenericObject):
    """
    Validates the OpenAPI Specification response object - §4.8.17
    """

    description: str | CommonMark
    headers: "Optional[dict[str, HeaderObject | ReferenceObject]]" = None
    content: Optional[dict[str, MediaTypeObject]] = None
    links: "Optional[dict[str, LinkObject | ReferenceObject]]" = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#response-object",
        section="Response Object",
    )

@specification_extensions("x-")
class CallbackObject(GenericObject):
    """
    Validates the OpenAPI Specification callback object - §4.8.18
    """

    model_config = ConfigDict(extra="allow")

    # The keys are runtime expressions that resolve to a URL
    # The values are Response Objects or Reference Objects
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#callback-object",
        section="Callback Object",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, data: dict[str, Any]) -> dict[str, PathItemObject]:
        """
        Validates the callback object.
        """

        validated_data: dict[str, PathItemObject] = {}

        # Everything after a { but before a } should be runtime expression
        pattern: str = r"\{([^}]+)\}"

        for field_name, value in data.items():

            # If the value is a specification extension, allow it
            if field_name.startswith("x-"):
                validated_data[field_name] = PathItemObject.model_validate(value)
                continue

            # Either the field name is a runtime expression, so test this:
            try:
                RuntimeExpression(field_name)
                validated_data[field_name] = PathItemObject.model_validate(value)
                continue
            except AmatiValueError:
                pass

            # Or, the field name is a runtime expression embedded in a string
            # value per https://spec.openapis.org/oas/latest.html#examples-0
            matches = re.findall(pattern, field_name)

            for match in matches:
                try:
                    RuntimeExpression(match)
                except AmatiValueError as e:
                    raise AmatiValueError(
                        f"Invalid runtime expression '{match}' in field '{field_name}'",
                        CallbackObject._reference,
                    ) from e

            if matches:
                validated_data[field_name] = PathItemObject.model_validate(value)
            else:
                # If the field does not contain a valid runtime expression
                raise ValueError(f"Invalid type for numeric field '{field_name}'")

        return validated_data


@specification_extensions("x-")
class TagObject(GenericObject):
    """
    Validates the OpenAPI Specification tag object - §4.8.22
    """

    name: str
    description: Optional[str | CommonMark] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#tag-object",
        section="Tag Object",
    )


class ReferenceObject(GenericObject):
    """
    Validates the OpenAPI Specification reference object - §4.8.23

    Note, "URIs" can be prefixed with a hash; this is because if the
    representation of the referenced document is JSON or YAML, then
    the fragment identifier SHOULD be interpreted as a JSON-Pointer
    as per RFC6901.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ref: URI = Field(alias="$ref")
    summary: Optional[str]
    description: Optional[CommonMark]
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#reference-object",
        section="Reference Object",
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
    _reference: ClassVar[Reference] = Reference(
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
    _reference: ClassVar[Reference] = Reference(
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
class HeaderObject(GenericObject):
    """
    Validates the OpenAPI Specification link object - §4.8.20
    """

    # Common schema/content fields
    description: Optional[str | CommonMark] = None
    required: Optional[bool] = Field(default=False)
    deprecated: Optional[bool] = Field(default=False)

    # Schema fields
    style: Optional[str] = Field(default="simple")
    explode: Optional[bool] = Field(default=False)
    schema_: "Optional[SchemaObject | ReferenceObject]" = Field(
        alias="schema", default=None
    )
    example: Optional[Any] = None
    examples: Optional[dict[str, ExampleObject | ReferenceObject]] = None

    # Content fields
    content: Optional[dict[str, MediaTypeObject]] = None

    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#link-object",
        section="Link Object",
    )

    @model_validator(mode="after")
    def _validate_afer(self: Self) -> Self:
        """
        Validates that a content and schema header are not
        both provided in a single header object.
        """

        if self.schema_ is not None and self.content is not None:
            LogMixin.log(
                Log(
                    message="Only one of content and schema can be provided",
                    type=ValueError,
                    reference=self._reference,
                )
            )

        return self


class SchemaObject(GenericObject):
    """
    Schema Object as per OAS 3.1.1 specification (section 4.8.24)

    This model defines only the OpenAPI-specific fields explicitly.
    Standard JSON Schema fields are allowed via the 'extra' config
    and validated through jsonschema.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",  # Allow all standard JSON Schema fields
    )

    # OpenAPI-specific fields not in standard JSON Schema
    nullable: Optional[bool] = None  # OAS 3.0 style nullable flag
    discriminator: Optional["DiscriminatorObject"] = None  # Polymorphism support
    readOnly: Optional[bool] = None  # Declares property as read-only for requests
    writeOnly: Optional[bool] = None  # Declares property as write-only for responses
    xml: Optional["XMLObject"] = None  # XML metadata
    externalDocs: Optional[ExternalDocumentationObject] = None  # External documentation
    example: Optional[Any] = None  # Example of schema
    examples: Optional[list[Any]] = None  # Examples of schema (OAS 3.1)
    deprecated: Optional[bool] = None  # Specifies schema is deprecated

    # JSON Schema fields that need special handling in OAS context
    ref: Optional[str] = Field(
        default=None, alias="$ref"
    )  # Reference to another schema

    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#schema-object",
        section="Link Object",
    )

    @model_validator(mode="after")
    def validate_schema(self):
        """
        Use jsonschema to validate the model as a valid JSON Schema
        """
        schema_dict = self.model_dump(exclude_none=True, by_alias=True)

        # Handle OAS 3.1 specific validations

        # 1. Convert nullable to type array with null if needed
        if schema_dict.get("nullable") is True and "type" in schema_dict:
            type_val = schema_dict["type"]
            if isinstance(type_val, str) and type_val != "null":
                schema_dict["type"] = [type_val, "null"]
            elif isinstance(type_val, list) and "null" not in type_val:
                schema_dict["type"] = type_val + ["null"]

        # 2. Validate the schema structure using jsonschema's meta-schema
        # Get the right validator based on the declared $schema or default
        # to Draft 2020-12
        schema_version = schema_dict.get(
            "$schema", "https://json-schema.org/draft/2020-12/schema"
        )
        try:
            validator_cls: JSONSchemaValidator = validator_for(  # type: ignore
                {"$schema": schema_version}
            )
            meta_schema: JSON = validator_cls.META_SCHEMA  # type: ignore

            # This will validate the structure conforms to JSON Schema
            validator_cls(meta_schema).validate(schema_dict)  # type: ignore
        except JSONVSchemeValidationError as e:
            LogMixin.log(
                Log(
                    message=f"Invalid JSON Schema: {e.message}",
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
    _reference: ClassVar[Reference] = Reference(
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
    _reference: ClassVar[Reference] = Reference(
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
    openIdConnectUrl: Optional[URI] = None

    _reference: ClassVar[Reference] = Reference(
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
class DiscriminatorObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.8.25
    """

    # FIXME: Need post processing to determine whether the property actually exists
    # FIXME: The component and schema objects need to check that this is being used
    # properly.
    mapping: Optional[dict[str, str]] = None
    propertyName: str
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#discriminator-object",
        section="Security Scheme Object",
    )


@specification_extensions("x-")
class XMLObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.8.26
    """

    name: Optional[str] = None
    namespace: Optional[URI] = None
    prefix: Optional[str] = None
    attribute: Optional[bool] = Field(default=False)
    wrapped: Optional[bool] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#xml-object",
        section="Security Scheme Object",
    )

    @field_validator("namespace", mode="after")
    @classmethod
    def _validate_namespace(cls, value: URI) -> URI:
        if value.type == URIType.RELATIVE:
            message = "XML namespace {value} cannot be a relative URI"
            LogMixin.log(
                Log(message=message, type=ValueError, reference=cls._reference)
            )

        return value


type _Requirement = dict[str, list[str]]


# NB This is implemented as a RootModel as there are no pre-defined field names.
class SecurityRequirementObject(RootModel[list[_Requirement] | _Requirement]):
    """
    Validates the OpenAPI Specification security requirement object - §4.8.30:
    """

    # FIXME: The name must be a valid Security Scheme - need to use post-processing
    # FIXME If the security scheme is of type "oauth2" or "openIdConnect", then the
    # value must be a list
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#security-requirement-object",
        section="Security Requirement Object",
    )


@specification_extensions("x-")
class OpenAPIObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.1
    """

    openapi: OpenAPI
    info: InfoObject
    servers: list[ServerObject] = []
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#openapi-object",
        section="OpenAPI Object",
    )
