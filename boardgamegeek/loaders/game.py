import logging

from ..exceptions import BGGApiError
from ..objects.games import BoardGame
from ..utils import (
    get_board_game_version_from_element,
    get_marketplace_listing_from_element,
    html_unescape,
    xml_subelement_attr,
    xml_subelement_attr_list,
    xml_subelement_text,
)

log = logging.getLogger("boardgamegeek.loaders.game")


def create_game_from_xml(xml_root, game_id):
    game_type = xml_root.attrib["type"]
    if game_type not in ["boardgame", "boardgameexpansion", "boardgameaccessory"]:
        log.debug(f"unsupported type {game_type} for item id {game_id}")
        raise BGGApiError("item has an unsupported type")

    data = {
        "id": game_id,
        "name": xml_subelement_attr(xml_root, "name[@type='primary']"),
        "alternative_names": xml_subelement_attr_list(
            xml_root, "name[@type='alternate']"
        ),
        "thumbnail": xml_subelement_text(xml_root, "thumbnail"),
        "image": xml_subelement_text(xml_root, "image"),
        "expansion": game_type == "boardgameexpansion",  # is this game an expansion?
        "accessory": game_type == "boardgameaccessory",  # is this game an accessory?
        "families": xml_subelement_attr_list(xml_root, "link[@type='boardgamefamily']"),
        "categories": xml_subelement_attr_list(
            xml_root, "link[@type='boardgamecategory']"
        ),
        "implementations": xml_subelement_attr_list(
            xml_root, "link[@type='boardgameimplementation']"
        ),
        "mechanics": xml_subelement_attr_list(
            xml_root, "link[@type='boardgamemechanic']"
        ),
        "designers": xml_subelement_attr_list(
            xml_root, "link[@type='boardgamedesigner']"
        ),
        "artists": xml_subelement_attr_list(xml_root, "link[@type='boardgameartist']"),
        "publishers": xml_subelement_attr_list(
            xml_root, "link[@type='boardgamepublisher']"
        ),
        "description": xml_subelement_text(
            xml_root, "description", convert=html_unescape, quiet=True
        ),
    }

    expands = []  # list of items this game expands
    expansions = []  # list of expansions this game has
    for e in xml_root.findall("link[@type='boardgameexpansion']"):
        try:
            item = {"id": e.attrib["id"], "name": e.attrib["value"]}
        except KeyError:
            raise BGGApiError("malformed XML element ('link type=boardgameexpansion')")

        if e.attrib.get("inbound", "false").lower()[0] == "t":
            # this is an item expanded by game_id
            expands.append(item)
        else:
            expansions.append(item)

    data["expansions"] = expansions
    data["expands"] = expands

    # These XML elements have a numberic value, attempt to convert them to integers
    for i in [
        "yearpublished",
        "minplayers",
        "maxplayers",
        "playingtime",
        "minplaytime",
        "maxplaytime",
        "minage",
    ]:
        data[i] = xml_subelement_attr(xml_root, i, convert=int, quiet=True)

    # Look for the videos
    # TODO: The BGG API doesn't take the page=NNN parameter into account for videos; when it does, paginate them too
    videos = xml_root.find("videos")
    if videos is not None:
        vid_list = []
        for vid in videos.findall("video"):
            try:
                vd = {
                    "id": vid.attrib["id"],
                    "name": vid.attrib["title"],
                    "category": vid.attrib.get("category"),
                    "language": vid.attrib.get("language"),
                    "link": vid.attrib["link"],
                    "uploader": vid.attrib.get("username"),
                    "uploader_id": vid.attrib.get("userid"),
                    "post_date": vid.attrib.get("postdate"),
                }
                vid_list.append(vd)
            except KeyError:
                raise BGGApiError("malformed XML element ('video')")

        data["videos"] = vid_list

    # look for the versions
    versions = xml_root.find("versions")
    if versions is not None:
        ver_list = []

        for version in versions.findall("item[@type='boardgameversion']"):
            try:
                vd = get_board_game_version_from_element(version)
                ver_list.append(vd)
            except KeyError:
                raise BGGApiError("malformed XML element ('versions')")

        data["versions"] = ver_list

    # look for marketplace
    marketplace = xml_root.find("marketplacelistings")
    if marketplace is not None:
        listings = []

        for listing in marketplace.findall("listing"):
            try:
                ld = get_marketplace_listing_from_element(listing)
                listings.append(ld)
            except KeyError:
                raise BGGApiError("malformed XML element ('marketplacelistings')")

        data["marketplace"] = listings

    # look for the statistics
    stats = xml_root.find("statistics/ratings")
    if stats is not None:
        sd = {
            "usersrated": xml_subelement_attr(
                stats, "usersrated", convert=int, quiet=True
            ),
            "average": xml_subelement_attr(stats, "average", convert=float, quiet=True),
            "bayesaverage": xml_subelement_attr(
                stats, "bayesaverage", convert=float, quiet=True
            ),
            "stddev": xml_subelement_attr(stats, "stddev", convert=float, quiet=True),
            "median": xml_subelement_attr(stats, "median", convert=float, quiet=True),
            "owned": xml_subelement_attr(stats, "owned", convert=int, quiet=True),
            "trading": xml_subelement_attr(stats, "trading", convert=int, quiet=True),
            "wanting": xml_subelement_attr(stats, "wanting", convert=int, quiet=True),
            "wishing": xml_subelement_attr(stats, "wishing", convert=int, quiet=True),
            "numcomments": xml_subelement_attr(
                stats, "numcomments", convert=int, quiet=True
            ),
            "numweights": xml_subelement_attr(
                stats, "numweights", convert=int, quiet=True
            ),
            "averageweight": xml_subelement_attr(
                stats, "averageweight", convert=float, quiet=True
            ),
            "ranks": [],
        }

        ranks = stats.findall("ranks/rank")
        for rank in ranks:
            try:
                rank_value = int(rank.attrib.get("value"))
            except (ValueError, TypeError):
                rank_value = None
            sd["ranks"].append(
                {
                    "id": rank.attrib["id"],
                    "name": rank.attrib["name"],
                    "friendlyname": rank.attrib.get("friendlyname"),
                    "value": rank_value,
                }
            )

        data["stats"] = sd
        data["suggested_players"] = {}

        suggested_players_poll = xml_root.find("poll[@name='suggested_numplayers']")
        if suggested_players_poll is not None:
            dsp = data["suggested_players"]
            dsp.update(
                {
                    "total_votes": int(
                        suggested_players_poll.attrib.get("totalvotes", 0)
                    ),
                    "results": {},
                }
            )

            for results in suggested_players_poll.findall("results"):
                player_count = results.attrib.get("numplayers")
                dspr = {
                    "best_rating": 0,
                    "recommended_rating": 0,
                    "not_recommended_rating": 0,
                }

                for result in results.findall("result"):
                    kind = result.attrib.get("value")
                    votes = int(result.attrib.get("numvotes", 0))
                    if kind == "Best":
                        dspr["best_rating"] = votes
                    elif kind == "Recommended":
                        dspr["recommended_rating"] = votes
                    elif kind == "Not Recommended":
                        dspr["not_recommended_rating"] = votes

                dsp["results"][player_count] = dspr

    return BoardGame(data)


def add_game_comments_from_xml(game, xml_root):
    added_items = False
    total_comments = 0

    comments = xml_root.find("comments")
    if comments is not None:
        total_comments = int(comments.attrib["totalitems"])

        for comm in xml_root.findall("comments/comment"):
            comment = {
                "username": comm.attrib["username"],
                "rating": comm.attrib.get("rating", "n/a").lower(),
                "comment": comm.attrib.get("value", "n/a"),
            }
            added_items = True
            game.add_comment(comment)

    return added_items, total_comments
