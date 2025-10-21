"""
Helper functions for tests, e.g. create a search strategy for all all data
types but one.
"""

from typing import Any
from urllib.parse import urlparse

from abnf.parser import ParseError
from hypothesis import strategies as st
from hypothesis.provisional import urls

from amati.grammars import rfc6901

ExcludedTypes = type[Any] | tuple[type[Any], ...]


def everything_except(excluded_types: ExcludedTypes) -> st.SearchStrategy[Any]:
    """Generate arbitrary values excluding instances of specified types.

    Args:
        excluded_types: A type or tuple of types to exclude from generation.

    Returns:
        A strategy that generates values not matching the excluded type(s).
    """
    return (
        st.from_type(object)
        .map(type)
        .filter(lambda x: not isinstance(x, excluded_types))
    )


def text_excluding_empty_string() -> st.SearchStrategy[str]:
    """Return a Hypothesis strategy for generating non-empty strings."""

    return st.text().filter(lambda x: x != "")


def none_and_empty_object(type_: Any) -> st.SearchStrategy[Any]:
    """Returns a Hypothesis strategy for generating an empty object and None"""
    return st.sampled_from([None, type_()])


@st.composite
def relative_uris(draw: st.DrawFn) -> str:
    """
    Generate relative URIs
    """

    candidate = draw(urls())

    parsed = urlparse(candidate)
    # urlparse parses the URI http://a.com// with a path of //, which indicates that
    # the succeeding item is the authority in RFC 2986 when actual authority/netloc
    # is removed.
    path = f"/{parsed.path.lstrip('/')}"
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""

    return f"{path}{query}{fragment}"


@st.composite
def json_pointers(draw: st.DrawFn) -> str:
    while True:
        pointer = draw(relative_uris())
        try:
            candidate = rfc6901.Rule("json-pointer").parse_all(pointer).value
            break
        except ParseError:
            continue

    return f"#{candidate}"
