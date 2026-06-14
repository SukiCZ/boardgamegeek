"""
:mod:`boardgamegeek.plays` - BoardGameGeek "Plays"
==================================================

.. module:: boardgamegeek.plays
   :platform: Unix, Windows
   :synopsis: classes for handling plays/play sessions

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import datetime
import logging
from copy import copy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlaysessionPlayer(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    username: str | None = None
    user_id: int | None = None
    name: str | None = None
    startposition: str | None = None
    new: str | None = None
    win: str | None = None
    rating: str | None = None
    score: str | None = None
    color: str | None = None

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class PlaySession(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int
    user_id: int | None = None
    date: datetime.datetime | None = None
    quantity: int | None = None
    duration: int | None = None
    incomplete: bool = False
    nowinstats: int | None = None
    location: str | None = None
    game_id: int | None = None
    game_name: str | None = None
    comment: str | None = None
    players: list[PlaysessionPlayer] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _parse_date(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "date" in data and not isinstance(data["date"], datetime.datetime):
            try:
                data["date"] = datetime.datetime.strptime(data["date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                data["date"] = None
        return data

    def _format(self, log: logging.Logger) -> None:
        log.info(f"play id         : {self.id}")
        log.info(f"play user id    : {self.user_id}")
        if self.date:
            try:
                log.info("play date       : {}".format(self.date.strftime("%Y-%m-%d")))
            except ValueError:
                pass
        log.info(f"play quantity   : {self.quantity}")
        log.info(f"play duration   : {self.duration}")
        log.info(f"play incomplete : {self.incomplete}")
        log.info(f"play nowinstats : {self.nowinstats}")
        log.info(f"play game       : {self.game_name} ({self.game_id})")
        log.info(f"play comment    : {self.comment}")
        if self.players:
            log.info("players")
            for player in self.players:
                log.info(f"\t{player.username} ({player.user_id}): name: {player.name}, score: {player.score}")

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class Plays(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    plays_count: int = 0
    plays: list[PlaySession] = Field(default_factory=list)

    def __getitem__(self, item: int) -> PlaySession:
        return self.plays[item]

    def __len__(self) -> int:
        return len(self.plays)

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class UserPlays(Plays):
    username: str | None = None
    user_id: int | None = None

    @property
    def user(self) -> str | None:
        return self.username

    def add_play(self, data: dict[str, Any]) -> None:
        kw = copy(data)
        kw["user_id"] = self.user_id
        self.plays.append(PlaySession.model_validate(kw))

    def _format(self, log: logging.Logger) -> None:
        log.info(f"plays of        : {self.user} ({self.user_id})")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")


class GamePlays(Plays):
    game_id: int | None = None

    def add_play(self, data: dict[str, Any]) -> None:
        self.plays.append(PlaySession.model_validate(data))

    def _format(self, log: logging.Logger) -> None:
        log.info(f"plays of game id: {self.game_id}")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")
