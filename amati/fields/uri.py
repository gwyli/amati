"""
Validates a URI according to the RFC3986 ABNF grammar
"""

import json
import pathlib
from enum import Enum
from typing import Optional, Self

from abnf import Node, ParseError, Rule
from abnf.grammars import rfc3986, rfc3987

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str
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


class URI(_Str):
    """
    A class representing a Uniform Resource Identifier (URI) as defined in
    RFC 3986/3987.

    This class parses and validates URI strings, supporting standard URIs, IRIs
    (Internationalized Resource Identifiers), and JSON pointers. It provides attributes
    for accessing URI components and determining the URI type and validity.

    The class attempts to parse URIs using multiple RFC specifications in order of
    preference, falling back to less restrictive parsing when necessary.

    Attributes:
        scheme (Optional[Scheme]): The URI scheme component (e.g., "http", "https").
        authority (Optional[str]): The authority component for standard URIs.
        iauthority (Optional[str]): The authority component for internationalized IRIs.
        path (Optional[str]): The path component for standard URIs.
        ipath (Optional[str]): The path component for internationalized IRIs.
        query (Optional[str]): The query string component for standard URIs.
        iquery (Optional[str]): The query string component for internationalized IRIs.
        fragment (Optional[str]): The fragment identifier for standard URIs.
        ifragment (Optional[str]): The fragment identifier for internationalized IRIs.
        is_iri (bool): Whether this is an Internationalized Resource Identifier.
        tld_registered (bool): Whether the top-level domain is registered with IANA.
    """

    scheme: Optional[Scheme] = None
    authority: Optional[str] = None
    iauthority: Optional[str] = None
    path: Optional[str] = None
    ipath: Optional[str] = None
    query: Optional[str] = None
    iquery: Optional[str] = None
    fragment: Optional[str] = None
    ifragment: Optional[str] = None
    # RFC 3987 Internationalized Resource Identifier (IRI) flag
    is_iri: bool = False
    tld_registered: bool = False

    # Valid path types from RFC 3986 grammar rules
    _path_types: frozenset[str] = frozenset(
        [
            "path-abempty",
            "path-absolute",
            "path-noscheme",
            "path-rootless",
            "path-empty",
        ]
    )

    # Valid internationalized path types from RFC 3987 grammar rules
    _ipath_types: frozenset[str] = frozenset(
        [
            "ipath-abempty",
            "ipath-absolute",
            "ipath-noscheme",
            "ipath-rootless",
            "ipath-empty",
        ]
    )

    @property
    def type(self) -> URIType:
        """
        Determine the type of the URI based on its components.

        This property analyzes the URI components to classify the URI according to the
        URIType enumeration. The classification follows a hierarchical approach:
        absolute URIs take precedence over non-relative, which take precedence over
        relative URIs.

        Returns:
            URIType: The classified type of the URI (ABSOLUTE, NON_RELATIVE, RELATIVE,
                     or JSON_POINTER).

        Raises:
            TypeError: If the URI has no scheme, authority, or path components.
        """

        if self.scheme:
            return URIType.ABSOLUTE
        if self.authority or self.iauthority:
            return URIType.NON_RELATIVE
        if self.path or self.ipath:
            if str(self).startswith("#"):
                return URIType.JSON_POINTER
            return URIType.RELATIVE

        # Should theoretically never be reached as if a URI does not have a scheme
        # authority or path an AmatiValueError should be raised. However, without
        # an additional return there is a code path in type() that doesn't return a
        # value. It's better to deal with the potential error case than ignore the
        # lack of a return value.
        raise TypeError(f"{str(self)} does not have a URI type.")  # pragma: no cover

    def __init__(self, value: str):
        """
        Initialize a URI object by parsing a URI string.

        Parses the input string according to RFC 3986/3987 grammar rules for URIs/IRIs.
        Handles special cases like JSON pointers (RFC 6901) and performs validation.
        Attempts multiple parsing strategies in order of preference.

        Args:
            value (str): A string representing a URI.

        Raises:
            AmatiValueError: If the input string is None, not a valid URI according to
                any supported RFC specification, is a JSON pointer with invalid syntax,
                or contains only a fragment without other components.
        """

        super().__init__()

        if value is None:  # type: ignore
            raise AmatiValueError("None is not a valid URI; declare as Optional")

        candidate = value

        # Handle JSON pointers as per OpenAPI Specification (OAS) standard.
        # OAS uses fragment identifiers to indicate JSON pointers per RFC 6901,
        # e.g., "$ref": "#/components/schemas/pet".
        # The hash symbol does not indicate a URI fragment in this context.

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

        # Attempt parsing with multiple RFC specifications in order of preference.
        # Start with most restrictive (RFC 3986 URI) and fall back to more permissive
        # specifications as needed.
        rules_to_attempt: list[Rule] = [
            rfc3986.Rule("URI"),
            rfc3987.Rule("IRI"),
            rfc3986.Rule("hier-part"),
            rfc3987.Rule("ihier-part"),
            rfc3986.Rule("relative-ref"),
            rfc3987.Rule("irelative-ref"),
        ]

        for rule in rules_to_attempt:
            try:
                result = rule.parse_all(candidate)
            except ParseError:
                # If the rule fails, continue to the next rule
                continue

            self._add_attributes(result)

            # Mark as IRI if parsed using RFC 3987 rules
            if rule.__module__ == rfc3987.__name__:
                self.is_iri = True

            # Successfully parsed - stop attempting other rules
            break

        # A URI is invalid if it contains only a fragment without scheme, authority,
        # or path.
        if (
            not self.scheme
            and not self.iauthority
            and not self.authority
            and not self.ipath
            and not self.path
        ):
            raise AmatiValueError(
                "{value} does not contain a scheme, authority or path"
            )

        # Check if the top-level domain is registered with IANA
        if self.authority:
            tld_candidate = f".{self.authority.split(".")[-1]}"
            self.tld_registered = tld_candidate in TLDS
        if self.iauthority:
            tld_candidate = f".{self.iauthority.split(".")[-1]}"
            self.tld_registered = tld_candidate in TLDS

    def _add_attributes(self: Self, node: Node):
        """
        Recursively extract and set attributes from the parsed ABNF grammar tree.

        This method traverses the parsed grammar tree and assigns values to the
        appropriate class attributes based on the node names and types encountered.
        Special handling is provided for scheme nodes (converted to Scheme objects)
        and path nodes (categorized by type).

        Args:
            node (Node): The current node from the parsed ABNF grammar tree.
        """

        if node.name in URI.__annotations__.keys():
            # If the node name is in the URI annotations, set the attribute
            self.__dict__[node.name] = node.value

        for child in node.children:

            if child.name == "scheme":
                self.__dict__["scheme"] = Scheme(child.value)
            if child.name in self._path_types:
                self.__dict__["path"] = child.value
            if child.name in self._ipath_types:
                self.__dict__["ipath"] = child.value
            elif child.name in URI.__annotations__.keys():
                self.__dict__[child.name] = child.value

            # Recursively process child nodes (LiteralNode has empty children list)
            self._add_attributes(child)


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
            raise AmatiValueError("None is not a valid URI; declare as Optional")

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
