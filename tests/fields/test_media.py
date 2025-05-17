"""
Tests amati/fields/media.py
"""

from hypothesis import given
from hypothesis import strategies as st

from amati.fields.media import MediaType
from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class MediaTypeModel(GenericObject):
    media_type: MediaType


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
    "video/webm",
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
def test_media_type(value: str):
    with LogMixin.context():
        result = MediaTypeModel(media_type=value)  # type: ignore
        assert not LogMixin.logs

        assert " ".join(value.split()) == str(result.media_type)
