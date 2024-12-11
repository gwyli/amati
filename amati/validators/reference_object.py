"""
Citation object for each other object for providing more
information in errors and warnings.
"""

from types import NoneType
from typing import Annotated, Optional, Sequence, Union

from pydantic import AfterValidator, AnyUrl, BaseModel, Field


def _validate_after_url(value: Optional[str|AnyUrl]) -> Optional[str|AnyUrl]:
    """
    Validate that the URL is a valid URL.

    Args:
        value: The URL to validate
    """
    if value is None: return None
    
    if isinstance(value, AnyUrl): return value

    return str(AnyUrl(value))

class ReferenceModel(BaseModel):

    title: Annotated[Optional[str],
                     Field(default=None, description='Title of the referenced content')
    ]
    section: Annotated[Optional[str],
                       Field(default=None, description='Section of the referenced content')
    ] = None
    url: Annotated[Optional[str],
                   Field(default=None, description='URL of the specific web page where the referenced content can be found'),
                   AfterValidator(_validate_after_url)
                   ]


ReferencePrimitive = Union[ReferenceModel, NoneType]
ReferenceArray = Sequence[ReferencePrimitive]
Reference = Union[ReferencePrimitive, ReferenceArray]
