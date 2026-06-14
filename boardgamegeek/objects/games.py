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

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field, field_validator, model_validator

from ..exceptions import BGGError
from ..utils import fix_url
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
    thumbnail: str | None = None
    image: str | None = None
    year: int | None = Field(None, alias="yearpublished")
    min_players: int | None = Field(None, alias="minplayers")
    max_players: int | None = Field(None, alias="maxplayers")
    min_playing_time: int | None = Field(None, alias="minplaytime")
    max_playing_time: int | None = Field(None, alias="maxplaytime")
    playing_time: int | None = Field(None, alias="playingtime")
    stats: BoardGameStats
    versions: list[BoardGameVersion] = Field(default_factory=list)
    marketplace: list[MarketplaceListing] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _fix_base_game(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["thumbnail", "image"]:
            if field in data:
                data[field] = fix_url(data[field])
        return data

    @property
    def users_rated(self) -> int | None:
        """
        :return: how many users rated the game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.users_rated

    @property
    def rating_average(self) -> float | None:
        """
        :return: average rating
        :rtype: float
        :return: ``None`` if n/a
        """
        return self.stats.rating_average

    @property
    def rating_bayes_average(self) -> float | None:
        """
        :return: bayes average rating
        :rtype: float
        :return: ``None`` if n/a
        """
        return self.stats.rating_bayes_average

    @property
    def rating_stddev(self) -> float | None:
        """
        :return: standard deviation
        :rtype: float
        :return: ``None`` if n/a
        """
        return self.stats.rating_stddev

    @property
    def rating_median(self) -> float | None:
        """
        :return:
        :rtype: float
        :return: ``None`` if n/a
        """
        return self.stats.rating_median

    @property
    def ranks(self) -> list[BoardGameRank]:
        """
        :return: rankings of this game
        :rtype: list of :py:class:`boardgamegeek.games.BoardGameRank`
        :return: ``None`` if n/a
        """
        return self.stats.ranks

    @property
    def bgg_rank(self) -> int | None:
        """
        :return: The board game geek rank of this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.bgg_rank

    @property
    def boardgame_rank(self) -> int | None:
        warnings.warn("deprecated, use 'bgg_rank' instead", DeprecationWarning, stacklevel=2)
        return self.bgg_rank


class CollectionBoardGame(BaseGame):
    """
    A boardgame retrieved from the collection information, which has less information than the one retrieved
    via the /thing api and which also contains some user-specific information.
    """

    last_modified: str | None = Field(None, alias="lastmodified")
    numplays: int = 0
    rating: float | None = None
    owned: bool = Field(False, alias="own")
    preordered: bool = False
    prev_owned: bool = Field(False, alias="prevowned")
    want: bool = False
    want_to_buy: bool = Field(False, alias="wanttobuy")
    want_to_play: bool = Field(False, alias="wanttoplay")
    for_trade: bool = Field(False, alias="fortrade")
    wishlist: bool = False
    wishlist_priority: str | None = Field(None, alias="wishlistpriority")
    comment: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_status_bools(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["own", "preordered", "prevowned", "want", "wanttobuy", "wanttoplay", "fortrade", "wishlist"]:
            if field in data and data[field] is not None:
                try:
                    data[field] = bool(int(data[field]))
                except (ValueError, TypeError):
                    data[field] = False
        return data

    @property
    def lastmodified(self) -> str | None:
        warnings.warn("deprecated, use 'last_modified' instead", DeprecationWarning, stacklevel=2)
        return self.last_modified

    @property
    def version(self) -> BoardGameVersion | None:
        if self.versions:
            return self.versions[0]
        return None

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
        for v in self.versions:
            v._format(log)


class BoardGame(BaseGame):
    """
    Object containing information about a board game
    """

    alternative_names: list[str] = Field(default_factory=list)
    description: str = ""
    families: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    mechanics: list[str] = Field(default_factory=list)
    implementations: list[str] = Field(default_factory=list)
    designers: list[str] = Field(default_factory=list)
    artists: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    expansion: bool = False
    accessory: bool = False
    min_age: int | None = Field(None, alias="minage")
    expansions: list[Thing] = Field(default_factory=list)
    expands: list[Thing] = Field(default_factory=list)
    videos: list[BoardGameVideo] = Field(default_factory=list)
    comments: list[BoardGameComment] = Field(default_factory=list)
    player_suggestions: list[PlayerSuggestion] = Field(default_factory=list)

    _expansion_ids: set[int] = PrivateAttr(default_factory=set)
    _expands_ids: set[int] = PrivateAttr(default_factory=set)
    _video_ids: set[int] = PrivateAttr(default_factory=set)

    @model_validator(mode="before")
    @classmethod
    def _build_board_game(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # Convert suggested_players dict -> player_suggestions list
        suggested = data.get("suggested_players", {})
        if suggested and "results" in suggested:
            suggestions = []
            for count, result in suggested["results"].items():
                suggestions.append(
                    {
                        "player_count": count,
                        "best": result.get("best_rating", 0),
                        "recommended": result.get("recommended_rating", 0),
                        "not_recommended": result.get("not_recommended_rating", 0),
                    }
                )
            data.setdefault("player_suggestions", suggestions)
        # Deduplicate expansions/expands by id
        for field in ["expansions", "expands"]:
            seen: set[Any] = set()
            unique = []
            for item in data.get(field, []):
                item_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
                if item_id not in seen:
                    seen.add(item_id)
                    unique.append(item)
            data[field] = unique
        return data

    def model_post_init(self, __context: Any) -> None:
        self._expansion_ids = {exp.id for exp in self.expansions}
        self._expands_ids = {exp.id for exp in self.expands}
        self._video_ids = {vid.id for vid in self.videos}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id: {self.id})"

    def add_comment(self, data: dict[str, Any]) -> None:
        self.comments.append(BoardGameComment.model_validate(data))

    def add_expanded_game(self, data: dict[str, Any]) -> None:
        """
        Add a game expanded by this one

        :param dict data: expanded game's data
        :raises: :py:exc:`boardgamegeek.exceptions.BoardGameGeekError` if data is invalid
        """
        try:
            if data["id"] not in self._expands_ids:
                self._expands_ids.add(data["id"])
                self.expands.append(Thing.model_validate(data))
        except KeyError:
            raise BGGError("invalid expanded game data")

    def add_expansion(self, data: dict[str, Any]) -> None:
        """
        Add an expansion of this game

        :param dict data: expansion data
        :raises: :py:exc:`boardgamegeek.exceptions.BoardGameGeekError` if data is invalid
        """
        try:
            if data["id"] not in self._expansion_ids:
                self._expansion_ids.add(data["id"])
                self.expansions.append(Thing.model_validate(data))
        except KeyError:
            raise BGGError("invalid expansion data")

    @property
    def users_owned(self) -> int | None:
        """
        :return: number of users owning this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.users_owned

    @property
    def users_trading(self) -> int | None:
        """
        :return: number of users trading this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.users_trading

    @property
    def users_wanting(self) -> int | None:
        """
        :return: number of users wanting this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.users_wanting

    @property
    def users_wishing(self) -> int | None:
        """
        :return: number of users wishing for this game
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.users_wishing

    @property
    def users_commented(self) -> int | None:
        """
        :return: number of user comments
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.users_commented

    @property
    def rating_num_weights(self) -> int | None:
        """
        :return:
        :rtype: integer
        :return: ``None`` if n/a
        """
        return self.stats.rating_num_weights

    @property
    def rating_average_weight(self) -> float | None:
        """
        :return: average weight
        :rtype: float
        :return: ``None`` if n/a
        """
        return self.stats.rating_average_weight

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
