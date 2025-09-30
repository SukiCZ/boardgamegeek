import urllib.parse
from pathlib import Path
from typing import Any

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
BASE_DIR = Path(__file__).resolve().parent  # 'tests' directory
XML_PATH = BASE_DIR / "xml"
STATUS_PATH = BASE_DIR / "status"


class MockResponse:
    """
    A simple object which contains all the fields we need from a response

    :param str text: the text to be returned with the response
    """

    def __init__(self, text: str, status_code: int = 200):
        self.headers = {"content-type": "text/xml"}
        self.status_code = status_code
        self.text = text


def simulate_bgg(url: str, params: dict[str, Any], timeout: int, headers: dict[str, Any]) -> MockResponse:
    *_, fragment = url.split("/")

    sorted_params = sorted(params.items(), key=lambda t: t[0])
    query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)

    filename = XML_PATH / f"{fragment}@{query_string}.xml"

    response_text = filename.read_text()

    return MockResponse(response_text)


def simulate_legacy_bgg(url: str, params: dict[str, Any], timeout: int, headers: dict[str, Any]) -> MockResponse:
    *_, fragment = url.split("/")
    sorted_params = sorted(params.items(), key=lambda t: t[0])
    # Response body
    query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
    if query_string:
        filename = XML_PATH / f"{fragment}@{query_string}.xml"
    else:
        filename = XML_PATH / f"{fragment}.xml"

    response_text = filename.read_text()

    # Response status code
    filename = STATUS_PATH / fragment
    if filename.is_file():
        response_status = int(filename.read_text())
    else:
        response_status = 200

    return MockResponse(response_text, response_status)


def simulate_bgg_401(url: str, params: dict[str, Any], timeout: int, headers: dict[str, Any]) -> MockResponse:
    return MockResponse(text="", status_code=401)
