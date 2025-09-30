"""
:mod:`boardgamegeek.things` - Generic objects
=============================================

.. module:: boardgamegeek.things
   :platform: Unix, Windows
   :synopsis: Generic objects

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

from typing import Any

from ..exceptions import BGGError
from ..utils import DictObject


class Thing(DictObject):
    """
    A thing, an object with a name and an id. Base class for various objects in the library.
    """

    def __init__(self, data: dict[str, Any]):
        if "id" not in data:
            raise BGGError("missing 'id' when trying to create a Thing")
        if "name" not in data:
            raise BGGError("missing 'name' when trying to create a Thing")

        try:
            self._id = int(data["id"])
        except ValueError:
            raise BGGError("id ({}) is not an int when trying to create a Thing".format(data["id"]))

        self._name = str(data["name"])

        super().__init__(data)

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id: {self.id})"
