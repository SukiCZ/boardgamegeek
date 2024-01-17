"""
:mod:`boardgamegeek.plays` - BoardGameGeek "Plays"
==================================================

.. module:: boardgamegeek.plays
   :platform: Unix, Windows
   :synopsis: classes for handling plays/play sessions

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""
import datetime
from copy import copy

from boardgamegeek.exceptions import BGGError
from boardgamegeek.utils import DictObject


class PlaysessionPlayer(DictObject):
    """
    Class representing a player in a play session

    :param dict data: a dictionary containing the collection data
    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """

    def __init__(self, data):
        self._data = data

    @property
    def username(self):
        """
        :return: user name
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("username")

    @property
    def user_id(self):
        """
        :return: user id
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("user_id")

    @property
    def name(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("name")

    @property
    def startposition(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("startposition")

    @property
    def new(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("new")

    @property
    def win(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("win")

    @property
    def rating(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("rating")

    @property
    def score(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("score")

    @property
    def color(self):
        """
        :return:
        :rtype:
        :return: ``None`` if n/a
        """
        return self._data.get("color")


class PlaySession(DictObject):
    """
    Container for a play session information.

    :param dict data: a dictionary containing the collection data
    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """

    def __init__(self, data):
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

    def _format(self, log):
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
                log.info(
                    "\t{} ({}): name: {}, score: {}".format(
                        player.username, player.user_id, player.name, player.score
                    )
                )

    @property
    def id(self):
        """
        :return: id
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("id")

    @property
    def user_id(self):
        """
        :return: id of the user owning this play session
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("user_id")

    @property
    def date(self):
        """
        :return: the date of the play session
        :rtype: datetime.datetime
        :return: ``None`` if n/a
        """
        return self._data.get("date")

    @property
    def quantity(self):
        """
        :return: number of recorded plays
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("quantity")

    @property
    def duration(self):
        """
        :return: duration of the play session
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("duration")

    @property
    def incomplete(self):
        """
        :return: incomplete session
        :rtype: bool
        """
        return bool(self._data.get("incomplete"))

    @property
    def nowinstats(self):
        """
        :return:
        """
        return self._data.get("nowinstats")

    @property
    def location(self):
        """
        :return:
        """
        return self._data.get("location")

    @property
    def game_id(self):
        """
        :return: played game id
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("game_id")

    @property
    def game_name(self):
        """
        :return: played game name
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("game_name")

    @property
    def comment(self):
        """
        :return: comment on the play session
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("comment")

    @property
    def players(self):
        return self._players


class Plays(DictObject):
    """
    A list of play sessions, associated either to an user or to a game.

    :param dict data: a dictionary containing the collection data
    """

    def __init__(self, data):
        kw = copy(data)
        self._plays = []

        for p in kw.get("plays", []):
            self._plays.append(PlaySession(p))

        super().__init__(kw)

    def __getitem__(self, item):
        return self._plays.__getitem__(item)

    def __len__(self):
        return len(self._plays)

    @property
    def plays(self):
        """
        :return: play sessions
        :rtype: list of :py:class:`boardgamegeek.plays.PlaySession`
        """
        return self._plays

    @property
    def plays_count(self):
        """
        :return: plays count, as reported by the server
        :rtype: integer
        """
        return self._data.get("plays_count", 0)


class UserPlays(Plays):
    def _format(self, log):
        log.info(f"plays of        : {self.user} ({self.user_id})")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")

    def add_play(self, data):
        kw = copy(data)
        # User plays don't have the ID set in the XML
        kw["user_id"] = self.user_id
        self._plays.append(PlaySession(kw))

    @property
    def user(self):
        """
        :return: name of the playlist owner
        :rtype: str
        :return: ``None`` if this is the playlist of a game (not an user's)
        """
        return self._data.get("username")

    @property
    def user_id(self):
        """
        :return: id of the playlist owner
        :rtype: integer
        :return: ``None`` if this is the playlist of a game (not an user's)
        """
        return self._data.get("user_id")


class GamePlays(Plays):
    def _format(self, log):
        log.info(f"plays of game id: {self.game_id}")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")

    def add_play(self, data):
        self._plays.append(PlaySession(data))

    @property
    def game_id(self):
        """
        :return: id of the game this plays list belongs to
        :rtype: integer
        :return: ``None`` if this list is that of an user
        """
        return self._data.get("game_id")
