"""
Convenience, can import all types from one place
"""

# Imports are here for convenience, they're not going to be used here
# pylint: disable=unused-import
# pyright: reportUnusedImport=false

from amati.fields._custom_types import Str
from amati.fields.email import Email
from amati.fields.http_status_codes import HTTPStatusCode
from amati.fields.iso9110 import HTTPAuthenticationScheme
from amati.fields.media import MediaType
from amati.fields.spdx_licences import SPDXURL, SPDXIdentifier
from amati.fields.uri import URI, Scheme, URIType, URIWithVariables
