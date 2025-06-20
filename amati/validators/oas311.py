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
    model_validator,
)

from amati import AmatiValueError, Reference
from amati import model_validators as mv
from amati.fields import (
    SPDXURL,
    URI,
    HTTPStatusCode,
    SPDXIdentifier,
)
from amati.fields.commonmark import CommonMark
from amati.fields.json import JSON
from amati.fields.oas import OpenAPI
from amati.fields.spdx_licences import VALID_LICENCES
from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject, allow_extra_fields
from amati.validators.oas304 import (
    CallbackObject,
    ContactObject,
    EncodingObject,
    ExampleObject,
    ExternalDocumentationObject,
    HeaderObject,
    LinkObject,
    PathItemObject,
    PathsObject,
    RequestBodyObject,
    ResponseObject,
)
from amati.validators.oas304 import SecuritySchemeObject as OAS30SecuritySchemeObject
from amati.validators.oas304 import (
    ServerObject,
    TagObject,
    XMLObject,
)

TITLE = "OpenAPI Specification v3.1.1"

# Convenience naming to ensure that it's clear what's happening.
# https://spec.openapis.org/oas/v3.1.1.html#specification-extensions
specification_extensions = allow_extra_fields


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

    _not_url_and_identifier = mv.only_one_of(["url", "identifier"])

    @model_validator(mode="after")
    def check_uri_associated_with_identifier(self: Self) -> Self:
        """
        Validate that the URL matches the provided licence identifier.

        This validator checks if the URL is listed among the known URLs for the
        specified licence identifier.

        Returns:
            The validated licence object
        """
        # URI only - should warn if not SPDX
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

        # Both Identifier and URI, technically invalid, but should check if
        # consistent
        if (
            self.url
            and self.identifier
            and str(self.url) not in VALID_LICENCES[self.identifier]
        ):
            LogMixin.log(
                Log(
                    message=f"{self.url} is not associated with the identifier {self.identifier}",  # pylint: disable=line-too-long
                    type=Warning,
                    reference=self._reference,
                )
            )

        return self


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
class DiscriminatorObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.8.25
    """

    # FIXME: Need post processing to determine whether the property actually exists
    # FIXME: The component and schema objects need to check that this is being used
    # properly.
    propertyName: str
    mapping: Optional[dict[str, str | URI]] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#discriminator-object",
        section="Discriminator Object",
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
class OperationObject(GenericObject):
    """Validates the OpenAPI Specification operation object - §4.8.10"""

    tags: Optional[list[str]] = None
    summary: Optional[str] = None
    description: Optional[str | CommonMark] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    operationId: Optional[str] = None
    parameters: Optional[list["ParameterObject | ReferenceObject"]] = None
    requestBody: Optional["RequestBodyObject | ReferenceObject"] = None
    responses: Optional["ResponsesObject"] = None
    callbacks: Optional[dict[str, "CallbackObject | ReferenceObject"]] = None
    deprecated: Optional[bool] = False
    security: Optional[list["SecurityRequirementObject"]] = None
    servers: Optional[list[ServerObject]] = None

    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#operation-object",
        section="Operation Object",
    )


PARAMETER_STYLES: set[str] = {
    "matrix",
    "label",
    "simple",
    "form",
    "spaceDelimited",
    "pipeDelimited",
    "deepObject",
}


class ParameterObject(GenericObject):
    """Validates the OpenAPI Specification parameter object - §4.8.11"""

    name: str
    in_: str = Field(alias="in")
    description: Optional[str | CommonMark] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = None
    schema_: Optional["SchemaObject"] = Field(alias="schema")
    example: Optional[Any] = None
    examples: Optional[dict[str, "ExampleObject | ReferenceObject"]] = None
    content: Optional[dict[str, "MediaTypeObject"]] = None

    _in_valid = mv.if_then(
        conditions={"in_": mv.UNKNOWN},
        consequences={"in_": ["query", "header", "path", "cookie"]},
    )
    _path_location_is_required = mv.if_then(
        conditions={"in_": "path"}, consequences={"required": True}
    )
    _empty_value_only_with_query = mv.if_then(
        conditions={"allowEmptyValue": mv.UNKNOWN},
        consequences={"in_": PARAMETER_STYLES ^ {"query"}},
    )
    _style_is_valid = mv.if_then(
        conditions={"style": mv.UNKNOWN}, consequences={"style": list(PARAMETER_STYLES)}
    )
    _reserved_only_with_query = mv.if_then(
        conditions={"allowReserved": mv.UNKNOWN},
        consequences={"in_": PARAMETER_STYLES ^ {"query"}},
    )
    _disallowed_if_schema = mv.if_then(
        conditions={"schema_": mv.UNKNOWN}, consequences={"content": None}
    )
    _disallowed_if_content = mv.if_then(
        conditions={"content": mv.UNKNOWN},
        consequences={
            "content": None,
            "style": None,
            "explode": None,
            "allowReserved": None,
            "schema_": None,
        },
    )


@specification_extensions("x-")
class MediaTypeObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.14
    """

    schema_: Optional["SchemaObject"] = Field(alias="schema", default=None)
    # FIXME: Define example
    example: Optional[Any] = None
    examples: Optional[dict[str, ExampleObject | ReferenceObject]] = None
    encoding: Optional["EncodingObject"] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#media-type-object",
        section="Tag Object",
    )


type _ResponsesObjectReturnType = dict[str, "ReferenceObject | ResponseObject"]


@specification_extensions("x-")
class ResponsesObject(GenericObject):
    """
    Validates the OpenAPI Specification responses object - §4.8.16
    """

    model_config = ConfigDict(
        extra="allow",
    )

    default: Optional["ResponseObject | ReferenceObject"] = None
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
    discriminator: Optional[DiscriminatorObject] = None  # Polymorphism support
    readOnly: Optional[bool] = None  # Declares property as read-only for requests
    writeOnly: Optional[bool] = None  # Declares property as write-only for responses
    xml: Optional[XMLObject] = None  # XML metadata
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


class SecuritySchemeObject(OAS30SecuritySchemeObject):
    """
    Validates the OpenAPI Security Scheme object - §4.8.27
    """

    _SECURITY_SCHEME_TYPES: ClassVar[set[str]] = {
        "apiKey",
        "http",
        "oauth2",
        "openIdConnect",
        "mutualTLS",
    }


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
class ComponentsObject(GenericObject):
    """
    Validates the OpenAPI Specification components object - §4.8.7
    """

    schemas: Optional[dict[str, SchemaObject | ReferenceObject]] = None
    responses: Optional[dict[str, ResponseObject | ReferenceObject]] = None
    paremeters: Optional[dict[str, ParameterObject | ReferenceObject]] = None
    examples: Optional[dict[str, ExampleObject | ReferenceObject]] = None
    requestBodies: Optional[dict[str, RequestBodyObject | ReferenceObject]] = None
    headers: Optional[dict[str, HeaderObject | ReferenceObject]] = None
    securitySchemes: Optional[dict[str, SecuritySchemeObject | ReferenceObject]] = None
    links: Optional[dict[str, LinkObject | ReferenceObject]] = None
    callbacks: Optional[dict[str, CallbackObject | ReferenceObject]] = None
    pathItems: Optional[dict[str, PathItemObject]] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.1.1.html#components-object",
        section="Components Object",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(
        cls, data: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """
        Validates the components object.

        Args:
            data: The data to validate.

        Returns:
            The validated components object.
        """

        pattern: str = r"^[a-zA-Z0-9\.\-_]+$"

        # Validate each field in the components object
        for field_name, value in data.items():
            if field_name.startswith("x-"):
                continue

            if not isinstance(value, dict):  # type: ignore
                raise ValueError(
                    f"Invalid type for '{field_name}': expected dict, got {type(value)}"
                )

            for key in value.keys():
                if not re.match(pattern, key):
                    raise ValueError(
                        f"Invalid key '{key}' in '{field_name}': must match pattern {pattern}"  # pylint: disable=line-too-long
                    )

        return data


@specification_extensions("x-")
class OpenAPIObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.1
    """

    openapi: OpenAPI
    info: InfoObject
    jsonSchemaDialect: Optional[URI] = None
    servers: Optional[list[ServerObject]] = Field(default=[ServerObject(url=URI("/"))])
    paths: Optional[PathsObject] = None
    webhooks: Optional[dict[str, PathItemObject]] = None
    components: Optional[ComponentsObject] = None
    security: Optional[list[SecurityRequirementObject]] = None
    tags: Optional[list[TagObject]] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.1.1.html#openapi-object",
        section="OpenAPI Object",
    )
