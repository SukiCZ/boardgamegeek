"""
:mod:`boardgamegeek.hotitems` - BoardGameGeek "Hot Items"
=========================================================

.. module:: boardgamegeek.hotitems
   :platform: Unix, Windows
   :synopsis: classes for handling hot items information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>
"""

from __future__ import annotations

import logging
from typing import Any
from collections.abc import Generator

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .things import Thing
from ..utils import fix_url


class HotItem(Thing):
    """
    A hot item from a list. Can refer to either
    an item (``boardgame``, ``videogame``, etc.),
    a person (``rpgperson``, ``boardgameperson``)
    or even a company (``boardgamecompany``, ``videogamecompany``),
    depending on the type of hot list retrieved.
    """

    rank: int
    year: int | None = Field(None, alias="yearpublished")
    thumbnail: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _fix_thumbnail(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "thumbnail" in data:
            data["thumbnail"] = fix_url(data["thumbnail"])
        return data

    def __repr__(self) -> str:
        return f"HotItem (id: {self.id})"

    def _format(self, log: logging.Logger) -> None:
        log.info(f"hot item id        : {self.id}")
        log.info(f"hot item name      : {self.name}")
        log.info(f"hot item rank      : {self.rank}")
        log.info(f"hot item published : {self.year}")
        log.info(f"hot item thumbnail : {self.thumbnail}")


class HotItems(BaseModel):
    """
    A collection of :py:class:`boardgamegeek.hotitems.HotItem`
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    items: list[HotItem] = Field(default_factory=list)

    def add_hot_item(self, data: dict[str, Any]) -> None:
        """
        Add a new hot item to the container

        :param data: dictionary containing the data
        """
        self.items.append(HotItem.model_validate(data))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Generator[HotItem]:
        yield from self.items

    def __getitem__(self, item: int) -> HotItem:
        return self.items[item]

    def data(self) -> dict[str, Any]:
        return self.model_dump()
