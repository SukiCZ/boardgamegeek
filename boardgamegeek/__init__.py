# coding: utf-8
"""
.. module:: boardgamegeek
   :platform: Unix, Windows
   :synopsis: interface to boardgamegeek.com

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>
"""

from .api import BGGClient, BGGChoose, BGGRestrictDomainTo, BGGRestrictPlaysTo, BGGRestrictSearchResultsTo, BGGRestrictCollectionTo
from .exceptions import BGGError, BGGApiRetryError, BGGApiError, BGGApiTimeoutError, BGGValueError, BGGItemNotFoundError
from .cache import CacheBackendNone, CacheBackendMemory, CacheBackendSqlite

__all__ = ["BGGClient", "BGGChoose", "BGGRestrictSearchResultsTo", "BGGRestrictPlaysTo", "BGGRestrictDomainTo",
           "BGGRestrictCollectionTo", "BGGError", "BGGValueError", "BGGApiRetryError", "BGGApiError",
           "BGGApiTimeoutError", "BGGItemNotFoundError", "CacheBackendNone", "CacheBackendSqlite", "CacheBackendMemory"]

__version__ = "1.0.1"
