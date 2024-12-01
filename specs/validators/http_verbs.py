from pydantic import Field
from typing import Annotated

HTTP_VERBS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"]


HTTPVerb = Annotated[
    str,
    Field(strict=True, pattern='|'.join(HTTP_VERBS))
    ]