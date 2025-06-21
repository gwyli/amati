"""
Tests amati/fields/media.py
"""

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from amati.fields.media import MediaType

MEDIA_TYPES = [
    "text/plain",
    "text/html",
    "text/css",
    "text/javascript",
    "application/json",
    "application/xml",
    "application/pdf",
    "application/zip",
    "application/octet-stream",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/svg+xml",
    "audio/mpeg",
    "audio/ogg",
    "video/mp4",
    "multipart/form-data",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/*",
    "image/*",
    "audio/*",
    "video/*",
    "application/*",
    "multipart/*",
    "message/*",
    "model/*",
    "font/*",
    "example/*",
    "text/html; q=0.8",
    "application/json; q=1.0",
    "image/png; q=0.9",
    "text/*; q=0.5",
    "application/xml; q=0.7",
    "audio/*; q=0.6",
    "video/mp4; q=0.8",
    "application/pdf; q=0.9",
    "image/jpeg;  q=0.7",
    "*/*",
]


@given(st.sampled_from(MEDIA_TYPES))
def test_media_type_valid(value: str):
    result = MediaType(value)
    assert " ".join(value.split()) == str(result)
    assert result.is_registered

    subtype_parameter = value.split("/")[1].split(";")

    if subtype_parameter[0] == "*":
        assert result.is_range

    if len(subtype_parameter) > 1:
        assert result.parameter


@given(st.text().filter(lambda x: x not in MEDIA_TYPES))
def test_media_type_invalid(value: str):

    # Exists just in case a valid media type is returned
    # NB: A RFC 7230 "token" is a valid sub-media-type
    # according to RFC
    pattern = r"[a-zA-Z0-9]+/[a-zA-Z0-9!#$%&'*+-.^_`|~]+"
    if re.match(pattern, value):  # pragma: no cover
        result = MediaType(value)
        assert not result.is_registered
        assert not result.is_range
    else:
        with pytest.raises(ValueError):
            MediaType(value)
