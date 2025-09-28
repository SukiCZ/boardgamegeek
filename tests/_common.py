import os
import urllib.parse

# TODO Clean up this file:
#  - Move constants to consts.py

# Kinda hard to test without having a "test" user
TEST_VALID_USER = "fagentu007"
TEST_VALID_USER_ID = 818216
TEST_USER_WITH_LOTS_OF_FRIENDS = "Solamar"  # user chosen randomly (..after a long search :)) ), just needed
# someone with lots of friends :D
TEST_INVALID_USER = "someOneThatHopefullyWontExistPlsGuysDontCreateThisUser"
TEST_INVALID_GAME_NAME = "blablablathisgamewonteverexist"
TEST_GAME_NAME = "Agricola"
TEST_GAME_ID = 31260

# TEST_GAME_NAME_2 = "Merchant of Venus (second edition)"
# TEST_GAME_ID_2 = 131646

TEST_GAME_NAME_2 = "Advanced Third Reich"
TEST_GAME_ID_2 = 283

TEST_GUILD_ID = 1229
TEST_GUILD_ID_2 = 930

TEST_GAME_WITH_IMPLEMENTATIONS_ID = 28720  # Brass

TEST_GAME_EXPANSION_ID = 223555  # Scythe: The Wind Gambit

TEST_GAME_ACCESSORY_ID = 104163  # Descent: Journeys in the Dark (second edition) – Conversion Kit

TEST_GEEKLIST_ID = 1
TEST_GEEKLIST_INVALID_ID = -1

STR_TYPES_OR_NONE = [str, type(None)]

# The top level directory for our XML files
XML_PATH = os.path.join(os.path.dirname(__file__), "xml")
STATUS_PATH = os.path.join(os.path.dirname(__file__), "status")


class MockResponse:
    """
    A simple object which contains all the fields we need from a response

    :param str text: the text to be returned with the response
    """

    def __init__(self, text, status_code=200):
        self.headers = {"content-type": "text/xml"}
        self.status_code = status_code
        self.text = text


def simulate_bgg(url, params, timeout, headers=None):
    *_, fragment = url.split("/")

    sorted_params = sorted(params.items(), key=lambda t: t[0])
    query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)

    filename = os.path.join(XML_PATH, fragment + "@" + query_string + ".xml")

    with open(filename, encoding="utf-8") as xmlfile:
        response_text = xmlfile.read()

    return MockResponse(response_text)


def simulate_legacy_bgg(url, params, timeout, headers=None):
    *_, fragment = url.split("/")
    sorted_params = sorted(params.items(), key=lambda t: t[0])
    # Response body
    query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
    if query_string:
        filename = os.path.join(XML_PATH, fragment + "@" + query_string + ".xml")
    else:
        filename = os.path.join(XML_PATH, fragment + ".xml")

    with open(filename, encoding="utf-8") as xmlfile:
        response_text = xmlfile.read()

    # Response status code
    filename = os.path.join(STATUS_PATH, fragment)
    if os.path.isfile(filename):
        with open(filename, encoding="utf-8") as statusfile:
            response_status = int(statusfile.read())
    else:
        response_status = 200

    return MockResponse(response_text, response_status)


def simulate_bgg_401(url, params, timeout, headers=None):
    return MockResponse(text="", status_code=401)
