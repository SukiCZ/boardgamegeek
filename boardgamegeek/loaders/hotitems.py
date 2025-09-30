from __future__ import annotations

from xml.etree import ElementTree as ET

from ..objects.hotitems import HotItems
from ..utils import xml_subelement_attr


def create_hot_items_from_xml(_xml_root: ET.Element) -> HotItems:
    return HotItems({})


def add_hot_items_from_xml(hot_items: HotItems, xml_root: ET.Element) -> bool:
    added_items = False

    for item in xml_root.findall("item"):
        kwargs = {
            "name": xml_subelement_attr(item, "name"),
            "id": int(item.attrib["id"]),
            "rank": int(item.attrib["rank"]),
            "yearpublished": xml_subelement_attr(item, "yearpublished", convert=int, quiet=True),
            "thumbnail": xml_subelement_attr(item, "thumbnail"),
        }

        hot_items.add_hot_item(kwargs)
        added_items = True

    return added_items
