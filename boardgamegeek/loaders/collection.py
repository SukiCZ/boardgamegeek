from ..exceptions import BGGApiError, BGGItemNotFoundError
from ..objects.collection import Collection
from ..utils import (
    get_board_game_version_from_element,
    xml_subelement_attr,
    xml_subelement_text,
)


def create_collection_from_xml(xml_root, user_name):
    # check if there's an error (e.g. invalid username)
    error = xml_root.find(".//error")
    if error is not None:
        msg = xml_subelement_text(error, "message")
        # TODO: this is probably the invalid user error, but need to find out if there are any other error cases
        raise BGGItemNotFoundError(msg)

    return Collection({"owner": user_name})


def add_collection_items_from_xml(collection, xml_root, subtype):
    added_items = False

    for item in xml_root.findall(f"item[@subtype='{subtype}']"):
        # initial data for this collection item
        data = {
            "name": xml_subelement_text(item, "name"),
            "id": int(item.attrib["objectid"]),
            "image": xml_subelement_text(item, "image"),
            "thumbnail": xml_subelement_text(item, "thumbnail"),
            "yearpublished": xml_subelement_attr(
                item, "yearpublished", default=0, convert=int, quiet=True
            ),
            "numplays": xml_subelement_text(item, "numplays", convert=int, default=0),
            "comment": xml_subelement_text(item, "comment", default=""),
        }

        # Add item statistics
        stats = item.find("stats")
        if stats is None:
            raise BGGApiError("missing 'stats'")

        stat_data = {
            "usersrated": xml_subelement_attr(
                stats, "usersrated", convert=int, quiet=True
            ),
            "average": xml_subelement_attr(stats, "average", convert=float, quiet=True),
            "bayesaverage": xml_subelement_attr(
                stats, "bayesaverage", convert=float, quiet=True
            ),
            "stddev": xml_subelement_attr(stats, "stddev", convert=float, quiet=True),
            "median": xml_subelement_attr(stats, "median", convert=float, quiet=True),
            "ranks": [],
        }

        for rank in stats.findall("ranks/rank"):
            stat_data["ranks"].append(
                {
                    "type": rank.attrib.get("type"),
                    "id": rank.attrib["id"],
                    "name": rank.attrib["name"],
                    "friendlyname": rank.attrib["friendlyname"],
                    "value": rank.attrib.get("value"),
                    "bayesaverage": float(rank.attrib.get("bayesaverage", 0.0)),
                }
            )

        data.update(
            {
                "stats": stat_data,
                "minplayers": int(stats.attrib.get("minplayers", 0)),
                "maxplayers": int(stats.attrib.get("maxplayers", 0)),
                "minplaytime": int(stats.attrib.get("minplaytime", 0)),
                "maxplaytime": int(stats.attrib.get("maxplaytime", 0)),
                "playingtime": int(stats.attrib.get("playingtime", 0)),
                "rating": xml_subelement_attr(
                    stats, "rating", convert=float, quiet=True
                ),
            }
        )

        # status of the item in the collection
        status = item.find("status")
        if status is not None:
            data.update(
                {
                    stat: status.attrib.get(stat)
                    for stat in [
                        "lastmodified",
                        "own",
                        "preordered",
                        "prevowned",
                        "want",
                        "wanttobuy",
                        "wanttoplay",
                        "fortrade",
                        "wishlist",
                        "wishlistpriority",
                    ]
                }
            )

        # get the version, if any
        version = item.find("version")
        if version is not None:
            # This collection item has version information
            ver = version.find("item[@type='boardgameversion']")
            if ver is not None:
                try:
                    data["versions"] = [get_board_game_version_from_element(ver)]
                except KeyError:
                    raise BGGApiError("malformed XML element ('version')")

        collection.add_game(data)
        added_items = True

    return added_items
