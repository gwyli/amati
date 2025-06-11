"""
Validates a URI according to the RFC3986 ABNF grammar
"""

import json
import pathlib
from enum import Enum
from typing import Optional, Self

import idna
from abnf import Node, ParseError, Rule
from abnf.grammars import rfc3986, rfc3987

from amati import AmatiValueError, Reference
from amati.fields import Str as _Str
from amati.grammars import rfc6901

DATA_DIRECTORY = pathlib.Path(__file__).parent.parent.resolve() / "data"

with open(DATA_DIRECTORY / "schemes.json", "r", encoding="utf-8") as f:
    SCHEMES = json.loads(f.read())


class Scheme(_Str):
    """Represents a URI scheme with validation and status tracking.

    This class validates URI schemes according to RFC 3986 standards and
    provides information about their registration status with IANA. It
    inherits from _Str to provide string-like behavior while adding
    scheme-specific functionality.

    Attributes:
        status: The IANA registration status of the scheme. Common values
            include "Permanent", "Provisional", "Historical", or None for
            unregistered schemes.

    Example:
        >>> Scheme("https").status
        'Permanent'
    """

    status: Optional[str] = None

    def __init__(self, value: str) -> None:
        """Initialize a new Scheme instance with validation.

        Args:
            value: The scheme string

        Raises:
            AmatiValueError: If the provided value does not conform to RFC 3986
                scheme syntax rules.
        """

        super().__init__()

        # Validate the scheme against RFC 3986 syntax rules
        # This will raise ParseError if the scheme is invalid
        try:
            rfc3986.Rule("scheme").parse_all(value)
        except ParseError as e:
            raise AmatiValueError(
                f"{value} is not a valid URI scheme",
                reference=Reference(
                    title="Uniform Resource Identifier (URI): Generic Syntax",
                    section="3.1 - Scheme",
                    url="https://www.rfc-editor.org/rfc/rfc3986#section-3.1",
                ),
            ) from e

        # Look up the scheme in the IANA registry to get status info
        # Returns None if the scheme is not in the registry
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
        scheme: The URI scheme component (e.g., "http", "https").
        authority: The authority component.
        path: The path component
        query: The query string component
        fragment: The fragment identifier
        is_iri: Whether this is an Internationalized Resource Identifier.

    Example:
        >>> uri = URI("https://example.com/path?query#fragment")
        >>> uri.scheme
        'https'
        >>> uri.authority
        'example.com'
        >>> uri.type
        <URIType.ABSOLUTE: 'absolute'>
    """

    scheme: Optional[Scheme] = None
    authority: Optional[str] = None
    host: Optional[str] = None
    path: Optional[str] = None
    query: Optional[str] = None
    fragment: Optional[str] = None
    # RFC 3987 Internationalized Resource Identifier (IRI) flag
    is_iri: bool = False

    _attribute_map: dict[str, str] = {
        "authority": "authority",
        "iauthority": "authority",
        "host": "host",
        "ihost": "host",
        "path-abempty": "path",
        "path-absolute": "path",
        "path-noscheme": "path",
        "path-rootless": "path",
        "path-empty": "path",
        "ipath-abempty": "path",
        "ipath-absolute": "path",
        "ipath-noscheme": "path",
        "ipath-rootless": "path",
        "ipath-empty": "path",
        "query": "query",
        "iquery": "query",
        "fragment": "fragment",
        "ifragment": "fragment",
    }

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
        if self.authority:
            return URIType.NON_RELATIVE
        if self.path:
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
            value: A string representing a URI.

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
        rules_to_attempt: tuple[Rule, ...] = (
            rfc3986.Rule("URI"),
            rfc3987.Rule("IRI"),
            rfc3986.Rule("hier-part"),
            rfc3987.Rule("ihier-part"),
            rfc3986.Rule("relative-ref"),
            rfc3987.Rule("irelative-ref"),
        )

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
            elif self.host:
                # If the host is IDNA encoded then the URI is an IRI.
                # IDNA encoded URIs will successfully parse with RFC 3986
                self.is_iri = idna.decode(self.host, uts46=True) != self.host.lower()

            # Successfully parsed - stop attempting other rules
            break

        # A URI is invalid if it contains only a fragment without scheme, authority,
        # or path.
        if not self.scheme and not self.authority and not self.path:
            raise AmatiValueError(
                f"{value} does not contain a scheme, authority or path"
            )

    def _add_attributes(self: Self, node: Node):
        """
        Recursively extract and set attributes from the parsed ABNF grammar tree.

        This method traverses the parsed grammar tree and assigns values to the
        appropriate class attributes based on the node names and types encountered.
        Special handling is provided for scheme nodes (converted to Scheme objects).

        Args:
            node: The current node from the parsed ABNF grammar tree.
        """

        for child in node.children:

            # If the node name is in the URI annotations, set the attribute
            if child.name == "scheme":
                self.__dict__["scheme"] = Scheme(child.value)
            elif child.name in self._attribute_map:
                self.__dict__[self._attribute_map[child.name]] = child.value

            # If the child is a node with children, recursively add attributes
            # This is necessary for nodes that have nested structures, such as
            # the hier-part that may contain subcomponents.
            if child.children:
                self._add_attributes(child)


class URIWithVariables(URI):
    """
    Extends URI to cope with URIs with variable components, e.g.
    https://{username}.example.com/api/v1/{resource}

    Expected to be used where tooling is required to use string interpolation to
    generate a valid URI. Will change `{username}` to `username` for validation,
    but return the original string when called.

    Attributes:
        scheme: The URI scheme component (e.g., "http", "https").
        authority: The authority component.
        path: The path component
        query: The query string component
        fragment: The fragment identifier
        is_iri: Whether this is an Internationalized Resource Identifier.
        tld_registered: Whether the top-level domain is registered with IANA.

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

        Raises:
            ValueError: If there are unbalanced or embedded braces in the URI
            AmatiValueError: If the value is None
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
