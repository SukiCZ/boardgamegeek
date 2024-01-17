import logging

from ..exceptions import BGGItemNotFoundError
from ..objects.plays import GamePlays, UserPlays
from ..utils import xml_subelement_attr, xml_subelement_text

log = logging.getLogger("boardgamegeek.loaders.plays")


def create_plays_from_xml(xml_root, game_id=None):
    count = 0
    try:
        # in case of error, the root node doesn't have a 'total' attribute
        count = int(xml_root.attrib["total"])  # how many plays
    except (KeyError, ValueError):
        pass

    if not count:
        # TODO: test with something that has 0 plays.
        # count is zero when passed an invalid game id
        raise BGGItemNotFoundError("invalid user name or game id")

    if game_id is None:
        # User's plays
        return UserPlays(
            {
                "username": xml_root.attrib["username"],
                "user_id": int(xml_root.attrib["userid"]),
                "plays_count": count,
            }
        )
    else:
        return GamePlays({"game_id": game_id, "plays_count": count})


def add_plays_from_xml(plays, xml_root):
    added_items = False

    for play in xml_root.findall("play"):
        player_list = []
        for player in play.findall("players/player"):
            player_data = {
                "username": player.attrib.get("username"),
                "user_id": int(player.attrib.get("userid", -1)),
                "name": player.attrib.get("name"),
                "startposition": player.attrib.get("startposition"),
                "new": player.attrib.get("new"),
                "win": player.attrib.get("win"),
                "rating": player.attrib.get("rating"),
                "score": player.attrib.get("score"),
                "color": player.attrib.get("color"),
                "location": player.attrib.get("location"),
            }

            player_list.append(player_data)

        # TODO: add the game subtype too
        data = {
            "id": int(play.attrib["id"]),
            "date": play.attrib["date"],
            "quantity": int(play.attrib["quantity"]),
            "duration": int(play.attrib["length"]),
            "incomplete": int(play.attrib["incomplete"]),
            "nowinstats": int(play.attrib["nowinstats"]),
            # for User plays, will be overwritten with the user id when adding the play.
            "user_id": int(play.attrib.get("userid", -1)),
            "game_id": xml_subelement_attr(
                play, "item", attribute="objectid", convert=int
            ),
            "game_name": xml_subelement_attr(play, "item", attribute="name"),
            "comment": xml_subelement_text(play, "comments"),
            "players": player_list,
        }

        plays.add_play(data)
        added_items = True

    return added_items
