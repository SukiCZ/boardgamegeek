"""
:mod:`boardgamegeek.user` - BoardGameGeek "Users"
=================================================

.. module:: boardgamegeek.user
   :platform: Unix, Windows
   :synopsis: class handling user information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from pydantic import Field, model_validator

from .things import Thing


class User(Thing):
    """
    Information about a user.
    """

    firstname: str | None = None
    lastname: str | None = None
    avatar: str | None = Field(None, alias="avatarlink")
    last_login: datetime.datetime | None = Field(None, alias="lastlogin")
    state: str | None = Field(None, alias="stateorprovince")
    country: str | None = None
    homepage: str | None = Field(None, alias="webaddress")
    xbox_account: str | None = Field(None, alias="xboxaccount")
    wii_account: str | None = Field(None, alias="wiiaccount")
    steam_account: str | None = Field(None, alias="steam_account")
    psn_account: str | None = Field(None, alias="psnaccount")
    trade_rating: str | None = None
    buddies: list[Thing] = Field(default_factory=list)
    guilds: list[Thing] = Field(default_factory=list)
    hot: list[Thing] = Field(default_factory=list)
    top: list[Thing] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _ensure_lists(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["buddies", "guilds", "hot", "top"]:
            data.setdefault(field, [])
        return data

    def __str__(self) -> str:
        return f"User: {self.firstname} {self.lastname}"

    def __repr__(self) -> str:
        return f"User: {self.name} (id: {self.id})"

    def add_buddy(self, data: dict[str, Any]) -> None:
        self.buddies.append(Thing.model_validate(data))

    def add_guild(self, data: dict[str, Any]) -> None:
        self.guilds.append(Thing.model_validate(data))

    def add_top_item(self, data: dict[str, Any]) -> None:
        self.top.append(Thing.model_validate(data))

    def add_hot_item(self, data: dict[str, Any]) -> None:
        self.hot.append(Thing.model_validate(data))

    @property
    def total_buddies(self) -> int:
        """
        :return: number of buddies
        :rtype: integer
        """
        return len(self.buddies)

    @property
    def total_guilds(self) -> int:
        """
        :return: number of guilds
        :rtype: integer
        """
        return len(self.guilds)

    @property
    def top10(self) -> list[Thing]:
        """
        :return: user's top10
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self.top

    @property
    def hot10(self) -> list[Thing]:
        """
        :return: user's hot10
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self.hot

    def _format(self, log: logging.Logger) -> None:
        log.info(f"id          : {self.id}")
        log.info(f"login name  : {self.name}")
        log.info(f"first name  : {self.firstname}")
        log.info(f"last name   : {self.lastname}")
        log.info(f"state       : {self.state}")
        log.info(f"country     : {self.country}")
        log.info(f"home page   : {self.homepage}")
        log.info(f"avatar      : {self.avatar}")
        log.info(f"xbox acct   : {self.xbox_account}")
        log.info(f"wii acct    : {self.wii_account}")
        log.info(f"steam acct  : {self.steam_account}")
        log.info(f"psn acct    : {self.psn_account}")
        log.info(f"last login  : {self.last_login}")
        log.info(f"trade rating: {self.trade_rating}")
        log.info(
            "user has {} buddies{}".format(
                self.total_buddies,
                " (forever alone :'( )" if self.total_buddies == 0 else "",
            )
        )
        for b in self.buddies:
            log.info(f"- {b.name}")
        log.info(f"user is member in {self.total_guilds} guilds")
        for g in self.guilds:
            log.info(f"- {g.name}")
        log.info("top10 items")
        for i in self.top10:
            log.info(f"- {i.name} (id: {i.id})")
        log.info("hot10 items")
        for i in self.hot10:
            log.info(f"- {i.name} (id: {i.id})")
