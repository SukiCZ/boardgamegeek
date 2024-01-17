"""
:mod:`boardgamegeek.api` - Core functions
=========================================

This module contains the core functionality needed to retrieve data from boardgamegeek.com and parse it into usable
objects.

.. module:: boardgamegeek.api
   :platform: Unix, Windows
   :synopsis: module handling communication with the online BoardGameGeek API

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>
"""

import datetime
import logging

from .cache import CacheBackendMemory, CacheBackendNone
from .exceptions import BGGApiError, BGGError, BGGItemNotFoundError, BGGValueError
from .loaders import (
    add_collection_items_from_xml,
    add_game_comments_from_xml,
    add_guild_members_from_xml,
    add_hot_items_from_xml,
    add_plays_from_xml,
    create_collection_from_xml,
    create_game_from_xml,
    create_guild_from_xml,
    create_hot_items_from_xml,
    create_plays_from_xml,
)
from .objects.search import SearchResult
from .objects.user import User
from .utils import (
    DEFAULT_REQUESTS_PER_MINUTE,
    RateLimitingAdapter,
    request_and_parse_xml,
    xml_subelement_attr,
)

log = logging.getLogger("boardgamegeek.api")

HOT_ITEM_CHOICES = [
    "boardgame",
    "rpg",
    "videogame",
    "boardgameperson",
    "rpgperson",
    "boardgamecompany",
    "rpgcompany",
    "videogamecompany",
]

COLLECTION_SUBTYPES = [
    "boardgame",
    "boardgameexpansion",
    "boardgameaccessory",
    "rpgitem",
    "rpgissue",
    "videogame",
]


class BGGChoose:
    """
    Constants indicating how a game should be chosen when performing a search by name
    """

    FIRST = "first"
    RECENT = "recent"
    BEST_RANK = "best-rank"


class BGGRestrictSearchResultsTo:
    """
    Item types that should be included in search results
    """

    RPG = "rpgitem"
    VIDEO_GAME = "videogame"
    BOARD_GAME = "boardgame"
    BOARD_GAME_EXPANSION = "boardgameexpansion"


class BGGRestrictDomainTo:
    """
    Constants used in BoardGameGeek.user() calls, for specifying what hot/top items should be restricted to
    """

    BOARD_GAME = "boardgame"
    RPG = "rpg"
    VIDEO_GAME = "videogame"


class BGGRestrictPlaysTo:
    BOARD_GAME = "boardgame"
    BOARD_GAME_EXTENSION = "boardgameexpansion"
    BOARD_GAME_ACCESSORY = "boardgameaccessory"
    RPG = "rpgitem"
    VIDEO_GAME = "videogame"


class BGGRestrictCollectionTo:
    BOARD_GAME = "boardgame"
    BOARD_GAME_EXTENSION = "boardgameexpansion"
    BOARD_GAME_ACCESSORY = "boardgameaccessory"
    RPG = "rpgitem"
    RPG_ISSUE = "rpgissue"
    VIDEO_GAME = "videogame"


def call_progress_cb(progress_cb, current, total):
    """
    Calls the progress callback, if any
    """
    if progress_cb is not None:
        progress_cb(current, total)


class BGGCommon:
    """
    Base class for the BoardGameGeek websites APIs. All site-specific clients are derived from this.

    :param str api_endpoint: URL of the API
    :param :py:class:`boardgamegeek.cache.CacheBackend` cache: object to be used for caching BGG API results
    :param float timeout: timeout for a request, in seconds
    :param int retries: how many retries to perform in special cases
    :param float retry_delay: delay between retries, in seconds
    """

    def __init__(
        self, api_endpoint, cache, timeout, retries, retry_delay, requests_per_minute
    ):
        self._search_api_url = api_endpoint + "/search"
        self._thing_api_url = api_endpoint + "/thing"
        self._guild_api_url = api_endpoint + "/guild"
        self._user_api_url = api_endpoint + "/user"
        self._plays_api_url = api_endpoint + "/plays"
        self._hot_api_url = api_endpoint + "/hot"
        self._collection_api_url = api_endpoint + "/collection"
        try:
            self._timeout = float(timeout)
            self._retries = int(retries)
            self._retry_delay = float(retry_delay)
        except ValueError:
            raise BGGValueError

        if cache is None:
            cache = CacheBackendNone()
        self.requests_session = cache.cache

        # add the rate limiting adapter
        self.requests_session.mount(
            api_endpoint, RateLimitingAdapter(rpm=requests_per_minute)
        )

    def _get_game_id(self, name, game_type, choose, exact=True):
        """
        Returns the BGG ID of a game, searching by name

        :param str name: the name of the game to search for
        :param str game_type: searched game type (BGGItemType.RPG, BGGItemType.VIDEO_GAME, BGGItemType.BOARD_GAME,
                                                  BGGItemType.BOARD_GAME_EXPANSION)
        :param str choose: method of selecting the game by name, when having multiple results. Valid values are:
                           `BGGChoose.FIRST`, `BGGChoose.RECENT`, `BGGChoose.BEST_RANK`
        :param bool exact: limit results to items that match the `name` exactly
        :return: game's id
        :raises: `boardgamegeek.exceptions.BGGValueError` in case of invalid parameter(s)
        :raises: `boardgamegeek.exceptions.BGGItemNotFoundError` if the game hasn't been found
        :raises: `boardgamegeek.exceptions.BGGApiRetryError` if this request should be retried later
        :raises: `boardgamegeek.exceptions.BGGApiError` if the API response was invalid or couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """

        if choose not in [BGGChoose.FIRST, BGGChoose.RECENT, BGGChoose.BEST_RANK]:
            raise BGGValueError(f"invalid value for parameter 'choose': {choose}")

        log.debug(f"getting game id for '{name}'")
        res = self.search(name, search_type=[game_type], exact=exact)

        if not res:
            raise BGGItemNotFoundError(f"can't find '{name}'")

        if choose == BGGChoose.FIRST:
            return res[0].id
        elif choose == BGGChoose.RECENT:
            # choose the result with the biggest year
            return max(res, key=lambda x: x.year if x.year is not None else -300000).id
        else:
            # getting the best rank requires fetching the data of all games returned
            game_data = [self.game(game_id=r.id) for r in res]
            # ...and selecting the one with the best ranking
            return min(
                game_data,
                key=lambda x: x.boardgame_rank
                if x.boardgame_rank is not None
                else 10000000000,
            ).id

    def guild(self, guild_id, progress=None, members=True):
        """
        Retrieves details about a guild

        :param integer guild_id: the id number of the guild
        :param callable progress: optional callable for progress, takes two integers (``current``, ``total``)
        :param bool members: if ``True``, names of the guild members will be fetched
        :return: ``Guild`` object containing the data
        :return: ``None`` if the information couldn't be retrieved
        :rtype: :py:class:`boardgamegeek.guild.Guild`
        :raises: `BGGValueError` in case of an invalid parameter(s)
        :raises: `boardgamegeek.exceptions.BGGApiRetryError` if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """

        try:
            guild_id = int(guild_id)
        except (ValueError, TypeError):
            raise BGGValueError("invalid guild id")

        xml_root = request_and_parse_xml(
            self.requests_session,
            self._guild_api_url,
            params={"id": guild_id, "members": int(members)},
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        guild = create_guild_from_xml(xml_root)

        if not members:
            return guild

        # Add the first page of members
        added_member = add_guild_members_from_xml(guild, xml_root)

        try:
            call_progress_cb(progress, len(guild), guild.members_count)
        except Exception:
            # TODO Too broad
            return guild

        # Fetch the other pages of members
        page = 1
        while len(guild) < guild.members_count and added_member:
            page += 1
            log.debug(f"fetching guild members page {page}")

            xml_root = request_and_parse_xml(
                self.requests_session,
                self._guild_api_url,
                params={"id": guild_id, "members": 1, "page": page},
                timeout=self._timeout,
                retries=self._retries,
                retry_delay=self._retry_delay,
            )

            added_member = add_guild_members_from_xml(guild, xml_root)

            try:
                call_progress_cb(progress, len(guild), guild.members_count)
            except Exception:
                # TODO Too broad
                break

        return guild

    # TODO: refactor
    def user(
        self,
        name,
        progress=None,
        buddies=True,
        guilds=True,
        hot=True,
        top=True,
        domain=BGGRestrictDomainTo.BOARD_GAME,
    ):
        """
        Retrieves details about an user

        :param str name: user's login name
        :param callable progress: an optional callable for reporting progress when fetching the buddy list/guilds,
                                  taking two integers (``current``, ``total``) as arguments
        :param bool buddies: if ``True``, get the user's buddies
        :param bool guilds: if ``True``, get the user's guilds
        :param bool hot: if ``True``, get the user's "hot" list
        :param bool top: if ``True``, get the user's "top" list
        :param str domain:
            restrict items on the "hot" and "top" lists to ``domain``.
            One of the constants in :py:class:`boardgamegeek.BGGSelectDomain`
        :return: ``User`` object
        :rtype: :py:class:`boardgamegeek.user.User`
        :return: ``None`` if the user couldn't be found

        :raises: `ValueError` in case of invalid parameters
        :raises: `boardgamegeek.exceptions.BGGValueError` in case of invalid parameter(s)
        :raises: `boardgamegeek.exceptions.BGGItemNotFoundError` if the user wasn't found
        :raises: `boardgamegeek.exceptions.BGGApiRetryError` if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """

        if not name:
            raise BGGValueError("no user name specified")

        if domain not in [
            BGGRestrictDomainTo.BOARD_GAME,
            BGGRestrictDomainTo.RPG,
            BGGRestrictDomainTo.VIDEO_GAME,
        ]:
            raise BGGValueError("invalid domain")

        params = {
            "name": name,
            "buddies": int(buddies),
            "guilds": int(guilds),
            "hot": int(hot),
            "top": int(top),
            "domain": domain,
        }

        root = request_and_parse_xml(
            self.requests_session,
            self._user_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        # when the user is not found, the API returns an response, but with most fields empty. id is empty too
        try:
            data = {"name": root.attrib["name"], "id": int(root.attrib["id"])}
        except (KeyError, ValueError):
            raise BGGItemNotFoundError

        for i in [
            "firstname",
            "lastname",
            "avatarlink",
            "stateorprovince",
            "country",
            "webaddress",
            "xboxaccount",
            "wiiaccount",
            "steamaccount",
            "psnaccount",
            "traderating",
        ]:
            data[i] = xml_subelement_attr(root, i)

        data["yearregistered"] = xml_subelement_attr(
            root, "yearregistered", convert=int, quiet=True
        )
        data["lastlogin"] = xml_subelement_attr(
            root,
            "lastlogin",
            convert=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"),
            quiet=True,
        )

        # TODO: move add_top_item add_hot_item to sepparated files
        user = User(data)

        # add top items
        if top:
            for top_item in root.findall(".//top/item"):
                user.add_top_item(
                    {"id": int(top_item.attrib["id"]), "name": top_item.attrib["name"]}
                )

        # add hot items
        if hot:
            for hot_item in root.findall(".//hot/item"):
                user.add_hot_item(
                    {"id": int(hot_item.attrib["id"]), "name": hot_item.attrib["name"]}
                )

        if not buddies and not guilds:
            return user

        total_buddies = 0
        total_guilds = 0

        buddies = root.find("buddies")
        if buddies is not None:
            total_buddies = int(buddies.attrib["total"])
            if total_buddies > 0:
                # add the buddies from the first page
                for buddy in buddies.findall(".//buddy"):
                    user.add_buddy(
                        {"name": buddy.attrib["name"], "id": buddy.attrib["id"]}
                    )

        guilds = root.find("guilds")
        if guilds is not None:
            total_guilds = int(guilds.attrib["total"])
            if total_guilds > 0:
                # add the guilds from the first page
                for guild in guilds.findall(".//guild"):
                    user.add_guild(
                        {"name": guild.attrib["name"], "id": guild.attrib["id"]}
                    )

        # It seems that the BGG API can return more results than what's specified in the documentation (they say
        # page size is 100, but for an user with 114 friends, all buddies are there on the first page).
        # Therefore, we'll keep fetching pages until we reach the number of items we're expecting or we don't get
        # any more data

        max_items_to_fetch = max(total_buddies, total_guilds)

        try:
            call_progress_cb(
                progress, max(user.total_buddies, user.total_guilds), max_items_to_fetch
            )
        except Exception:
            # TODO Too broad
            return user

        page = 2
        while max(user.total_buddies, user.total_guilds) < max_items_to_fetch:
            added_buddy = False
            added_guild = False
            params["page"] = page
            root = request_and_parse_xml(
                self.requests_session,
                self._user_api_url,
                params=params,
                timeout=self._timeout,
            )

            for buddy in root.findall(".//buddy"):
                user.add_buddy({"name": buddy.attrib["name"], "id": buddy.attrib["id"]})
                added_buddy = True

            for guild in root.findall(".//guild"):
                user.add_guild({"name": guild.attrib["name"], "id": guild.attrib["id"]})
                added_guild = True

            try:
                call_progress_cb(
                    progress,
                    max(user.total_buddies, user.total_guilds),
                    max_items_to_fetch,
                )
            except Exception:
                # TODO Too broad
                break

            page += 1

            if not added_buddy and not added_guild:
                log.debug(
                    f"didn't add any buddy/guild after fetching page {page}, stopping here"
                )
                break

        return user

    def plays(
        self,
        name=None,
        game_id=None,
        progress=None,
        min_date=None,
        max_date=None,
        subtype=BGGRestrictPlaysTo.BOARD_GAME,
    ):
        """
        Retrieves the plays for an user (if using ``name``) or for a game (if using ``game_id``)

        :param str name: user name to retrieve the plays for
        :param integer game_id: game id to retrieve the plays for
        :param callable progress: an optional callable for reporting progress, taking two integers (``current``,
                                  ``total``) as arguments
        :param datetime.date min_date: return only plays of the specified date or later
        :param datetime.date max_date: return only plays of the specified date or earlier
        :param str subtype: limit plays results to the specified subtype.
        :return: object containing all the plays
        :rtype: :py:class:`boardgamegeek.plays.Plays`
        :return: ``None`` if the user/game couldn't be found
        :raises: `boardgamegeek.exceptions.BGGValueError` in case of invalid parameter(s)
        :raises: BGGApiRetryError if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout

        """
        if not name and not game_id:
            raise BGGValueError("no user name specified")

        if name and game_id:
            raise BGGValueError("can't retrieve by user and by game at the same time")

        if subtype not in [
            "boardgame",
            "boardgameexpansion",
            "boardgameaccessory",
            "rpgitem",
            "videogame",
        ]:
            raise BGGValueError("invalid subtype")

        params = {"subtype": subtype}

        if name:
            params["username"] = name
            game_id = None
        else:
            try:
                params["id"] = int(game_id)
            except ValueError:
                raise BGGValueError("invalid game id")

        if min_date:
            try:
                params["mindate"] = min_date.isoformat()
            except AttributeError:
                raise BGGValueError("mindate must be a datetime.date object")

        if max_date:
            try:
                params["maxdate"] = max_date.isoformat()
            except AttributeError:
                raise BGGValueError("maxdate must be a datetime.date object")

        xml_root = request_and_parse_xml(
            self.requests_session,
            self._plays_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        plays = create_plays_from_xml(xml_root, game_id)
        added_plays = add_plays_from_xml(plays, xml_root)

        try:
            call_progress_cb(progress, len(plays), plays.plays_count)
        except Exception:
            # TODO Too broad
            return plays

        page = 1

        # Since the BGG API doesn't seem to report the total number of plays for games correctly (it's 0), just
        # continue until we can't add anymore
        while added_plays:
            page += 1
            log.debug(f"fetching page {page} of plays")

            params["page"] = page

            # fetch the next pages of plays
            xml_root = request_and_parse_xml(
                self.requests_session,
                self._plays_api_url,
                params=params,
                timeout=self._timeout,
                retries=self._retries,
                retry_delay=self._retry_delay,
            )

            added_plays = add_plays_from_xml(plays, xml_root)

            try:
                call_progress_cb(progress, len(plays), plays.plays_count)
            except Exception:
                # TODO Too broad
                break

        return plays

    def hot_items(self, item_type):
        """
        Return the list of "Hot Items"

        :param str item_type: hot item type. Valid values: "boardgame", "rpg", "videogame", "boardgameperson",
                              "rpgperson", "boardgamecompany", "rpgcompany", "videogamecompany")
        :return: ``HotItems`` object
        :rtype: :py:class:`boardgamegeek.hotitems.HotItems`
        :return: ``None`` in case the hot items couldn't be retrieved

        :raises: `boardgamegeek.exceptions.BGGValueError` in case of invalid parameter(s)
        :raises: `boardgamegeek.exceptions.BGGApiRetryError` if this request should be retried after
                  a short delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """
        if item_type not in HOT_ITEM_CHOICES:
            raise BGGValueError("invalid type specified")

        params = {"type": item_type}

        xml_root = request_and_parse_xml(
            self.requests_session,
            self._hot_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        hot_items = create_hot_items_from_xml(xml_root)
        add_hot_items_from_xml(hot_items, xml_root)

        return hot_items

    def collection(
        self,
        user_name,
        subtype=BGGRestrictCollectionTo.BOARD_GAME,
        exclude_subtype=None,
        ids=None,
        versions=None,
        version=None,
        own=None,
        rated=None,
        played=None,
        commented=None,
        trade=None,
        want=None,
        wishlist=None,
        wishlist_prio=None,
        preordered=None,
        want_to_play=None,
        want_to_buy=None,
        prev_owned=None,
        has_parts=None,
        want_parts=None,
        min_rating=None,
        rating=None,
        min_bgg_rating=None,
        bgg_rating=None,
        min_plays=None,
        max_plays=None,
        collection_id=None,
        modified_since=None,
    ):
        """
        Returns an user's game collection

        :param str user_name: user name to retrieve the collection for
        :param str subtype:
            what type of items to return.
            One of the constants in :py:class:`boardgamegeek.api.BGGRestrictCollectionTo`
        :param str exclude_subtype:
            if not ``None`` (default), exclude the specified subtype.
            Else, one of the constants in :py:class:`boardgamegeek.api.BGGRestrictCollectionTo`
        :param list ids: if not ``None`` (default), limit the results to the specified ids.
        :param bool versions: *DEPRECATED* use `version` instead
        :param bool version: include item version information
        :param bool own: include (if ``True``) or exclude (if ``False``) owned items
        :param bool rated: include (if ``True``) or exclude (if ``False``) rated items
        :param bool played: include (if ``True``) or exclude (if ``False``) played items
        :param bool commented: include (if ``True``) or exclude (if ``False``) items commented on
        :param bool trade: include (if ``True``) or exclude (if ``False``) items for trade
        :param bool want: include (if ``True``) or exclude (if ``False``) items wanted in trade
        :param bool wishlist: include (if ``True``) or exclude (if ``False``) items in the wishlist
        :param int wishlist_prio: return only the items with the specified wishlist priority (valid values: 1 to 5)
        :param bool preordered: include (if ``True``) or exclude (if ``False``) preordered items
        :param bool want_to_play: include (if ``True``) or exclude (if ``False``) items wanting to play
        :param bool want_to_buy: include (if ``True``) or exclude (if ``False``) items wanting to buy
        :param bool prev_owned: include (if ``True``) or exclude (if ``False``) previously owned items
        :param bool has_parts: include (if ``True``) or exclude (if ``False``) items for which there is a comment in the
                               "Has parts" field
        :param bool want_parts: include (if ``True``) or exclude (if ``False``) items for which there is a comment in
                                the "Want parts" field
        :param double min_rating: return items rated by the user with a minimum of ``min_rating``
        :param double rating: return items rated by the user with a maximum of ``rating``
        :param double min_bgg_rating : return items rated on BGG with a minimum of ``min_bgg_rating``
        :param double bgg_rating: return items rated on BGG with a maximum of ``bgg_rating``
        :param int collection_id: restrict results to the collection specified by this id
        :param str modified_since:
            restrict results to those whose status (own, want, etc.) has been changed/added since ``modified_since``.
            Format: ``YY-MM-DD`` or ``YY-MM-DD HH:MM:SS``


        :return: ``Collection`` object
        :rtype: :py:class:`boardgamegeek.collection.Collection`
        :return: ``None`` if user not found

        :raises: `boardgamegeek.exceptions.BGGValueError` in case of invalid parameter(s)
        :raises: BGGApiRetryError if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """

        # Parameter validation

        if not user_name:
            raise BGGValueError("no user name specified")

        if subtype not in COLLECTION_SUBTYPES:
            raise BGGValueError("invalid 'subtype'")

        params = {"username": user_name, "subtype": subtype, "stats": 1}

        if exclude_subtype is not None:
            if exclude_subtype not in COLLECTION_SUBTYPES:
                raise BGGValueError("invalid 'exclude_subtype'")

            if subtype == exclude_subtype:
                raise BGGValueError("incompatible 'subtype' and 'exclude_subtype'")

            params["excludesubtype"] = exclude_subtype

        if ids is not None:
            params["id"] = ",".join([f"{id_}" for id_ in ids])

        for param in [
            "versions",
            "version",
            "own",
            "rated",
            "played",
            "trade",
            "want",
            "wishlist",
            "preordered",
        ]:
            p = locals()[param]
            if p is not None:
                if param == "versions":
                    param = "version"
                params[param] = int(p)

        if commented is not None:
            params["comment"] = int(commented)

        if wishlist_prio is not None:
            if 1 <= wishlist_prio <= 5:
                params["wishlishpriority"] = wishlist_prio
            else:
                raise BGGValueError("invalid 'wishlist_prio'")

        if want_to_play is not None:
            params["wanttoplay"] = int(want_to_play)

        if want_to_buy is not None:
            params["wanttobuy"] = int(want_to_buy)

        if prev_owned is not None:
            params["prevowned"] = int(prev_owned)

        if has_parts is not None:
            params["hasparts"] = int(has_parts)

        if want_parts is not None:
            params["wantparts"] = int(want_parts)

        if min_rating is not None:
            if 1.0 <= min_rating <= 10.0:
                params["minrating"] = min_rating
            else:
                raise BGGValueError("invalid 'min_rating'")

        if rating is not None:
            if 1.0 <= rating <= 10.0:
                params["rating"] = rating
            else:
                raise BGGValueError("invalid 'rating'")

        if min_bgg_rating is not None:
            if 1.0 <= min_bgg_rating <= 10.0:
                params["minbggrating"] = min_bgg_rating
            else:
                raise BGGValueError("invalid 'bgg_min_rating'")

        if bgg_rating is not None:
            if 1.0 <= bgg_rating <= 10.0:
                params["bggrating"] = bgg_rating
            else:
                raise BGGValueError("invalid 'bgg_rating'")

        if collection_id is not None:
            params["collid"] = collection_id

        if modified_since is not None:
            params["modifiedsince"] = modified_since

        xml_root = request_and_parse_xml(
            self.requests_session,
            self._collection_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        collection = create_collection_from_xml(xml_root, user_name)
        add_collection_items_from_xml(collection, xml_root, subtype)

        return collection

    def search(self, query, search_type=None, exact=False):
        """
        Search for a game

        :param str query: the string to search for
        :param list search_type:
            list of :py:class:`boardgamegeek.api.BGGRestrictItemTypeTo`,
            indicating what to include in the search results.
        :param bool exact: if True, try to match the name exactly
        :return: list of ``SearchResult``
        :rtype: list of :py:class:`boardgamegeek.search.SearchResult`

        :raises: `boardgamegeek.exceptions.BGGValueError` in case of invalid parameter(s)
        :raises: BGGApiRetryError if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the API response was invalid or couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """
        if not query:
            raise BGGValueError("invalid query string")

        if search_type is None:
            search_type = [BGGRestrictSearchResultsTo.BOARD_GAME]

        params = {"query": query}

        for s in search_type:
            if s not in [
                BGGRestrictSearchResultsTo.RPG,
                BGGRestrictSearchResultsTo.VIDEO_GAME,
                BGGRestrictSearchResultsTo.BOARD_GAME,
                BGGRestrictSearchResultsTo.BOARD_GAME_EXPANSION,
            ]:
                raise BGGValueError(f"invalid search type: {search_type}")

        params["type"] = ",".join(search_type)

        if exact:
            params["exact"] = 1

        root = request_and_parse_xml(
            self.requests_session,
            self._search_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        results = []
        for item in root.findall("item"):
            kwargs = {
                "id": item.attrib["id"],
                "name": xml_subelement_attr(item, "name"),
                "yearpublished": xml_subelement_attr(
                    item, "yearpublished", default=0, convert=int, quiet=True
                ),
                "type": item.attrib["type"],
            }

            results.append(SearchResult(kwargs))

        return results


class BGGClient(BGGCommon):
    """
    Python client for www.boardgamegeek.com's XML API 2.

    Caching for the requests can be used by specifying an URI for the ``cache`` parameter. By default, an in-memory
    cache is used, with sqlite being the other currently supported option.

    :param :py:class:`boardgamegeek.cache.CacheBackend` cache: An object to be used for caching the requests
    :param float timeout: Timeout for network operations, in seconds
    :param int retries: Number of retries to perform in case the API returns HTTP 202 (retry) or in case of timeouts
    :param float retry_delay: Time to sleep, in seconds, between retries when the API returns HTTP 202 (retry)
    :param disable_ssl: ignored, left for backwards compatibility
    :param requests_per_minute: how many requests per minute to allow to go out to BGG (throttle prevention)

    Example usage::

        >>> bgg = BGGClient()
        >>> game = bgg.game("Android: Netrunner")
        >>> game.id
        124742
        >>> bgg_no_cache = BGGClient(cache=CacheBackendNone())
        >>> bgg_sqlite_cache = BGGClient(cache=CacheBackendSqlite(path="/path/to/cache.db", ttl=3600))

    """

    def __init__(
        self,
        cache=CacheBackendMemory(ttl=3600),
        timeout=15,
        retries=3,
        retry_delay=5,
        disable_ssl=False,
        requests_per_minute=DEFAULT_REQUESTS_PER_MINUTE,
    ):
        super().__init__(
            api_endpoint="https://boardgamegeek.com/xmlapi2",
            cache=cache,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
            requests_per_minute=requests_per_minute,
        )

    def get_game_id(self, name, choose=BGGChoose.FIRST, exact=True):
        """
        Returns the BGG ID of a game, searching by name

        :param str name: The name of the game to search for
        :param boardgamegeek.BGGChoose choose: method of selecting the game by name, when dealing with multiple results.
        :param bool exact: limit results to items that match the `name` exactly
        :return: the game's id
        :rtype: integer
        :return: ``None`` if game wasn't found
        :raises: `boardgamegeek.exceptions.BGGError` in case of invalid name
        :raises: BGGApiRetryError if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BGGApiError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BGGApiTimeoutError` if there was a timeout
        """
        return self._get_game_id(
            name,
            game_type=BGGRestrictSearchResultsTo.BOARD_GAME,
            choose=choose,
            exact=exact,
        )

    def game_list(
        self,
        game_id_list,
        versions=False,
        videos=False,
        historical=False,
        marketplace=False,
    ):
        """
        Get list of games by from a list of ids.

        :param list game_id_list:  List of game ids
        :param bool versions: include versions information
        :param bool videos: include videos
        :param bool historical: include historical data
        :param bool marketplace: include marketplace data
        :return: list of ``BoardGame`` objects
        :rtype: list`

        :raises: `boardgamegeek.exceptions.BoardGameGeekAPIRetryError`
            if this request should be retried after a short delay
        :raises: `boardgamegeek.exceptions.BoardGameGeekAPIError`
            if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BoardGameGeekTimeoutError`
            if there was a timeout
        """

        if not game_id_list:
            raise BGGError("List of Game Ids must be specified")

        log.debug(f"retrieving games {game_id_list}")

        params = {
            "id": ",".join([str(game_id) for game_id in game_id_list]),
            "versions": int(versions),
            "videos": int(videos),
            "historical": int(historical),
            "marketplace": int(marketplace),
            "stats": 1,
        }

        xml_root = request_and_parse_xml(
            self.requests_session,
            self._thing_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        xml_root = xml_root.findall("item")
        if xml_root is None:
            msg = f"invalid data for game ids: {game_id_list}"
            raise BGGApiError(msg)

        game_list = []
        for i, game_root in enumerate(xml_root):
            game = create_game_from_xml(game_root, game_id=game_id_list[i])
            game_list.append(game)

        return game_list

    def game(
        self,
        name=None,
        game_id=None,
        choose=BGGChoose.FIRST,
        versions=False,
        videos=False,
        historical=False,
        marketplace=False,
        comments=False,
        rating_comments=False,
        progress=None,
        exact=True,
    ):
        """
        Get information about a game.

        :param str name: If not None, get information about a game with this name
        :param integer game_id:  If not None, get information about a game with this id
        :param str choose: method of selecting the game by name, when dealing with multiple results.
                           Valid values are : "first", "recent" or "best-rank"
        :param bool versions: include versions information
        :param bool videos: include videos
        :param bool historical: include historical data
        :param bool marketplace: include marketplace data
        :param bool comments: include comments
        :param bool rating_comments: include comments with rating (ignored in favor of ``comments``, if that is true)
        :param callable progress: callable for reporting progress if fetching comments
        :param bool exact: limit results to items that match the `name` exactly
        :return: ``BoardGame`` object
        :rtype: :py:class:`boardgamegeek.games.BoardGame`

        :raises: `boardgamegeek.exceptions.BoardGameGeekError` in case of invalid name or game_id
        :raises: `boardgamegeek.exceptions.BoardGameGeekAPIRetryError` if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BoardGameGeekAPIError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BoardGameGeekTimeoutError` if there was a timeout
        """

        if not name and game_id is None:
            raise BGGError("game name or id not specified")

        if game_id is None:
            game_id = self.get_game_id(name, choose=choose, exact=exact)
            if game_id is None:
                raise BGGItemNotFoundError

        log.debug(
            "retrieving game id {}{}".format(
                game_id, f" ({name})" if name is not None else ""
            )
        )

        params = {
            "id": game_id,
            "versions": int(versions),
            "videos": int(videos),
            "historical": int(historical),
            "marketplace": int(marketplace),
            "comments": int(comments),
            "ratingcomments": int(rating_comments),
            "pagesize": 100,
            "page": 1,
            "stats": 1,
        }

        xml_root = request_and_parse_xml(
            self.requests_session,
            self._thing_api_url,
            params=params,
            timeout=self._timeout,
            retries=self._retries,
            retry_delay=self._retry_delay,
        )

        xml_root = xml_root.find("item")
        if xml_root is None:
            msg = "invalid data for game id: {}{}".format(
                game_id, "" if name is None else f" ({name})"
            )
            raise BGGApiError(msg)

        game = create_game_from_xml(xml_root, game_id=game_id)

        if not (comments or rating_comments):
            return game

        added_items, total = add_game_comments_from_xml(game, xml_root)

        try:
            call_progress_cb(progress, len(game.comments), total)
        except Exception:
            # TODO Too broad
            return game

        page = 1
        while added_items and len(game.comments) < total:
            page += 1

            params["page"] = page
            xml_root = request_and_parse_xml(
                self.requests_session,
                self._thing_api_url,
                params={
                    "id": game_id,
                    "pagesize": 100,
                    "comments": int(comments),
                    "ratingcomments": int(rating_comments),
                    "page": page,
                },
                timeout=self._timeout,
                retries=self._retries,
                retry_delay=self._retry_delay,
            )

            xml_root = xml_root.find("item")
            if xml_root is None:
                msg = "invalid data for game id: {}{}".format(
                    game_id, "" if name is None else f" ({name})"
                )
                raise BGGApiError(msg)

            added_items, total = add_game_comments_from_xml(game, xml_root)

            try:
                call_progress_cb(progress, len(game.comments), total)
            except Exception:
                # TODO Too broad
                break

        return game

    def games(self, name):
        """
        Return a list containing all games with the given name

        :param str name: the name of the game to search for
        :return: list of :py:class:`boardgamegeek.games.BoardGame`
        :raises: `boardgamegeek.exceptions.BoardGameGeekAPIRetryError` if request should be retried after delay
        :raises: `boardgamegeek.exceptions.BoardGameGeekAPIError` if the response couldn't be parsed
        :raises: `boardgamegeek.exceptions.BoardGameGeekTimeoutError` if there was a timeout
        """
        return [
            self.game(game_id=s.id)
            for s in self.search(
                name,
                search_type=[
                    BGGRestrictSearchResultsTo.BOARD_GAME,
                    BGGRestrictSearchResultsTo.BOARD_GAME_EXPANSION,
                ],
                exact=True,
            )
        ]
