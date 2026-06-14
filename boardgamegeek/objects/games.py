"""
:mod:`boardgamegeek.games` - Games information
==============================================

.. module:: boardgamegeek.objects.games
   :platform: Unix, Windows
   :synopsis: classes for storing games information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import datetime
import logging
import warnings
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from ..exceptions import BGGError
from ..utils import fix_unsigned_negative, fix_url
from .things import Thing


class BoardGameRank(Thing):
    type: str | None = None
    friendly_name: str | None = Field(None, alias="friendlyname")
    value: str | None = None
    rating_bayes_average: float | None = Field(None, alias="bayesaverage")

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_value_to_str(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v)


class PlayerSuggestion(BaseModel):
    """
    Player Suggestion
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    player_count: str
    best: int
    recommended: int
    not_recommended: int

    @computed_field
    @property
    def numeric_player_count(self) -> int:
        """
        Convert player count to an int
        If player count contains a + symbol
        then add one to the player count
        """
        if "+" in self.player_count:
            return int(self.player_count[:-1]) + 1
        return int(self.player_count)

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BoardGameStats(BaseModel):
    """
    Statistics about a board game
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    users_rated: int | None = Field(None, alias="usersrated")
    rating_average: float | None = Field(None, alias="average")
    rating_bayes_average: float | None = Field(None, alias="bayesaverage")
    rating_stddev: float | None = Field(None, alias="stddev")
    rating_median: float | None = Field(None, alias="median")
    users_owned: int | None = Field(None, alias="owned")
    users_trading: int | None = Field(None, alias="trading")
    users_wanting: int | None = Field(None, alias="wanting")
    users_wishing: int | None = Field(None, alias="wishing")
    users_commented: int | None = Field(None, alias="numcomments")
    rating_num_weights: int | None = Field(None, alias="numweights")
    rating_average_weight: float | None = Field(None, alias="averageweight")
    ranks: list[BoardGameRank] = Field(default_factory=list)
    bgg_rank: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _build_ranks(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        rank_dicts = data.get("ranks", [])
        bgg_rank: int | None = None
        for rank in rank_dicts:
            if rank.get("name") == "boardgame":
                try:
                    bgg_rank = int(rank["value"])
                except (KeyError, TypeError, ValueError):
                    pass
        data["bgg_rank"] = bgg_rank
        return data

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BoardGameComment(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    commenter: str = Field(alias="username")
    comment: str
    rating: float

    def _format(self, log: logging.Logger) -> None:
        log.info(f"comment by {self.commenter} (rating: {self.rating}): {self.comment}")

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BoardGameVideo(Thing):
    """
    Object containing information about a board game video
    """

    category: str | None = None
    link: str | None = None
    language: str | None = None
    uploader: str | None = None
    uploader_id: int | None = None
    post_date: datetime.datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _process_video_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "post_date" in data and not isinstance(data["post_date"], datetime.datetime):
            try:
                data["post_date"] = datetime.datetime.strptime(data["post_date"][:-6], "%Y-%m-%dT%H:%M:%S")
            except (ValueError, TypeError, IndexError):
                data["post_date"] = None
        if "uploader_id" in data and not isinstance(data["uploader_id"], int):
            try:
                data["uploader_id"] = int(data["uploader_id"])
            except (ValueError, TypeError):
                data["uploader_id"] = None
        return data

    def _format(self, log: logging.Logger) -> None:
        log.info(f"video id          : {self.id}")
        log.info(f"video title       : {self.name}")
        log.info(f"video category    : {self.category}")
        log.info(f"video link        : {self.link}")
        log.info(f"video language    : {self.language}")
        log.info(f"video uploader    : {self.uploader}")
        log.info(f"video uploader id : {self.uploader_id}")
        log.info(f"video posted at   : {self.post_date}")


class BoardGameVersion(Thing):
    """
    Object containing information about a board game version
    """

    artist: str | None = None
    depth: float | None = None
    length: float | None = None
    language: str | None = None
    product_code: str | None = None
    publisher: str | None = None
    weight: float | None = None
    width: float | None = None
    year: int | None = Field(None, alias="yearpublished")
    thumbnail: str | None = None
    image: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _fix_urls(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["thumbnail", "image"]:
            if field in data:
                data[field] = fix_url(data[field])
        return data

    def __repr__(self) -> str:
        return f"BoardGameVersion (id: {self.id})"

    def _format(self, log: logging.Logger) -> None:
        log.info(f"version id           : {self.id}")
        log.info(f"version name         : {self.name}")
        log.info(f"version language     : {self.language}")
        log.info(f"version publisher    : {self.publisher}")
        log.info(f"version artist       : {self.artist}")
        log.info(f"version product code : {self.product_code}")
        log.info(f"W x L x D            : {self.width} x {self.length} x {self.depth}")
        log.info(f"weight               : {self.weight}")
        log.info(f"year                 : {self.year}")


class MarketplaceListing(BaseModel):
    """
    Object containing information about a marketplace listing
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    list_date: datetime.datetime | None = None
    price: float | None = None
    currency: str | None = None
    condition: str | None = None
    notes: str | None = None
    link: str | None = None

    def _format(self, log: logging.Logger) -> None:
        log.info(f"listing date       : {self.list_date}")
        log.info(f"listing price    : {self.price}")
        log.info(f"listing currency : {self.currency}")
        log.info(f"listing condition: {self.condition}")
        log.info(f"listing notes    : {self.notes}")
        log.info(f"listing link     : {self.link}")

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BaseGame(Thing):
    def __init__(self, data: dict[str, Any]):
        self._thumbnail = fix_url(data["thumbnail"]) if "thumbnail" in data else None
        self._image = fix_url(data["image"]) if "image" in data else None
        if "stats" not in data:
            raise BGGError("invalid data")

        self._stats = BoardGameStats(data["stats"])

        self._versions: list[BoardGameVersion] = []
        self._versions_set: set[int] = set()
        self._year_published: int | None = None

        try:
            self._year_published = fix_unsigned_negative(data["yearpublished"])
        except (KeyError, TypeError):
            pass

        for version in data.get("versions", []):
            try:
                if version["id"] not in self._versions_set:
                    self._versions.append(BoardGameVersion(version))
                    self._versions_set.add(version["id"])
            except KeyError:
                raise BGGError("invalid version data")

        self._marketplace: list[MarketplaceListing] = []

        for listing in data.get("marketplace", []):
            try:
                self._marketplace.append(MarketplaceListing(listing))
            except KeyError:
                raise BGGError("invalid marketplace data")

        super().__init__(data)

    @property
    def thumbnail(self) -> str | None:
        """
        :return: thumbnail URL
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._thumbnail

    @property
    def image(self) -> str | None:
        """
        :return: image URL
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._image

    @property
    def year(self) -> int | None:
        """
        :return: publishing year
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._year_published

    @property
    def min_players(self) -> int | None:
        """
        :return: minimum number of players
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("minplayers")

    @property
    def max_players(self) -> int | None:
        """
        :return: maximum number of players
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("maxplayers")

    @property
    def min_playing_time(self) -> int | None:
        """
        Minimum playing time
        :return: ``None if n/a
        :rtype: integer
        """
        return self._data.get("minplaytime")

    @property
    def max_playing_time(self) -> int | None:
        """
        Maximum playing time
        :return: ``None if n/a
        :rtype: integer
        """
        return self._data.get("maxplaytime")

    @property
    def playing_time(self) -> int | None:
        """
        :return: playing time
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("playingtime")

    # TODO: create properties to access the stats

    @property
    def users_rated(self) -> int | None:
        """
        :return: how many users rated the game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.users_rated

    @property
    def rating_average(self) -> float | None:
        """
        :return: average rating
        :rtype: float
        :return: ``None`` if n/a
        """
        return self._stats.rating_average

    @property
    def rating_bayes_average(self) -> float | None:
        """
        :return: bayes average rating
        :rtype: float
        :return: ``None`` if n/a
        """
        return self._stats.rating_bayes_average

    @property
    def rating_stddev(self) -> float | None:
        """
        :return: standard deviation
        :rtype: float
        :return: ``None`` if n/a
        """
        return self._stats.rating_stddev

    @property
    def rating_median(self) -> float | None:
        """
        :return:
        :rtype: float
        :return: ``None`` if n/a
        """
        return self._stats.rating_median

    @property
    def ranks(self) -> list[BoardGameRank]:
        """
        :return: rankings of this game
        :rtype: list of :py:class:`boardgamegeek.games.BoardGameRank`
        :return: ``None`` if n/a
        """
        return self._stats.ranks

    @property
    def bgg_rank(self) -> int | None:
        """
        :return: The board game geek rank of this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.bgg_rank

    @property
    def boardgame_rank(self) -> int | None:
        warnings.warn("deprecated, use 'bgg_rank' instead", DeprecationWarning, stacklevel=2)
        return self.bgg_rank


class CollectionBoardGame(BaseGame):
    """
    A boardgame retrieved from the collection information, which has less information than the one retrieved
    via the /thing api and which also contains some user-specific information.
    """

    def _format(self, log: logging.Logger) -> None:
        log.info(f"boardgame id      : {self.id}")
        log.info(f"boardgame name    : {self.name}")
        log.info(f"number of plays   : {self.numplays}")
        log.info(f"last modified     : {self.last_modified}")
        log.info(f"rating            : {self.rating}")
        log.info(f"own               : {self.owned}")
        log.info(f"preordered        : {self.preordered}")
        log.info(f"previously owned  : {self.prev_owned}")
        log.info(f"want              : {self.want}")
        log.info(f"want to buy       : {self.want_to_buy}")
        log.info(f"want to play      : {self.want_to_play}")
        log.info(f"wishlist          : {self.wishlist}")
        log.info(f"wishlist priority : {self.wishlist_priority}")
        log.info(f"for trade         : {self.for_trade}")
        log.info(f"comment           : {self.comment}")
        for v in self._versions:
            v._format(log)

    @property
    def lastmodified(self) -> str | None:
        warnings.warn("deprecated, use 'last_modified' instead", DeprecationWarning, stacklevel=2)
        return self._data.get("lastmodified")

    @property
    def last_modified(self) -> str | None:
        """
        :return: last modified date
        :rtype: str
        """
        return self._data.get("lastmodified")

    @property
    def version(self) -> BoardGameVersion | None:
        if self._versions:
            return self._versions[0]
        else:
            return None

    @property
    def numplays(self) -> int:
        return int(self._data.get("numplays", 0))

    @property
    def rating(self) -> float | None:
        """
        :return: user's rating of the game
        :rtype: float
        :return: ``None`` if n/a
        """
        return self._data.get("rating")

    @property
    def owned(self) -> bool:
        """
        :return: game owned
        :rtype: bool
        """
        return bool(int(self._data.get("own", 0)))

    @property
    def preordered(self) -> bool:
        """
        :return: game preordered
        :rtype: bool
        """
        return bool(int(self._data.get("preordered", 0)))

    @property
    def prev_owned(self) -> bool:
        """
        :return: game previously owned
        :rtype: bool
        """
        return bool(int(self._data.get("prevowned", 0)))

    @property
    def want(self) -> bool:
        """
        :return: game wanted
        :rtype: bool
        """
        return bool(int(self._data.get("want", 0)))

    @property
    def want_to_buy(self) -> bool:
        """
        :return: want to buy
        :rtype: bool
        """
        return bool(int(self._data.get("wanttobuy", 0)))

    @property
    def want_to_play(self) -> bool:
        """
        :return: want to play
        :rtype: bool
        """
        return bool(int(self._data.get("wanttoplay", 0)))

    @property
    def for_trade(self) -> bool:
        """
        :return: game for trading
        :rtype: bool
        """
        return bool(int(self._data.get("fortrade", 0)))

    @property
    def wishlist(self) -> bool:
        """
        :return: game on wishlist
        :rtype: bool
        """
        return bool(int(self._data.get("wishlist", 0)))

    @property
    def wishlist_priority(self) -> str | None:
        # TODO: convert to int (it's str)
        return self._data.get("wishlistpriority")

    @property
    def comment(self) -> str:
        """
        :return: comment left by user
        :rtype: str
        """
        return str(self._data.get("comment", ""))


class BoardGame(BaseGame):
    """
    Object containing information about a board game
    """

    def __init__(self, data: dict[str, Any]):
        self._expansions: list[Thing] = []  # list of Thing for the expansions
        self._expansions_set: set[int] = set()  # set for making sure things are unique
        for exp in data.get("expansions", []):
            try:
                if exp["id"] not in self._expansions_set:
                    self._expansions_set.add(exp["id"])
                    self._expansions.append(Thing(exp))
            except KeyError:
                raise BGGError("invalid expansion data")

        self._expands: list[Thing] = []  # list of Thing which this item expands
        self._expands_set: set[int] = set()  # set for keeping things unique
        for exp in data.get("expands", []):  # for all the items this game expands, create a Thing
            try:
                if exp["id"] not in self._expands_set:
                    self._expands_set.add(exp["id"])
                    self._expands.append(Thing(exp))
            except KeyError:
                raise BGGError("invalid expanded game data")

        self._videos: list[BoardGameVideo] = []
        self._videos_ids: set[int] = set()
        for video in data.get("videos", []):
            try:
                if video["id"] not in self._videos_ids:
                    self._videos.append(BoardGameVideo(video))
                    self._videos_ids.add(video["id"])
            except KeyError:
                raise BGGError("invalid video data")

        self._comments: list[BoardGameComment] = []
        for comment in data.get("comments", []):
            self.add_comment(comment)

        self._player_suggestion: list[PlayerSuggestion] = []
        if "suggested_players" in data and "results" in data["suggested_players"]:
            for count, result in data["suggested_players"]["results"].items():
                suggestion_data = {
                    "player_count": count,
                    "best": result["best_rating"],
                    "recommended": result["recommended_rating"],
                    "not_recommended": result["not_recommended_rating"],
                }
                self._player_suggestion.append(PlayerSuggestion(suggestion_data))

        super().__init__(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id: {self.id})"

    def add_comment(self, data: dict[str, Any]) -> None:
        self._comments.append(BoardGameComment(data))

    def add_expanded_game(self, data: dict[str, Any]) -> None:
        """
        Add a game expanded by this one

        :param dict data: expanded game's data
        :raises: :py:exc:`boardgamegeek.exceptions.BoardGameGeekError` if data is invalid
        """
        try:
            if data["id"] not in self._expands_set:
                self._data["expands"].append(data)
                self._expands_set.add(data["id"])
                self._expands.append(Thing(data))
        except KeyError:
            raise BGGError("invalid expanded game data")

    def add_expansion(self, data: dict[str, Any]) -> None:
        """
        Add an expansion of this game

        :param dict data: expansion data
        :raises: :py:exc:`boardgamegeek.exceptions.BoardGameGeekError` if data is invalid
        """
        try:
            if data["id"] not in self._expansions_set:
                self._data["expansions"].append(data)
                self._expansions_set.add(data["id"])
                self._expansions.append(Thing(data))
        except KeyError:
            raise BGGError("invalid expansion data")

    def _format(self, log: logging.Logger) -> None:
        log.info(f"boardgame id      : {self.id}")
        log.info(f"boardgame name    : {self.name}")
        log.info(f"boardgame rank    : {self.bgg_rank}")
        if self.alternative_names:
            for alternative_name in self.alternative_names:
                log.info(f"alternative name  : {alternative_name}")
        log.info(f"year published    : {self.year}")
        log.info(f"minimum players   : {self.min_players}")
        log.info(f"maximum players   : {self.max_players}")
        log.info(f"playing time      : {self.playing_time}")
        log.info(f"minimum age       : {self.min_age}")
        log.info(f"thumbnail         : {self.thumbnail}")
        log.info(f"image             : {self.image}")

        log.info(f"is expansion      : {self.expansion}")
        log.info(f"is accessory      : {self.accessory}")

        if self.expansions:
            log.info("expansions")
            for expansion in self.expansions:
                log.info(f"- {expansion.name}")

        if self.expands:
            log.info("expands")
            for expand in self.expands:
                log.info(f"- {expand.name}")

        if self.categories:
            log.info("categories")
            for category in self.categories:
                log.info(f"- {category}")

        if self.families:
            log.info("families")
            for family in self.families:
                log.info(f"- {family}")

        if self.mechanics:
            log.info("mechanics")
            for mechanic in self.mechanics:
                log.info(f"- {mechanic}")

        if self.implementations:
            log.info("implementations")
            for implementation in self.implementations:
                log.info(f"- {implementation}")

        if self.designers:
            log.info("designers")
            for designer in self.designers:
                log.info(f"- {designer}")

        if self.artists:
            log.info("artistis")
            for artist in self.artists:
                log.info(f"- {artist}")

        if self.publishers:
            log.info("publishers")
            for publisher in self.publishers:
                log.info(f"- {publisher}")

        if self.videos:
            log.info("videos")
            for video in self.videos:
                video._format(log)
                log.info("--------")

        if self.versions:
            log.info("versions")
            for version in self.versions:
                version._format(log)
                log.info("--------")

        if self.player_suggestions:
            log.info("Player Suggestions")
            for suggestion in self.player_suggestions:
                log.info(
                    f"- {suggestion.player_count} - Best: {suggestion.best}, "
                    f"Recommended: {suggestion.recommended}, "
                    f"Not Recommended: {suggestion.not_recommended}"
                )
                log.info("--------")

        log.info(f"users rated game  : {self.users_rated}")
        log.info(f"users avg rating  : {self.rating_average}")
        log.info(f"users b-avg rating: {self.rating_bayes_average}")
        log.info(f"users commented   : {self.users_commented}")
        log.info(f"users owned       : {self.users_owned}")
        log.info(f"users wanting     : {self.users_wanting}")
        log.info(f"users wishing     : {self.users_wishing}")
        log.info(f"users trading     : {self.users_trading}")
        log.info(f"ranks             : {self.ranks}")
        log.info(f"description       : {self.description}")
        if self.comments:
            for c in self.comments:
                c._format(log)

    @property
    def alternative_names(self) -> list[str]:
        """
        :return: alternative names
        :rtype: list of str
        """
        names = self._data.get("alternative_names", [])
        return [str(name) for name in names]

    @property
    def description(self) -> str:
        """
        :return: description
        :rtype: str
        """
        return str(self._data.get("description", ""))

    @property
    def families(self) -> list[str]:
        """
        :return: families
        :rtype: list of str
        """
        families = self._data.get("families", [])
        return [str(family) for family in families]

    @property
    def categories(self) -> list[str]:
        """
        :return: categories
        :rtype: list of str
        """
        categories = self._data.get("categories", [])
        return [str(category) for category in categories]

    @property
    def comments(self) -> list[BoardGameComment]:
        return self._comments

    @property
    def mechanics(self) -> list[str]:
        """
        :return: mechanics
        :rtype: list of str
        """
        mechanics = self._data.get("mechanics", [])
        return [str(mechanic) for mechanic in mechanics]

    @property
    def expansions(self) -> list[Thing]:
        """
        :return: expansions
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self._expansions

    @property
    def expands(self) -> list[Thing]:
        """
        :return: games this item expands
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self._expands

    @property
    def implementations(self) -> list[str]:
        """
        :return: implementations
        :rtype: list of str
        """
        implementations = self._data.get("implementations", [])
        return [str(implementation) for implementation in implementations]

    @property
    def designers(self) -> list[str]:
        """
        :return: designers
        :rtype: list of str
        """
        designers = self._data.get("designers", [])
        return [str(designer) for designer in designers]

    @property
    def artists(self) -> list[str]:
        """
        :return: artists
        :rtype: list of str
        """
        artists = self._data.get("artists", [])
        return [str(artist) for artist in artists]

    @property
    def publishers(self) -> list[str]:
        """
        :return: publishers
        :rtype: list of str
        """
        publishers = self._data.get("publishers", [])
        return [str(publisher) for publisher in publishers]

    @property
    def expansion(self) -> bool:
        """
        :return: True if this item is an expansion
        :rtype: bool
        """
        return bool(self._data.get("expansion", False))

    @property
    def accessory(self) -> bool:
        """
        :return: True if this item is an accessory
        :rtype: bool
        """
        return bool(self._data.get("accessory", False))

    @property
    def min_age(self) -> int | None:
        """
        :return: minimum recommended age
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._data.get("minage")

    @property
    def users_owned(self) -> int | None:
        """
        :return: number of users owning this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.users_owned

    @property
    def users_trading(self) -> int | None:
        """
        :return: number of users trading this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.users_trading

    @property
    def users_wanting(self) -> int | None:
        """
        :return: number of users wanting this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.users_wanting

    @property
    def users_wishing(self) -> int | None:
        """
        :return: number of users wishing for this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.users_wishing

    @property
    def users_commented(self) -> int | None:
        """
        :return: number of user comments
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.users_commented

    @property
    def rating_num_weights(self) -> int | None:
        """
        :return:
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self._stats.rating_num_weights

    @property
    def rating_average_weight(self) -> float | None:
        """
        :return: average weight
        :rtype: float
        :return: ``None`` if n/a
        """
        return self._stats.rating_average_weight

    @property
    def videos(self) -> list[BoardGameVideo]:
        """
        :return: videos of this game
        :rtype: list of :py:class:`boardgamegeek.game.BoardGameVideo`
        """
        return self._videos

    @property
    def versions(self) -> list[BoardGameVersion]:
        """
        :return: versions of this game
        :rtype: list of :py:class:`boardgamegeek.game.BoardGameVersion`
        """
        return self._versions

    @property
    def marketplace(self) -> list[MarketplaceListing]:
        """
        :return: marketplace listings of this game
        :rtype: list of :py:class:`boardgamegeek.game.MarketplaceListing`
        """
        return self._marketplace

    @property
    def player_suggestions(self) -> list[PlayerSuggestion]:
        """
        :return player suggestion list with votes
        :rtype: list of dicts
        """
        return self._player_suggestion
