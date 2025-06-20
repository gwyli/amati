"""
Amati is a specification validator, built to put a specification into
a single datatype and validate on instantiation.
"""

__version__ = "0.1.0"

# Imports are here for convenience, they're not going to be used here
# pylint: disable=unused-import
# pyright: reportUnusedImport=false

from amati.amati import dispatch, run
from amati.exceptions import AmatiValueError
from amati.references import AmatiReferenceException, Reference, References
