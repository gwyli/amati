"""
Helper functions for tests, e.g. create a search strategy for all all data
types but one.
"""

import string
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from abnf.parser import ParseError
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import BaseModel

from amati.fields import URI
from amati.grammars import rfc6901

ExcludedTypes = type[Any] | tuple[type[Any], ...]
path_safe_chars = string.ascii_letters + string.digits + "-_."


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
def network_path_uris(draw: st.DrawFn) -> URI:
    """
    Generate network path URIs (e.g., //example.com/path)
    """

    candidate = draw(urls())

    return URI(candidate.split(":")[1])  # Remove scheme to create network path


@st.composite
def relative_uris(draw: st.DrawFn) -> URI:
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

    return URI(f"{path}{query}{fragment}")


@st.composite
def json_pointers(draw: st.DrawFn) -> URI:
    while True:
        pointer = draw(relative_uris())
        try:
            candidate = rfc6901.Rule("json-pointer").parse_all(pointer).value
            break
        except ParseError:
            continue

    return URI(f"#{candidate}")


def uri_strategy() -> st.SearchStrategy:
    """
    Generate URIs including absolute, relative, and JSON Pointer URIs"""
    return st.one_of(urls(), relative_uris(), json_pointers())


def relative_paths() -> st.SearchStrategy:
    """
    Generate relative file system paths
    """
    return st.text(alphabet=path_safe_chars, min_size=1).map(Path)


def absolute_paths() -> st.SearchStrategy:
    """
    Generate absolute file system paths
    """

    def make_absolute_path(root: str, parts: list[str]) -> Path:
        return Path("/", root, *parts)

    return st.builds(
        make_absolute_path,
        st.text(alphabet=path_safe_chars, min_size=1),
        st.lists(st.text(alphabet=path_safe_chars, min_size=1), max_size=3),
    )


def file_strategy() -> st.SearchStrategy:
    """
    Generate both relative and absolute file system paths
    """
    return st.one_of(relative_paths(), absolute_paths())


@st.composite
def pydantic_models(draw: st.DrawFn) -> type[BaseModel]:
    """Generate Pydantic BaseModel subclasses for testing"""
    class_name = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu",)),
            min_size=1,
            max_size=10,
        )
    )

    # Dynamically create a Pydantic model
    model: type = type(class_name, (BaseModel,), {"__module__": "__main__"})
    return model
