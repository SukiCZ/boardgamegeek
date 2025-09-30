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
from copy import copy
from typing import Any
from collections.abc import Generator

from .things import Thing


class Guild(Thing):
    """
    Class containing guild information
    """

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

    def __init__(self, data: dict[str, Any]):
        kw = copy(data)

        if "members" in kw:
            self._members = set(kw.pop("members"))
        else:
            self._members = set()

        super().__init__(kw)

    @property
    def country(self) -> str | None:
        """
        :return: country
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("country")

    @property
    def city(self) -> str | None:
        """
        :return: city
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("city")

    @property
    def address(self) -> str | None:
        """
        :return: address (both fields concatenated)
        :rtype: str
        :return: ``None`` if n/a
        """
        parts = [self._data.get("addr1"), self._data.get("addr2")]
        str_parts: list[str] = [str(part) for part in parts if part]
        return " ".join(str_parts) or None

    @property
    def addr1(self) -> str | None:
        """
        :return: first field of the address
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("addr1")

    @property
    def addr2(self) -> str | None:
        """
        :return: second field of the address
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("addr2")

    @property
    def postalcode(self) -> int | None:
        """
        :return: postal code
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("postalcode")

    @property
    def state(self) -> str | None:
        """
        :return: state or provine
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("stateorprovince")

    @property
    def category(self) -> str | None:
        """
        :return: category
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("category")

    @property
    def members(self) -> set[str]:
        """
        :return: members of the guild
        :rtype: set of str
        """
        return self._members

    @property
    def members_count(self) -> int:
        """
        :return: number of members, as reported by the server
        :rtype: int
        """
        return int(self._data.get("member_count", 0))

    @property
    def description(self) -> str | None:
        """
        :return: description
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("description")

    @property
    def manager(self) -> str | None:
        """
        :return: manager
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("manager")

    @property
    def website(self) -> str | None:
        """
        :return: website address
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("website")

    def add_member(self, member: str) -> None:
        self._members.add(member)

    def __len__(self) -> int:
        return len(self._members)

    def __repr__(self) -> str:
        return f"Guild (id: {self.id})"

    def __iter__(self) -> Generator[str]:
        yield from self._members
