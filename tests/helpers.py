"""
Helper functions for tests, e.g. create a search strategy for all all data
types but one.
"""

from typing import Any

from hypothesis import strategies as st

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


def none_and_empty_string(type_: Any) -> st.SearchStrategy[Any]:
    """Returns a Hypothesis strategy for generating an empty object and None"""
    return st.sampled_from([None, type_()])
