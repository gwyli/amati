"""
Validates the OpenAPI Specification version 3.1.1

Note that per https://spec.openapis.org/oas/v3.0.4.html#relative-references-in-api-description-uris  # pylint: disable=line-too-long

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

from amati import AmatiValueError, Reference
from amati import model_validators as mv
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
from amati.logging import Log, LogMixin
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

    name: Optional[str] = None
    url: Optional[URI] = None
    email: Optional[Email] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.0.4.html#contact-object",
        section="Contact Object",
    )


@specification_extensions("x-")
class LicenceObject(GenericObject):
    """
    A model representing the OpenAPI Specification licence object §4.8.4
    """

    name: str = Field(min_length=1)
    url: Optional[URI] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#license-object",
        section="License Object",
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
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#reference-object",
        section="Reference Object",
    )


@specification_extensions("x-")
class InfoObject(GenericObject):
    """
    Validates the OpenAPI Specification info object - §4.8.2:
    """

    title: str
    description: Optional[str | CommonMark] = None
    termsOfService: Optional[str] = None  # pylint: disable=invalid-name
    contact: Optional[ContactObject] = None
    license: Optional[LicenceObject] = None
    version: str
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.0.4.html#info-object",
        section="Info Object",
    )


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
        url="https://spec.openapis.org/oas/v3.0.4.html#discriminator-object",
        section="Security Scheme Object",
    )


@specification_extensions("x-")
class ExampleObject(GenericObject):
    """
    Validates the OpenAPI Specification example object - §4.8.19
    """

    summary: Optional[str] = None
    description: Optional[str | CommonMark] = None
    value: Optional[JSONValue] = None
    externalValue: Optional[URI] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#example-object",
        section="Example Object",
    )

    _not_value_and_external_value = mv.only_one_of(["value", "externalValue"])


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
        url="https://spec.openapis.org/oas/v3.0.4.html#server-variable-object",
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
                    type=Warning,
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
        url="https://spec.openapis.org/oas/v3.0.4.html#server-object",
        section="Server Object",
    )


@specification_extensions("x-")
class ExternalDocumentationObject(GenericObject):
    """
    Validates the OpenAPI Specification external documentation object - §4.8.22
    """

    description: Optional[str | CommonMark] = None
    url: URI
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#external-documentation-object",
        section="External Documentation Object",
    )


# FIXME: Specification extensions should be "^x-", but the implementation
# doesn't play well with ConfigDict(extra="allow"). This is the only case
# so less important to change as the eventual logic is still correct.
@specification_extensions(".*")
class PathsObject(GenericObject):
    """Validates the OpenAPI Specification paths object - §4.8.8"""

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def paths_are_uris(cls, data: Any) -> Any:
        """
        Validates that paths are valid URIs, it's allowed that they
        have variables, e.g. /pets or /pets/{petID}

        Special-case specification extensions, which are also allowed.
        """

        for field in data.keys():

            # Specification extensions
            if field.startswith("x-"):
                continue

            URIWithVariables(field)

        return data


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
    responses: "ResponsesObject"
    callbacks: Optional[dict[str, "CallbackObject | ReferenceObject"]] = None
    deprecated: Optional[bool] = False
    security: Optional[list["SecurityRequirementObject"]] = None
    servers: Optional[list[ServerObject]] = None

    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#operation-object",
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
    schema_: Optional["SchemaObject | ReferenceObject"] = Field(alias="schema")
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
class RequestBodyObject(GenericObject):
    """
    Validates the OpenAPI Specification request body object - §4.8.13
    """

    description: Optional[CommonMark | str] = None
    content: dict[str, "MediaTypeObject"]
    required: Optional[bool] = False
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#request-body-object",
        section="Request Body Object",
    )


@specification_extensions("x-")
class MediaTypeObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.14
    """

    schema_: Optional["SchemaObject | ReferenceObject"] = Field(
        alias="schema", default=None
    )
    # FIXME: Define example
    example: Optional[Any] = None
    examples: Optional[dict[str, ExampleObject | ReferenceObject]] = None
    encoding: Optional["EncodingObject"] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#media-type-object",
        section="Tag Object",
    )


@specification_extensions("x-")
class EncodingObject(GenericObject):
    """
    Validates the OpenAPI Specification media type object - §4.8.15
    """

    contentType: Optional[str] = None
    headers: Optional[dict[str, "HeaderObject | ReferenceObject"]] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#encoding object-object",
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
        url="https://spec.openapis.org/oas/v3.0.4.html#responses-object",
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
    headers: Optional[dict[str, "HeaderObject | ReferenceObject"]] = None
    content: Optional[dict[str, MediaTypeObject]] = None
    links: Optional[dict[str, "LinkObject | ReferenceObject"]] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#response-object",
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
        url="https://spec.openapis.org/oas/v3.0.4.html#callback-object",
        section="Callback Object",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, data: dict[str, Any]) -> dict[str, "PathItemObject"]:
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
        url="https://spec.openapis.org/oas/v3.0.4.html#tag-object",
        section="Tag Object",
    )


@specification_extensions("x-")
class LinkObject(GenericObject):
    """
    Validates the OpenAPI Specification link object - §4.8.20
    """

    operationRef: Optional[URI] = None
    operationId: Optional[str] = None
    parameters: Optional[dict[str, RuntimeExpression | JSONValue]] = None
    requestBody: Optional[JSONValue | RuntimeExpression] = None
    description: Optional[str | CommonMark] = None
    server: Optional[ServerObject] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#link-object",
        section="Link Object",
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
    description: Optional[str | CommonMark] = None
    required: Optional[bool] = Field(default=False)
    deprecated: Optional[bool] = Field(default=False)

    # Schema fields
    style: Optional[str] = Field(default="simple")
    explode: Optional[bool] = Field(default=False)
    schema_: Optional["SchemaObject | ReferenceObject"] = Field(
        alias="schema", default=None
    )
    example: Optional[JSONValue] = None
    examples: Optional[dict[str, ExampleObject | ReferenceObject]] = None

    # Content fields
    content: Optional[dict[str, MediaTypeObject]] = None

    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#link-object",
        section="Link Object",
    )

    _not_schema_and_content = mv.only_one_of(["schema_", "content"])


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
        url="https://spec.openapis.org/oas/v3.0.4.html#xml-object",
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
        url="https://spec.openapis.org/oas/v3.0.4.html#schema-object",
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

    type: Optional[str] = None
    authorizationUrl: Optional[URI] = None
    tokenUrl: Optional[URI] = None
    refreshUrl: Optional[URI] = None
    scopes: dict[str, str] = {}
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#oauth-flow-object",
        section="OAuth Flow Object",
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

    implicit: Optional[OAuthFlowObject] = None
    password: Optional[OAuthFlowObject] = None
    clientCredentials: Optional[OAuthFlowObject] = None
    authorizationCode: Optional[OAuthFlowObject] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#oauth-flow-object",
        section="OAuth Flows Object",
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
    description: Optional[str | CommonMark] = None
    name: Optional[str] = None
    in_: Optional[str] = Field(default=None, alias="in")
    scheme: Optional[HTTPAuthenticationScheme] = None
    bearerFormat: Optional[str] = None
    flows: Optional[OAuthFlowsObject] = None
    openIdConnectUrl: Optional[URI] = None

    _SECURITY_SCHEME_TYPES: ClassVar[set[str]] = {
        "apiKey",
        "http",
        "oauth2",
        "openIdConnect",
    }

    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#security-scheme-object-0",
        section="Security Scheme Object",
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
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.0.4.html#security-requirement-object",
        section="Security Requirement Object",
    )


@specification_extensions("x-")
class PathItemObject(GenericObject):
    """Validates the OpenAPI Specification path item object - §4.8.9"""

    ref_: Optional[URI] = Field(alias="$ref", default=None)
    summary: Optional[str] = None
    description: Optional[str | CommonMark] = None
    get: Optional[OperationObject] = None
    put: Optional[OperationObject] = None
    post: Optional[OperationObject] = None
    delete: Optional[OperationObject] = None
    options: Optional[OperationObject] = None
    head: Optional[OperationObject] = None
    patch: Optional[OperationObject] = None
    trace: Optional[OperationObject] = None
    servers: Optional[list[ServerObject]] = None
    parameters: Optional[list[ParameterObject | ReferenceObject]] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#path-item-object",
        section="Path Item Object",
    )


@specification_extensions("x-")
class ComponentsObject(GenericObject):
    """
    Validates the OpenAPI Specification components object - §4.8.7
    """

    schemas: Optional[dict[str, SchemaObject]] = None
    responses: Optional[dict[str, ResponseObject | ReferenceObject]] = None
    paremeters: Optional[dict[str, ParameterObject | ReferenceObject]] = None
    examples: Optional[dict[str, ExampleObject | ReferenceObject]] = None
    requestBodies: Optional[dict[str, RequestBodyObject | ReferenceObject]] = None
    headers: Optional[dict[str, HeaderObject | ReferenceObject]] = None
    securitySchemes: Optional[dict[str, SecuritySchemeObject | ReferenceObject]] = None
    links: Optional[dict[str, LinkObject | ReferenceObject]] = None
    callbacks: Optional[dict[str, CallbackObject | ReferenceObject]] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/v3.0.4.html#components-object",
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
    servers: Optional[list[ServerObject]] = Field(default=[ServerObject(url=URI("/"))])
    paths: PathsObject
    components: Optional[ComponentsObject] = None
    security: Optional[list[SecurityRequirementObject]] = None
    tags: Optional[list[TagObject]] = None
    externalDocs: Optional[ExternalDocumentationObject] = None
    _reference: ClassVar[Reference] = Reference(
        title=TITLE,
        url="https://spec.openapis.org/oas/3.0.4.html#openapi-object",
        section="OpenAPI Object",
    )
