"""
Exceptions, declared here to not put in __init__
"""


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

    def __init__(self, message: str, reference_uri: str | None = None):
        self.message = message
        self.reference_uri = reference_uri
