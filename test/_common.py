# coding: utf-8

import logging
import os
import io
import pytest
import sys
import xml.etree.ElementTree as ET


from boardgamegeek import BGGClient, CacheBackendNone


# Kinda hard to test without having a "test" user
TEST_VALID_USER = "fagentu007"
TEST_VALID_USER_ID = 818216
TEST_USER_WITH_LOTS_OF_FRIENDS = "Solamar"        # user chosen randomly (..after a long search :)) ), just needed
                                                  # someone with lots of friends :D
TEST_INVALID_USER = "someOneThatHopefullyWontExistPlsGuysDontCreateThisUser"
TEST_INVALID_GAME_NAME = "blablablathisgamewonteverexist"
TEST_GAME_NAME = "Agricola"
TEST_GAME_ID = 31260

#TEST_GAME_NAME_2 = "Merchant of Venus (second edition)"
#TEST_GAME_ID_2 = 131646

TEST_GAME_NAME_2 = "Advanced Third Reich"
TEST_GAME_ID_2 = 283

TEST_GUILD_ID = 1229
TEST_GUILD_ID_2 = 930

TEST_GAME_ACCESSORY_ID = 104163 # Descent: Journeys in the Dark (second edition) – Conversion Kit

STR_TYPES_OR_NONE = [str, type(None)]

# The top level directory for our XML files
XML_PATH = os.path.join(os.path.dirname(__file__), "xml")

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
def null_logger():
    # create logger
    logger = logging.getLogger("null")
    logger.setLevel(logging.ERROR)
    return logger


class MockResponse:
    """
    A simple object which contains all the fields we need from a response

    :param str text: the text to be returned with the response
    """
    def __init__(self, text):
        self.headers = {"content-type": "text/xml"}
        self.status_code = 200
        self.text = text


def simulate_bgg(url, params, timeout):
    last_slash = url.rindex('/')
    fragment = url[last_slash + 1:]

    sorted_params = sorted(params.items(), key=lambda t: t[0])
    query_string = '&'.join([str(k) + "=" + str(v) for k, v in sorted_params])

    filename = os.path.join(XML_PATH, fragment + "?" + query_string)

    with io.open(filename, "r", encoding="utf-8") as xmlfile:
        response_text = xmlfile.read()

    return MockResponse(response_text)
