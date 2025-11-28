import logging
import xml.etree.ElementTree as ET

import pytest

from boardgamegeek import BGGClient, BGGClientLegacy, CacheBackendNone


@pytest.fixture
def xml() -> ET.Element:
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
def bgg() -> BGGClient:
    return BGGClient(access_token="token", cache=CacheBackendNone(), retries=2, retry_delay=1)


@pytest.fixture
def legacy_bgg() -> BGGClientLegacy:
    return BGGClientLegacy(access_token="token", cache=CacheBackendNone(), retries=2, retry_delay=1)


@pytest.fixture
def null_logger() -> logging.Logger:
    # create logger
    logger = logging.getLogger("null")
    logger.setLevel(logging.ERROR)
    return logger
