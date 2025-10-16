"""
Validates the OpenAPI Specification version 3.1.1

Note that per https://spec.openapis.org/oas/v3.0.4.html#relative-references-in-api-description-uris

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
    ValidationError,
    field_validator,
    model_validator,
)

from amati import AmatiValueError
from amati import model_validators as mv
from amati._logging import Logger
from amati.fields import (
    URI,
    Email,
    HTTPAuthenticationScheme,
    HTTPStatusCode,
    MediaType,
    URIType,
    URIWithVariables,
)
from amati.fields.commonmark import CommonMark
from amati.fields.json import JSON
from amati.fields.oas import OpenAPI, RuntimeExpression
from amati.validators.generic import GenericObject, allow_extra_fields

type JSONPrimitive = str | int | float | bool | None
type JSONArray = list["JSONValue"]
type JSONObject = dict[str, "JSONValue"]
type JSONValue = JSONPrimitive | JSONArray | JSONObject


TITLE = "OpenAPI Specification v3.0.4"

# Convenience naming to ensure that it's clear what's happening.
# https://spec.openapis.org/oas/v3.0.4.html#specification-extensions
specification_extensions = allow_extra_fields


@specification_extensions("x-")
class ContactObject(GenericObject):
    """
    Validates the OpenAPI Specification contact object - §4.8.3
    """

    name: str | None = None
    url: URI | None = None
    email: Email | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.0.4.html#contact-object"
    )


@specification_extensions("x-")
class LicenceObject(GenericObject):
    """
    A model representing the OpenAPI Specification licence object §4.8.4
    """

    name: str = Field(min_length=1)
    url: URI | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#license-object"
    )


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
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#reference-object"
    )


@specification_extensions("x-")
class InfoObject(GenericObject):
    """
    Validates the OpenAPI Specification info object - §4.8.2:
    """

    title: str
    description: str | CommonMark | None = None
    termsOfService: str | None = None
    contact: ContactObject | None = None
    license: LicenceObject | None = None
    version: str
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.0.4.html#info-object"
    )


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
        "https://spec.openapis.org/oas/v3.0.4.html#discriminator-object"
    )


@specification_extensions("x-")
class ExampleObject(GenericObject):
    """
    Validates the OpenAPI Specification example object - §4.8.19
    """

    summary: str | None = None
    description: str | CommonMark | None = None
    value: JSONValue | None = None
    externalValue: URI | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#example-object"
    )

    _not_value_and_external_value = mv.only_one_of(
        ["value", "externalValue"], "warning"
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
        "https://spec.openapis.org/oas/v3.0.4.html#server-variable-object"
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
                    "type": "warning",
                    "loc": (self.__class__.__name__,),
                    "input": {"default": self.default, "enum": self.enum},
                    "url": self._reference_uri,
                }
            )

        return self


@specification_extensions("x-")
class ServerObject(GenericObject):
    """
    Validates the OpenAPI Specification server object - §4.8.5
    """

    url: URIWithVariables | URI
    description: str | CommonMark | None = None
    variables: dict[str, ServerVariableObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#server-object"
    )


@specification_extensions("x-")
class ExternalDocumentationObject(GenericObject):
    """
    Validates the OpenAPI Specification external documentation object - §4.8.22
    """

    description: str | CommonMark | None = None
    url: URI
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#external-documentation-object"
    )


# FIXME: Specification extensions should be "^x-", but the implementation
# doesn't play well with ConfigDict(extra="allow"). This is the only case
# so less important to change as the eventual logic is still correct.
@specification_extensions(".*")
class PathsObject(GenericObject):
    """Validates the OpenAPI Specification paths object - §4.8.8"""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def paths_are_uris(cls, data: Any) -> Any:
        """
        Validates that paths are valid URIs, it's allowed that they
        have variables, e.g. /pets or /pets/{petID}

        Special-case specification extensions, which are also allowed.
        """

        for field in data:
            # Specification extensions
            if field.startswith("x-"):
                continue

            URIWithVariables(field)

        return data


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
    responses: ResponsesObject
    callbacks: dict[str, CallbackObject | ReferenceObject] | None = None
    deprecated: bool | None = False
    security: list[SecurityRequirementObject] | None = None
    servers: list[ServerObject] | None = None

    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#operation-object"
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
    schema_: SchemaObject | ReferenceObject | None = Field(alias="schema")
    example: Any | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None
    content: dict[str, MediaTypeObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#parameter-object"
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
class RequestBodyObject(GenericObject):
    """
    Validates the OpenAPI Specification request body object - §4.8.13
    """

    description: CommonMark | str | None = None
    content: dict[str, MediaTypeObject]
    required: bool | None = False
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#request-body-object"
    )


@specification_extensions("x-")
class MediaTypeObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.14
    """

    schema_: SchemaObject | ReferenceObject | None = Field(alias="schema", default=None)
    # FIXME: Define example
    example: Any | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None
    encoding: EncodingObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#media-type-object"
    )


@specification_extensions("x-")
class EncodingObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.15
    """

    contentType: str | None = None
    headers: dict[str, HeaderObject | ReferenceObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#encoding object-object"
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


type _ResponsesObjectReturnType = dict[str, "ReferenceObject | ResponseObject"]


@specification_extensions(".*")
class ResponsesObject(GenericObject):
    """
    Validates the OpenAPI Specification responses object - §4.8.16
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )

    default: ResponseObject | ReferenceObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#responses-object"
    )

    @classmethod
    def _choose_model(
        cls, value: Any, field_name: str
    ) -> ReferenceObject | ResponseObject:
        """
        Choose the model to use for validation based on the type of value.

        Args:
            value: The value to validate.

        Returns:
            The model class to use for validation.
        """

        message = f"{field_name} must be a ResponseObject or ReferenceObject, got {type(value)}"  # noqa: E501

        try:
            return ResponseObject.model_validate(value)
        except ValidationError:
            try:
                return ReferenceObject.model_validate(value)
            except ValidationError as e:
                raise ValueError(message, ResponsesObject._reference_uri) from e

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
    headers: dict[str, HeaderObject | ReferenceObject] | None = None
    content: dict[str, MediaTypeObject] | None = None
    links: dict[str, LinkObject | ReferenceObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#response-object"
    )


@specification_extensions("x-")
class CallbackObject(GenericObject):
    """
    Validates the OpenAPI Specification callback object - §4.8.18
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    # The keys are runtime expressions that resolve to a URL
    # The values are Response Objects or Reference Objects
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#callback-object"
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
                        CallbackObject._reference_uri,
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
    description: str | CommonMark | None = None
    externalDocs: ExternalDocumentationObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#tag-object"
    )


@specification_extensions("x-")
class LinkObject(GenericObject):
    """
    Validates the OpenAPI Specification link object - §4.8.20
    """

    operationRef: URI | None = None
    operationId: str | None = None
    parameters: dict[str, RuntimeExpression | JSONValue] | None = None
    requestBody: JSONValue | RuntimeExpression | None = None
    description: str | CommonMark | None = None
    server: ServerObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#link-object"
    )

    _not_operationref_and_operationid = mv.only_one_of(
        fields=["operationRef", "operationId"]
    )


@specification_extensions("x-")
class HeaderObject(GenericObject):
    """
    Validates the OpenAPI Specification link object - §4.8.20
    """

    # Common schema/content fields
    description: str | CommonMark | None = None
    required: bool | None = Field(default=False)
    deprecated: bool | None = Field(default=False)

    # Schema fields
    style: str | None = Field(default="simple")
    explode: bool | None = Field(default=False)
    schema_: SchemaObject | ReferenceObject | None = Field(alias="schema", default=None)
    example: JSONValue | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None

    # Content fields
    content: dict[str, MediaTypeObject] | None = None

    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#link-object"
    )

    _not_schema_and_content = mv.only_one_of(["schema_", "content"])


@specification_extensions("x-")
class XMLObject(GenericObject):
    """
    Validates the OpenAPI Specification object - §4.8.26
    """

    name: str | None = None
    namespace: URI | None = None
    prefix: str | None = None
    attribute: bool | None = Field(default=False)
    wrapped: bool | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#xml-object"
    )

    @field_validator("namespace", mode="after")
    @classmethod
    def _validate_namespace(cls, value: URI) -> URI:
        """
        Validates that the namespace is not a relative URI.
        """
        if value.type == URIType.RELATIVE:
            message = "XML namespace {value} cannot be a relative URI"
            Logger.log(
                {
                    "msg": message,
                    "type": "value_error",
                    "loc": (cls.__name__,),
                    "input": value,
                    "url": cls._reference_uri,
                }
            )

        return value


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
        "https://spec.openapis.org/oas/v3.0.4.html#schema-object"
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


OAUTH_FLOW_TYPES: set[str] = {
    "implicit",
    "authorizationCode",
    "clientCredentials",
    "password",
}


@specification_extensions("x-")
class OAuthFlowObject(GenericObject):
    """
    Validates the OpenAPI OAuth Flow object - §4.8.29
    """

    type: str | None = None
    authorizationUrl: URI | None = None
    tokenUrl: URI | None = None
    refreshUrl: URI | None = None
    scopes: dict[str, str] = Field(default={})
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#oauth-flow-object"
    )

    _implicit_has_authorization_url = mv.if_then(
        conditions={"type": "implicit"},
        consequences={"authorizationUrl": mv.UNKNOWN},
    )

    _token_url_not_implicit = mv.if_then(
        conditions={"tokenUrl": mv.UNKNOWN},
        consequences={"type": OAUTH_FLOW_TYPES ^ {"implicit"}},
    )

    _authorization_code_has_urls = mv.if_then(
        conditions={"type": "authorizationCode"},
        consequences={"authorizationUrl": mv.UNKNOWN, "tokenUrl": mv.UNKNOWN},
    )

    _authorization_url_not_credentials_password = mv.if_then(
        conditions={"authorizationUrl": mv.UNKNOWN},
        consequences={"type": OAUTH_FLOW_TYPES ^ {"clientCredentials", "password"}},
    )

    _client_credentials_has_token = mv.if_then(
        conditions={"type": "clientCredentials"},
        consequences={"tokenUrl": mv.UNKNOWN},
    )
    _password_has_token = mv.if_then(
        conditions={"type": "password"}, consequences={"tokenUrl": mv.UNKNOWN}
    )


@specification_extensions("-x")
class OAuthFlowsObject(GenericObject):
    """
    Validates the OpenAPI OAuth Flows object - §4.8.28

    SPECFIX: Not all of these should be optional as an OAuth2 workflow
    without any credentials will not do anything.
    """

    implicit: OAuthFlowObject | None = None
    password: OAuthFlowObject | None = None
    clientCredentials: OAuthFlowObject | None = None
    authorizationCode: OAuthFlowObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#oauth-flow-object"
    )

    @model_validator(mode="before")
    @classmethod
    def _push_down_type(cls, data: Any) -> Any:
        """
        Adds the type of OAuth2 flow, e.g. implicit, password to the child
        OAuthFlowObject so that additional validation can be done on this object.
        """

        for k, v in data.items():
            if isinstance(v, OAuthFlowObject):
                raise NotImplementedError("Must pass a dict")

            if v:
                data[k]["type"] = k

        return data


class SecuritySchemeObject(GenericObject):
    """
    Validates the OpenAPI Security Scheme object - §4.8.27
    """

    type: str
    description: str | CommonMark | None = None
    name: str | None = None
    in_: str | None = Field(default=None, alias="in")
    scheme: HTTPAuthenticationScheme | None = None
    bearerFormat: str | None = None
    flows: OAuthFlowsObject | None = None
    openIdConnectUrl: URI | None = None

    _SECURITY_SCHEME_TYPES: ClassVar[set[str]] = {
        "apiKey",
        "http",
        "oauth2",
        "openIdConnect",
    }

    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#security-scheme-object-0"
    )

    _type_in_enum = mv.if_then(
        conditions={"type": mv.UNKNOWN}, consequences={"type": _SECURITY_SCHEME_TYPES}
    )

    _apikey_has_name_and_in = mv.if_then(
        conditions={"type": "apiKey"},
        consequences={"name": mv.UNKNOWN, "in_": ("query", "header", "cookie")},
    )

    _http_has_scheme = mv.if_then(
        conditions={"type": "http"}, consequences={"scheme": mv.UNKNOWN}
    )

    _oauth2_has_flows = mv.if_then(
        conditions={"type": "oauth2"}, consequences={"flows": mv.UNKNOWN}
    )

    _open_id_connect_has_url = mv.if_then(
        conditions={"type": "openIdConnect"},
        consequences={"openIdConnectUrl": mv.UNKNOWN},
    )

    _flows_not_oauth2 = mv.if_then(
        conditions={"flows": None},
        consequences={"type": _SECURITY_SCHEME_TYPES ^ {"oauth2"}},
    )


type _Requirement = dict[str, list[str]]


# NB This is implemented as a RootModel as there are no pre-defined field names.
class SecurityRequirementObject(RootModel[list[_Requirement] | _Requirement]):
    """
    Validates the OpenAPI Specification security requirement object - §4.8.30:
    """

    # FIXME: The name must be a valid Security Scheme - need to use post-processing
    # FIXME If the security scheme is of type "oauth2" or "openIdConnect", then the
    # value must be a list For other security scheme types, the array MAY contain a
    # list of role names which are required for the execution
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.0.4.html#security-requirement-object"
    )


@specification_extensions("x-")
class PathItemObject(GenericObject):
    """Validates the OpenAPI Specification path item object - §4.8.9"""

    ref_: URI | None = Field(alias="$ref", default=None)
    summary: str | None = None
    description: str | CommonMark | None = None
    get: OperationObject | None = None
    put: OperationObject | None = None
    post: OperationObject | None = None
    delete: OperationObject | None = None
    options: OperationObject | None = None
    head: OperationObject | None = None
    patch: OperationObject | None = None
    trace: OperationObject | None = None
    servers: list[ServerObject] | None = None
    parameters: list[ParameterObject | ReferenceObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#path-item-object"
    )


@specification_extensions("x-")
class ComponentsObject(GenericObject):
    """
    Validates the OpenAPI Specification components object - §4.8.7
    """

    schemas: dict[str, SchemaObject] | None = None
    responses: dict[str, ResponseObject | ReferenceObject] | None = None
    parameters: dict[str, ParameterObject | ReferenceObject] | None = None
    examples: dict[str, ExampleObject | ReferenceObject] | None = None
    requestBodies: dict[str, RequestBodyObject | ReferenceObject] | None = None
    headers: dict[str, HeaderObject | ReferenceObject] | None = None
    securitySchemes: dict[str, SecuritySchemeObject | ReferenceObject] | None = None
    links: dict[str, LinkObject | ReferenceObject] | None = None
    callbacks: dict[str, CallbackObject | ReferenceObject] | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/v3.0.4.html#components-object"
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
    servers: list[ServerObject] | None = Field(default=[ServerObject(url=URI("/"))])
    paths: PathsObject
    components: ComponentsObject | None = None
    security: list[SecurityRequirementObject] | None = None
    tags: list[TagObject] | None = None
    externalDocs: ExternalDocumentationObject | None = None
    _reference_uri: ClassVar[str] = (
        "https://spec.openapis.org/oas/3.0.4.html#openapi-object"
    )
