"""
Validates a URI according to the RFC3986 ABNF grammar
"""

import json
import pathlib
from enum import Enum
from typing import Optional

import rfc3987
from abnf import ParseError

from amati import AmatiValueError, Reference
from amati.fields import _Str
from amati.grammars import rfc6901

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "schemes.json", "r", encoding="utf-8") as f:
    SCHEMES = json.loads(f.read())

with open(DATA_DIRECTORY / "tlds.json", "r", encoding="utf-8") as f:
    TLDS = json.loads(f.read())


class Scheme(_Str):
    status: Optional[str] = None

    def __init__(self, value: str):
        self.status = SCHEMES.get(value, None)


class URIType(str, Enum):

    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    NON_RELATIVE = "non-relative"
    JSON_POINTER = "JSON pointer"
    UNKNOWN = "unknown"


class URI(_Str):
    """
    Represents a Uniform Resource Identifier (URI) as defined in RFC 3986/3987.

    This class parses and validates URI strings, supporting standard URIs, IRIs
    (Internationalized Resource Identifiers), and JSON pointers. It provides attributes
    for accessing URI components and determining the URI type and validity.

    Attributes:
        scheme (Optional[str]): The URI scheme component (e.g., "http", "https",
            "file").
        authority (Optional[str]): The authority component (typically host/server).
        path (Optional[str]): The path component of the URI.
        query (Optional[str]): The query string component.
        fragment (Optional[str]): The fragment identifier component.
        is_iri (bool): Whether this is an Internationalized Resource Identifier
            (RFC 3987).
        scheme_status (Optional[str]): The registration status of the scheme with IANA,
            if known. Can be used
        tld_registered (Optional[bool]): Whether the TLD is registered with IANA.
    """

    scheme: Optional[Scheme] = None
    authority: Optional[str] = None
    path: Optional[str] = None
    query: Optional[str] = None
    fragment: Optional[str] = None
    # Is this an RFC 3987 "Internationalized Resource Identifier (IRI)
    # per RFC 3987
    is_iri: bool = False
    tld_registered: bool = False

    @property
    def type(self) -> URIType:
        """
        Determine the type of the URI.

        This property analyzes the URI components to classify the URI according to the
        URIType enumeration.

        Returns:
            URIType: The classified type of the URI (ABSOLUTE, NON_RELATIVE, RELATIVE,
                     JSON_POINTER, or UNKNOWN).
        """
        if self.scheme:
            return URIType.ABSOLUTE
        if self.authority:
            return URIType.NON_RELATIVE
        if self.path:
            if str(self).startswith("#"):
                return URIType.JSON_POINTER
            return URIType.RELATIVE
        return URIType.UNKNOWN

    def __init__(self, value: str):
        """
        Initialize a URI object by parsing a URI string.

        Parses the input string according to RFC 3986/3987 grammar rules for URIs/IRIs.
        Handles special cases like JSON pointers (RFC 6901) and performs validation.
        Sets appropriate attributes based on the parsed components.

        Args:
            value (str): A string representing a URI.

        Raises:
            AmatiValueError: If the input string is not a valid URI, or if essential
                components are missing.
        """

        if value is None:  # type: ignore
            raise AmatiValueError("None is not a valid URI; declare as Optional")

        candidate = value

        # The OAS standard is to use a fragment identifier
        # to indicate that it is a JSON pointer per RFC 6901, e.g.
        # "$ref": "#/components/schemas/pet".
        # The hash does not indicate that the URI is a fragment.

        if value.startswith("#"):
            candidate = value[1:]
            try:
                rfc6901.Rule("json-pointer").parse_all(candidate)
            except ParseError as e:
                raise AmatiValueError(
                    f"{value} is not a valid JSON pointer",
                    reference=Reference(
                        title="JavaScript Object Notation (JSON) Pointer",
                        section="6 - URI Fragment Identifier Representation",
                        url="https://www.rfc-editor.org/rfc/rfc6901#section-6",
                    ),
                ) from e

        # Parse as if the candidate were an IRI per RFC 3987.
        # Raises ValueError if invalid
        result = rfc3987.parse(candidate)

        for component, value in result.items():
            if not value:
                continue

            if component == "scheme":
                self.__dict__["scheme"] = Scheme(value)
            else:
                self.__dict__[component] = value

        # If an URI/IRI is invalid if only a fragment.
        if not self.scheme and not self.authority and not self.path:
            raise AmatiValueError(
                "{value} does not contain a scheme, authority or path"
            )

        # If valid according to RFC 3987 but not ASCII the candidate is a IRI
        # not a URI
        try:
            candidate.encode("ascii")
        except UnicodeEncodeError:
            self.is_iri = True

        if self.authority:
            tld_candidate = f".{self.authority.split(".")[-1]}"
            self.tld_registered = tld_candidate in TLDS


class URIWithVariables(URI):
    """
    Extends URI to cope with URIs with variable components, e.g.
    https://{username}.example.com/api/v1/{resource}

    Expected to be used where tooling is required to use string interpolation to
    generate a valid URI. Will change `{username}` to `username` for validation,
    but return the original string when called.

    Attributes:
        scheme (Optional[str]): The URI scheme component (e.g., "http", "https",
            "file").
        authority (Optional[str]): The authority component (typically host/server).
        path (Optional[str]): The path component of the URI.
        query (Optional[str]): The query string component.
        fragment (Optional[str]): The fragment identifier component.
        is_iri (bool): Whether this is an Internationalized Resource Identifier
            (RFC 3987).
        scheme_status (Optional[str]): The registration status of the scheme with IANA,
            if known. Can be used
        tld_registered (Optional[bool]): Whether the TLD is registered with IANA.

    Inherits:
        URI: Represents a Uniform Resource Identifier (URI) as defined in RFC 3986/3987.
    """

    def __init__(self, value: str):
        """
        Validate that the URI is a valid URI with variables.
        e.g. of the form:

        https://{username}.example.com/api/v1/{resource}

        Args:
            value: The URI to validate

        Returns:
            The original value, if valid

        Raises:
            ParseError: If the URI is not valid
        """

        if value is None:  # type: ignore
            raise ValueError

        # `string.format()` takes a dict of the key, value pairs to
        # replace to replace the keys inside braces. As we don't have the keys a dict
        # that returns the keys that `string.format()` is expecting will have the
        # effect of replacing '{a}b{c} with 'abc'.
        class MissingKeyDict(dict[str, str]):
            def __missing__(self, key: str) -> str:
                return key

        # Unbalanced or embedded braces, e.g. /example/{id{a}}/ or /example/{id
        # will cause a ValueError in .format_map().
        try:
            candidate = value.format_map(MissingKeyDict())
        except ValueError as e:
            raise ValueError(f"Unbalanced or embedded braces in {value}") from e

        super().__init__(candidate)
