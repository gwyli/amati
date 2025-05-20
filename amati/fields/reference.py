"""
Citation object for each other object for providing more
information in errors and warnings.
"""

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
