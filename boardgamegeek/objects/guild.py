"""
:mod:`boardgamegeek.guild` - Guild information
==============================================

.. module:: boardgamegeek.guild
   :platform: Unix, Windows
   :synopsis: classes for storing guild information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import logging
from typing import Any
from collections.abc import Generator

from pydantic import Field, model_validator

from .things import Thing


class Guild(Thing):
    """
    Class containing guild information
    """

    created: str | None = None
    category: str | None = None
    website: str | None = None
    manager: str | None = None
    description: str | None = None
    members_count: int = Field(0, alias="member_count")
    country: str | None = None
    city: str | None = None
    postalcode: str | None = None
    addr1: str | None = None
    addr2: str | None = None
    state: str | None = Field(None, alias="stateorprovince")
    members: set[str] = Field(default_factory=set)

    @model_validator(mode="before")
    @classmethod
    def _coerce_members(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "members" in data and isinstance(data["members"], list):
            data["members"] = set(data["members"])
        return data

    @property
    def address(self) -> str | None:
        parts = [self.addr1, self.addr2]
        str_parts = [str(p) for p in parts if p]
        return " ".join(str_parts) or None

    def _format(self, log: logging.Logger) -> None:
        log.info(f"id         : {self.id}")
        log.info(f"name       : {self.name}")
        log.info(f"category   : {self.category}")
        log.info(f"manager    : {self.manager}")
        log.info(f"website    : {self.website}")
        log.info(f"description: {self.description}")
        log.info(f"country    : {self.country}")
        log.info(f"state      : {self.state}")
        log.info(f"city       : {self.city}")
        log.info(f"address    : {self.address}")
        log.info(f"postal code: {self.postalcode}")
        if self.members:
            log.info(f"{len(self.members)} members")
            for i in self.members:
                log.info(f" - {i}")

    def add_member(self, member: str) -> None:
        self.members.add(member)

    def __len__(self) -> int:
        return len(self.members)

    def __repr__(self) -> str:
        return f"Guild (id: {self.id})"

    def __iter__(self) -> Generator[str]:  # type: ignore[override]
        yield from self.members
