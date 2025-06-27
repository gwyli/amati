"""
Amati is a specification validator, built to put a specification into
a single datatype and validate on instantiation.
"""

import importlib.metadata

__version__ = importlib.metadata.version("amati")

# Imports are here for convenience, they're not going to be used here
# pylint: disable=unused-import
# pyright: reportUnusedImport=false

from amati.amati import dispatch, run
from amati.exceptions import AmatiValueError
