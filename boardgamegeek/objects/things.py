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

from pydantic import BaseModel, ConfigDict

from ..exceptions import BGGError  # noqa: F401  kept for import compat


class Thing(BaseModel):  # type: ignore[misc]
    """
    A thing, an object with a name and an id. Base class for various objects in the library.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int
    name: str

    def data(self) -> dict[str, Any]:
        return self.model_dump()  # type: ignore[no-any-return]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id: {self.id})"
