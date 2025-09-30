"""
:mod:`boardgamegeek.collection` - Collection information
========================================================

.. module:: boardgamegeek.collection
   :platform: Unix, Windows
   :synopsis: classes for storing collection information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import logging
from collections.abc import Generator
from copy import copy
from typing import Any

from ..exceptions import BGGError
from ..utils import DictObject
from .games import CollectionBoardGame


class Collection(DictObject):
    """
    A dictionary-like object represeting a ``Collection``

    :param dict data: a dictionary containing the collection data
    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """

    def __init__(self, data: dict[str, Any]):
        kw = copy(data)

        self._items: list[CollectionBoardGame] = []
        self.__game_ids: set[int] = set()

        for game in kw.get("items", []):
            self.add_game(game)

        super().__init__(kw)

    def _format(self, log: logging.Logger) -> None:
        log.info(f"owner    : {self.owner}")
        log.info(f"size     : {len(self)} items")

        log.info("items")

        for i in self:
            i._format(log)
            log.info("")

    def add_game(self, game: dict[str, Any]) -> None:
        """
        Add a game to the ``Collection``

        :param dict game: game data
        :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
        """
        try:
            # Collections can have duplicate elements (different collection ids), so don't add the same thing
            # multiple times
            if game["id"] not in self.__game_ids:
                self.__game_ids.add(game["id"])
                self._items.append(CollectionBoardGame(game))
        except KeyError:
            raise BGGError("invalid game data")

    def __getitem__(self, item: int) -> CollectionBoardGame:
        return self._items.__getitem__(item)

    def __str__(self) -> str:
        return f"{self.owner}'s collection, {len(self)} items"

    def __repr__(self) -> str:
        return f"Collection: (owner: {self.owner}, items: {len(self)})"

    def __len__(self) -> int:
        return len(self._items)

    @property
    def owner(self) -> str | None:
        """
        Return the collection's owner

        :returns: the collection's owner
        :rtype: str
        """
        return self._data.get("owner")

    @property
    def items(self) -> list[CollectionBoardGame]:
        """
        Returns the items in the collection

        :returns: the items in the collection
        :rtype: list of :py:class:`boardgamegeek.games.CollectionBoardGame`
        """
        return self._items

    def __iter__(self) -> Generator[CollectionBoardGame]:
        yield from self._items
