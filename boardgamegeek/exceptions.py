"""
:mod:`boardgamegeek.exceptions` - Exceptions
============================================

.. module:: boardgamegeek.exceptions
   :platform: Unix, Windows
   :synopsis: exceptions used in the package

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>
"""


class BGGValueError(ValueError):
    """invalid parameters"""

    pass


class BGGError(Exception):
    pass


class BGGItemNotFoundError(BGGError):
    """Requested item was not found"""

    pass


class BGGApiTimeoutError(BGGError):
    """Network timeout conditions"""

    pass


class BGGApiError(BGGError):
    """An error related to the BGG XML2 API"""

    pass


class BGGApiRetryError(BGGApiError):
    """The request to the BGG XML2 API should be retried"""

    pass


BoardGameGeekError = BGGError
BoardGameGeekTimeoutError = BGGApiTimeoutError
BoardGameGeekAPIError = BGGApiError
BGGApiRetryError = BGGApiRetryError
