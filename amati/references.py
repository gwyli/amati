"""
Represents a reference, declared here to not put in __init__.
"""

from dataclasses import dataclass
from typing import Optional, Sequence


class AmatiReferenceException(Exception):
    message: str = "Cannot construct empty references"


@dataclass
class Reference:
    """
    Attributes:
        title : Title of the referenced content
        section : Section of the referenced content
        url : URL where the referenced content can be found
    """

    title: Optional[str] = None
    section: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):

        if not self.title and not self.section and not self.url:
            raise AmatiReferenceException


type ReferenceArray = Sequence[Reference]
type References = Reference | ReferenceArray
