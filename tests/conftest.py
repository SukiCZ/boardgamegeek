import logging
import xml.etree.ElementTree as ET

import pytest

from boardgamegeek import BGGClient, BGGClientLegacy, CacheBackendNone

pytest.mark.serialize = pytest.mark.markers


@pytest.fixture
def xml():
    xml_code = """
    <root>
        <node1 attr="hello1" int_attr="1">text</node1>
        <node2 attr="hello2" int_attr="2" />
        <list>
            <li attr="elem1" int_attr="1" />
            <li attr="elem2" int_attr="2" />
            <li attr="elem3" int_attr="3" />
            <li attr="elem4" int_attr="4" />
        </list>
    </root>
    """
    return ET.fromstring(xml_code)


@pytest.fixture
def bgg():
    return BGGClient(cache=CacheBackendNone(), retries=2, retry_delay=1)


@pytest.fixture
def legacy_bgg():
    return BGGClientLegacy(cache=CacheBackendNone(), retries=2, retry_delay=1)


@pytest.fixture
def null_logger():
    # create logger
    logger = logging.getLogger("null")
    logger.setLevel(logging.ERROR)
    return logger
