"""
Helper functions for tests, e.g. create a search strategy for all all data
types but one.
"""

import random
from typing import Any, Optional, Sequence, Tuple, Type, Union

from hypothesis import strategies as st

ExcludedTypes = Union[Type[Any], Tuple[Type[Any], ...]]


def everything_except(excluded_types: ExcludedTypes) -> st.SearchStrategy[Any]:
    """Generate arbitrary values excluding instances of specified types.

    Args:
        excluded_types: A type or tuple of types to exclude from generation.

    Returns:
        A strategy that generates values not matching the excluded type(s).
    """
    return (
        st.from_type(type)  # type: ignore
        .flatmap(st.from_type)
        .filter(lambda x: not isinstance(x, excluded_types))  # type: ignore
    )


def text_excluding_empty_string() -> st.SearchStrategy[str]:
    """Return a Hypothesis strategy for generating non-empty strings."""

    return st.text().filter(lambda x: x != "")


def none_and_empty_string(type_: Any) -> st.SearchStrategy[Any]:
    """Returns a Hypothesis strategy for generating an empty object and None"""
    return st.sampled_from([None, type_()])


def random_choice_empty(sequence: Sequence[Any]) -> Optional[Any]:
    """Return a random element from a sequence, or None if the sequence is empty.

    Args:
        sequence: A sequence of elements to choose from.

    Returns:
        A random element from the sequence, or None if sequence is empty.
    """
    return random.choice(sequence) if sequence else None
