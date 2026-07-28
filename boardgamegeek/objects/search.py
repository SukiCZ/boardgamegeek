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

from pydantic import Field, model_validator

from boardgamegeek.objects.things import Thing
from boardgamegeek.utils import fix_unsigned_negative


class SearchResult(Thing):
    """
    Result of a search
    """

    type: str
    year: int | None = Field(None, alias="yearpublished")

    @model_validator(mode="before")
    @classmethod
    def _fix_year(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "yearpublished" in data and data["yearpublished"] is not None:
            try:
                data["yearpublished"] = fix_unsigned_negative(int(data["yearpublished"]))
            except (ValueError, TypeError):
                data["yearpublished"] = None
        return data

    def _format(self, log: logging.Logger) -> None:
        log.info(f"searched item id   : {self.id}")
        log.info(f"searched item name : {self.name}")
        log.info(f"searched item type : {self.type}")
        log.info(f"searched item year : {self.year}")
