"""
Amati is a specification validator, built to put a specification into
a single datatype and validate on instantiation.
"""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class Reference:
    """
    Attributes:
        title (str): Title of the referenced content
        section (str): Section of the referenced content
        url (str): URL where the referenced content can be found
    """

    title: Optional[str] = None
    section: Optional[str] = None
    url: Optional[str] = None


type ReferenceArray = Sequence[Reference]
type References = Reference | ReferenceArray


class AmatiValueError(ValueError):
    """
    Custom exception to allow adding of references to exceptions.


    Attributes:
        message (str): The explanation of why the exception was raised
        authority (Optional[ReferenceModel]): The reference to the standard that
            explains why the exception was raised

    Inherits:
        ValueError
    """

    def __init__(self, message: str, reference: Optional[References] = None):
        self.message = message
        self.reference = reference
