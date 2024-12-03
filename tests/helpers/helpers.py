from typing import Any, Iterable
from hypothesis import strategies as st

import random

def everything_except(excluded_types: Any) -> st.SearchStrategy:
    return (
        st.from_type(type)
        .flatmap(st.from_type)
        .filter(lambda x: not isinstance(x, excluded_types))
    )

def text_excluding_empty_string() -> st.SearchStrategy:
    return st.text().filter(lambda x: x != '')


def random_choice_empty(iterable: Iterable) -> Any:
    return random.choice(iterable) if iterable else None