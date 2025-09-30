import datetime
from xml.etree import ElementTree as ET

from ..objects.geeklist import GeekList, GeekListItem
from ..utils import xml_subelement_text

GeekListOrItem = GeekList | GeekListItem


def parse_date(str_date: str) -> datetime.datetime:
    return datetime.datetime.strptime(str_date, "%a, %d %b %Y %H:%M:%S %z")


def add_geeklist_comments_from_xml(geeklist_or_item: GeekListOrItem, xml_root: ET.Element) -> bool:
    added_comments = False
    for comment in xml_root.findall("comment"):
        # initial data for this collection item
        data = {
            "username": comment.attrib["username"],
            "date": parse_date(comment.attrib["date"]) or None,
            "postdate": parse_date(comment.attrib["postdate"]) or None,
            "editdate": parse_date(comment.attrib["editdate"]) or None,
            "thumbs": int(comment.attrib["thumbs"]),
            "text": (comment.text or "").strip(),
        }
        geeklist_or_item.add_comment(data)
        added_comments = True
    return added_comments


def create_geeklist_from_xml(xml_root: ET.Element, listid: int) -> GeekList:
    data = {
        "id": listid,
        "name": xml_subelement_text(xml_root, "title"),  # need a name for a thing!
        "postdate": xml_subelement_text(xml_root, "postdate", parse_date, quiet=True),
        "editdate": xml_subelement_text(xml_root, "editdate", parse_date, quiet=True),
        "thumbs": xml_subelement_text(xml_root, "thumbs", int),
        "numitems": xml_subelement_text(xml_root, "numitems", int),
        "username": xml_subelement_text(xml_root, "username"),
        "description": xml_subelement_text(xml_root, "description"),
    }
    geeklist = GeekList(data)
    add_geeklist_comments_from_xml(geeklist, xml_root)
    return geeklist


def add_geeklist_items_from_xml(geeklist: GeekList, xml_root: ET.Element) -> bool:
    added_items = False
    for item in xml_root.findall("item"):
        # initial data for this geeklist item
        data = {
            "id": item.attrib["id"],
            "username": item.attrib["username"],
            "postdate": parse_date(item.attrib["postdate"]) or None,
            "editdate": parse_date(item.attrib["editdate"]) or None,
            "thumbs": int(item.attrib["thumbs"]),
            "body": xml_subelement_text(item, "body"),
        }
        listitem = geeklist.add_item(data)
        object_data = {
            "id": item.attrib["objectid"],
            "name": item.attrib["objectname"],
            "imageid": item.attrib["imageid"],
            "type": item.attrib["objecttype"],
            "subtype": item.attrib["subtype"],
        }
        listitem.set_object(object_data)
        add_geeklist_comments_from_xml(listitem, item)
        added_items = True
    return added_items
