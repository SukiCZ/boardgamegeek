"""
:mod:`boardgamegeek.search` - Search results
============================================

.. module:: boardgamegeek.search
   :platform: Unix, Windows
   :synopsis: classes for handling search results

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import logging
from typing import Any

from boardgamegeek.exceptions import BGGError
from boardgamegeek.objects.things import Thing
from boardgamegeek.utils import fix_unsigned_negative


class SearchResult(Thing):
    """
    Result of a search
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._yearpublished = None
        if "yearpublished" in data:
            if type(data["yearpublished"]) not in [int, type(None)]:
                raise BGGError("yearpublished is not valid")

            self._yearpublished = fix_unsigned_negative(data["yearpublished"])

        super().__init__(data)

    def _format(self, log: logging.Logger) -> None:
        log.info(f"searched item id   : {self.id}")
        log.info(f"searched item name : {self.name}")
        log.info(f"searched item type : {self.type}")
        log.info(f"searched item year : {self.year}")

    @property
    def type(self) -> str:
        return str(self._data["type"])

    @property
    def year(self) -> int | None:
        return self._yearpublished
