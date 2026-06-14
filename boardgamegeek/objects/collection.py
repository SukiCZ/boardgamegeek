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
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ..exceptions import BGGError
from .games import CollectionBoardGame


class Collection(BaseModel):
    """
    A pydantic model representing a ``Collection``

    :param dict data: a dictionary containing the collection data
    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    owner: str | None = None
    items: list[CollectionBoardGame] = Field(default_factory=list)

    _game_ids: set[int] = PrivateAttr(default_factory=set)

    def model_post_init(self, __context: Any) -> None:
        self._game_ids = {item.id for item in self.items}

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
            if game["id"] not in self._game_ids:
                self._game_ids.add(game["id"])
                self.items.append(CollectionBoardGame.model_validate(game))
        except KeyError:
            raise BGGError("invalid game data")

    def __getitem__(self, item: int) -> CollectionBoardGame:
        return self.items[item]

    def __str__(self) -> str:
        return f"{self.owner}'s collection, {len(self)} items"

    def __repr__(self) -> str:
        return f"Collection: (owner: {self.owner}, items: {len(self)})"

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Generator[CollectionBoardGame]:
        yield from self.items

    def data(self) -> dict[str, Any]:
        return self.model_dump()
