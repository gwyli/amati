"""
Validates the OpenAPI Specification version 3.1.1

Note that per https://spec.openapis.org/oas/v3.1.1.html#relative-references-in-api-description-uris

> URIs used as references within an OpenAPI Description, or to external documentation
> or other supplementary information such as a license, are resolved as identifiers,
> and described by this specification as URIs.

> Note that some URI fields are named url for historical reasons, but the descriptive
> text for those fields uses the correct “URI” terminology.

"""

import re
from typing import Any, ClassVar, Self

from jsonschema.exceptions import ValidationError as JSONVSchemeValidationError
from jsonschema.protocols import Validator as JSONSchemaValidator
from jsonschema.validators import validator_for  # type: ignore
from pydantic import (
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)

from amati import AmatiValueError
from amati import model_validators as mv
from amati._logging import Logger
from amati.fields import (
    SPDXURL,
    URI,
    SPDXIdentifier,
)
from amati.fields.commonmark import CommonMark
from amati.fields.json import JSON
from amati.fields.oas import OpenAPI
from amati.fields.spdx_licences import VALID_LICENCES
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
    ResponsesObject,
    ServerObject,
    TagObject,
    XMLObject,
)
from amati.validators.oas304 import SecuritySchemeObject as OAS30SecuritySchemeObject

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
    identifier: SPDXIdentifier | None = None
    url: URI | None = None
    _reference_uri: ClassVar[str] = URI(
        "https://spec.openapis.org/oas/v3.1.1.html#license-object"
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
                Logger.log(
                    {
                        "msg": f"{self.url} is not a valid SPDX URL",
                        "type": "warning",
                        "loc": (self.__class__.__name__,),
                        "input": self.url,
                        "url": self._reference_uri,
                    }
                )

        # Both Identifier and URI, technically invalid, but should check if
        # consistent
        if (
            self.url
            and self.identifier
            and str(self.url) not in VALID_LICENCES[self.identifier]
        ):
            Logger.log(
                {
                    "msg": f"{self.url} is not associated with the identifier {self.identifier}",  # noqa: E501
                    "type": "warning",
                    "loc": (self.__class__.__name__,),
                    "input": self.model_dump_json(),
                    "url": self._reference_uri,
                }
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

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", populate_by_name=True
    )

    ref: URI = Field(alias="$ref")
    summary: str | None
    description: CommonMark | None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#reference-object"
    )


@specification_extensions("x-")
class InfoObject(GenericObject):
    """
    Validates the OpenAPI Specification info object - §4.8.2:
    """

    title: str
    summary: str | None = None
    description: str | CommonMark | None = None
    termsOfService: str | None = None
    contact: ContactObject | None = None
    license: LicenceObject | None = None
    version: str
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.1.1.html#info-object"
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
    mapping: dict[str, str | URI] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#discriminator-object"
    )


@specification_extensions("x-")
class ServerVariableObject(GenericObject):
    """
    Validates the OpenAPI Specification server variable object - §4.8.6
    """

    enum: list[str] | None = Field(None, min_length=1)
    default: str = Field(min_length=1)
    description: str | CommonMark | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#server-variable-object"
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
            Logger.log(
                {
                    "msg": f"The default value {self.default} is not in the enum list {self.enum}",  # noqa: E501
                    "type": "value_error",
                    "loc": (self.__class__.__name__,),
                    "input": {"default": self.default, "enum": self.enum},
                    "url": self._reference_uri,
                }
            )

        return self


@specification_extensions("x-")
class OperationObject(GenericObject):
    """Validates the OpenAPI Specification operation object - §4.8.10"""

    tags: list[str] | None = None
    summary: str | None = None
    description: str | CommonMark | None = None
    externalDocs: ExternalDocumentationObject | None = None
    operationId: str | None = None
    parameters: list[ParameterObject | ReferenceObject] | None = None
    requestBody: RequestBodyObject | ReferenceObject | None = None
    responses: ResponsesObject | None = None
    callbacks: dict[str, CallbackObject | ReferenceObject] | None = None
    deprecated: bool | None = False
    security: list[SecurityRequirementObject] | None = None
    servers: list[ServerObject] | None = None

    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#operation-object"
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


@specification_extensions("x-")
class ParameterObject(GenericObject):
    """Validates the OpenAPI Specification parameter object - §4.8.11"""

    name: str
    in_: str = Field(alias="in")
    description: str | CommonMark | None = None
    required: bool | None = None
    deprecated: bool | None = None
    allowEmptyValue: bool | None = None
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = None
    schema_: SchemaObject | None = Field(alias="schema")
    example: Any | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None
    content: dict[str, MediaTypeObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#parameter-object"
    )

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

    schema_: SchemaObject | None = Field(alias="schema", default=None)
    # FIXME: Define example
    example: Any | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None
    encoding: EncodingObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#media-type-object"
    )


class SchemaObject(GenericObject):
    """
    Schema Object as per OAS 3.1.1 specification (section 4.8.24)

    This model defines only the OpenAPI-specific fields explicitly.
    Standard JSON Schema fields are allowed via the 'extra' config
    and validated through jsonschema.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        populate_by_name=True,
        extra="allow",  # Allow all standard JSON Schema fields
    )

    # OpenAPI-specific fields not in standard JSON Schema
    nullable: bool | None = None  # OAS 3.0 style nullable flag
    discriminator: DiscriminatorObject | None = None  # Polymorphism support
    readOnly: bool | None = None  # Declares property as read-only for requests
    writeOnly: bool | None = None  # Declares property as write-only for responses
    xml: XMLObject | None = None  # XML metadata
    externalDocs: ExternalDocumentationObject | None = None  # External documentation
    example: Any | None = None  # Example of schema
    examples: list[Any] | None = None  # Examples of schema (OAS 3.1)
    deprecated: bool | None = None  # Specifies schema is deprecated

    # JSON Schema fields that need special handling in OAS context
    ref: str | None = Field(default=None, alias="$ref")  # Reference to another schema

    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#schema-object"
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
                schema_dict["type"] = [*type_val, ["null"]]

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
            Logger.log(
                {
                    "msg": f"Invalid JSON Schema: {e.message}",
                    "type": "value_error",
                    "loc": (self.__class__.__name__,),
                    "input": schema_dict,
                    "url": self._reference_uri,
                }
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
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.1.1.html#security-requirement-object"
    )


@specification_extensions("x-")
class ComponentsObject(GenericObject):
    """
    Validates the OpenAPI Specification components object - §4.8.7
    """

    schemas: dict[str, SchemaObject | ReferenceObject] | None = None
    responses: dict[str, ResponseObject | ReferenceObject] | None = None
    parameters: dict[str, ParameterObject | ReferenceObject] | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None
    requestBodies: dict[str, RequestBodyObject | ReferenceObject] | None = None
    headers: dict[str, HeaderObject | ReferenceObject] | None = None
    securitySchemes: dict[str, SecuritySchemeObject | ReferenceObject] | None = None
    links: dict[str, LinkObject | ReferenceObject] | None = None
    callbacks: dict[str, CallbackObject | ReferenceObject] | None = None
    pathItems: dict[str, PathItemObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.1.1.html#components-object"
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

            for key in value:
                if not re.match(pattern, key):
                    raise ValueError(
                        f"Invalid key '{key}' in '{field_name}': must match pattern {pattern}"  # noqa: E501
                    )

        return data


@specification_extensions("x-")
class OpenAPIObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.1
    """

    openapi: OpenAPI
    info: InfoObject
    jsonSchemaDialect: URI | None = None
    servers: list[ServerObject] | None = Field(default=[ServerObject(url=URI("/"))])
    paths: PathsObject | None = None
    webhooks: dict[str, PathItemObject] | None = None
    components: ComponentsObject | None = None
    security: list[SecurityRequirementObject] | None = None
    tags: list[TagObject] | None = None
    externalDocs: ExternalDocumentationObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.1.1.html#openapi-object"
    )
