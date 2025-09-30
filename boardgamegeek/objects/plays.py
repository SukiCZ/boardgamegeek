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

from boardgamegeek.exceptions import BGGError
from boardgamegeek.utils import DictObject


class PlaysessionPlayer(DictObject):
    """
    Class representing a player in a play session

    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """

    @property
    def username(self) -> str | None:
        """
        :return: username
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("username")

    @property
    def user_id(self) -> int | None:
        """
        :return: user id
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("user_id")

    @property
    def name(self) -> str | None:
        """
        :return: name
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("name")

    @property
    def startposition(self) -> str | None:
        """
        :return: strting position
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("startposition")

    @property
    def new(self) -> str | None:
        """
        :return: `1` or `0` (new or not)
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("new")

    @property
    def win(self) -> str | None:
        """
        :return: `1` or `0` (win or not)
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("win")

    @property
    def rating(self) -> str | None:
        """
        :return: `1` or `0` (rated or not)
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("rating")

    @property
    def score(self) -> str | None:
        """
        :return: score
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("score")

    @property
    def color(self) -> str | None:
        """
        :return: color
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("color")


class PlaySession(DictObject):
    """
    Container for a play session information.

    :param dict data: a dictionary containing the collection data
    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """

    def __init__(self, data: dict[str, Any]):
        if "id" not in data:
            raise BGGError("missing id of PlaySession")

        kw = copy(data)

        if "date" in kw:
            if not isinstance(kw["date"], datetime.datetime):
                try:
                    kw["date"] = datetime.datetime.strptime(kw["date"], "%Y-%m-%d")
                except ValueError:
                    kw["date"] = None

        # create "nice" dictionaries out of plain ones, so you can .dot access stuff.
        self._players = [PlaysessionPlayer(player) for player in kw.get("players", [])]

        super().__init__(kw)

    def _format(self, log: logging.Logger) -> None:
        log.info(f"play id         : {self.id}")
        log.info(f"play user id    : {self.user_id}")
        if self.date:
            try:
                log.info("play date       : {}".format(self.date.strftime("%Y-%m-%d")))
            except ValueError:
                # strftime doesn't like dates before 1900 (and it seems that someone logged plays before 1900 :D)
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

    @property
    def id(self) -> int:
        """
        :return: id
        :rtype: integer
        :return: ``None`` if n/a
        """
        return int(self._data["id"])

    @property
    def user_id(self) -> int | None:
        """
        :return: id of the user owning this play session
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("user_id")

    @property
    def date(self) -> datetime.datetime | None:
        """
        :return: the date of the play session
        :rtype: datetime.datetime
        :return: ``None`` if n/a
        """
        return self._data.get("date")

    @property
    def quantity(self) -> int | None:
        """
        :return: number of recorded plays
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("quantity")

    @property
    def duration(self) -> int | None:
        """
        :return: duration of the play session
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("duration")

    @property
    def incomplete(self) -> bool:
        """
        :return: incomplete session
        :rtype: bool
        """
        return bool(self._data.get("incomplete"))

    @property
    def nowinstats(self) -> int | None:
        """
        :rtype: integer
        :return:
        """
        return self._data.get("nowinstats")

    @property
    def location(self) -> str | None:
        """
        :return:
        """
        return self._data.get("location")

    @property
    def game_id(self) -> int | None:
        """
        :return: played game id
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("game_id")

    @property
    def game_name(self) -> str | None:
        """
        :return: played game name
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("game_name")

    @property
    def comment(self) -> str | None:
        """
        :return: comment on the play session
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("comment")

    @property
    def players(self) -> list[PlaysessionPlayer]:
        """
        :return: list of players in this play session
        :rtype: list of :py:class:`boardgamegeek.plays.PlaysessionPlayer`
        """
        return self._players


class Plays(DictObject):
    """
    A list of play sessions, associated either to a user or to a game.

    :param dict data: a dictionary containing the collection data
    """

    def __init__(self, data: dict[str, Any]):
        kw = copy(data)
        self._plays = []

        for p in kw.get("plays", []):
            self._plays.append(PlaySession(p))

        super().__init__(kw)

    def __getitem__(self, item: int) -> PlaySession:
        return self._plays.__getitem__(item)

    def __len__(self) -> int:
        return len(self._plays)

    @property
    def plays(self) -> list[PlaySession]:
        """
        :return: play sessions
        :rtype: list of :py:class:`boardgamegeek.plays.PlaySession`
        """
        return self._plays

    @property
    def plays_count(self) -> int:
        """
        :return: plays count, as reported by the server
        :rtype: integer
        """
        return int(self._data.get("plays_count", 0))


class UserPlays(Plays):
    def _format(self, log: logging.Logger) -> None:
        log.info(f"plays of        : {self.user} ({self.user_id})")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")

    def add_play(self, data: dict[str, Any]) -> None:
        kw = copy(data)
        # User plays don't have the ID set in the XML
        kw["user_id"] = self.user_id
        self._plays.append(PlaySession(kw))

    @property
    def user(self) -> str | None:
        """
        :return: name of the playlist owner
        :rtype: str
        :return: ``None`` if this is the playlist of a game (not an user's)
        """
        return self._data.get("username")

    @property
    def user_id(self) -> int | None:
        """
        :return: id of the playlist owner
        :rtype: integer
        :return: ``None`` if this is the playlist of a game (not an user's)
        """
        return self._data.get("user_id")


class GamePlays(Plays):
    def _format(self, log: logging.Logger) -> None:
        log.info(f"plays of game id: {self.game_id}")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")

    def add_play(self, data: dict[str, Any]) -> None:
        self._plays.append(PlaySession(data))

    @property
    def game_id(self) -> int | None:
        """
        :return: id of the game this plays list belongs to
        :rtype: integer
        :return: ``None`` if this list is that of an user
        """
        return self._data.get("game_id")
