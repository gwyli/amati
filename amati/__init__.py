"""
Amati is a specification validator, built to put a specification into
a single datatype and validate on instantiation.
"""

__version__ = "0.1.0"

from typing import Optional

from amati.fields import References


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
