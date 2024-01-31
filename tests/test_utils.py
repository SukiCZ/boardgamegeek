import pickle
import threading
import time

import pytest

import boardgamegeek.utils as bggutil
from boardgamegeek import BGGClient
from boardgamegeek.objects.things import Thing


def test_get_xml_subelement_attr(xml):
    node = bggutil.xml_subelement_attr(None, "hello")
    assert node is None

    node = bggutil.xml_subelement_attr(xml, None)
    assert node is None

    node = bggutil.xml_subelement_attr(xml, "")
    assert node is None

    node = bggutil.xml_subelement_attr(xml, "node1", attribute="attr")
    assert node == "hello1"

    node = bggutil.xml_subelement_attr(xml, "node1", attribute="int_attr", convert=int)
    assert node == 1

    # test that default works
    node = bggutil.xml_subelement_attr(xml, "node_thats_missing", default="hello")
    assert node == "hello"

    node = bggutil.xml_subelement_attr(
        xml, "node1", attribute="attribute_thats_missing", default=1234
    )
    assert node == 1234

    # test quiet
    with pytest.raises(Exception):
        # attr can't be converted to int
        node = bggutil.xml_subelement_attr(xml, "node1", attribute="attr", convert=int)

    node = bggutil.xml_subelement_attr(
        xml, "node1", attribute="attr", convert=int, quiet=True
    )
    assert node is None

    node = bggutil.xml_subelement_attr(
        xml, "node1", attribute="attr", convert=int, default=999, quiet=True
    )
    assert node == 999


def test_get_xml_subelement_attr_list(xml):
    nodes = bggutil.xml_subelement_attr_list(None, "list")
    assert nodes is None

    nodes = bggutil.xml_subelement_attr_list(xml, None)
    assert nodes is None

    nodes = bggutil.xml_subelement_attr_list(xml, "")
    assert nodes is None

    list_root = xml.find("list")
    nodes = bggutil.xml_subelement_attr_list(list_root, "li", attribute="attr")
    assert nodes == ["elem1", "elem2", "elem3", "elem4"]

    nodes = bggutil.xml_subelement_attr_list(
        list_root, "li", attribute="int_attr", convert=int
    )
    assert nodes == [1, 2, 3, 4]

    nodes = bggutil.xml_subelement_attr_list(xml, "node1", attribute="attr")
    assert nodes == ["hello1"]

    # test default
    nodes = bggutil.xml_subelement_attr_list(
        list_root, "li", attribute="missing_attr", default="n/a"
    )
    assert nodes == ["n/a", "n/a", "n/a", "n/a"]

    # test quiet
    with pytest.raises(Exception):
        nodes = bggutil.xml_subelement_attr_list(
            list_root, "li", attribute="attr", convert=int
        )

    nodes = bggutil.xml_subelement_attr_list(
        list_root, "li", attribute="attr", convert=int, quiet=True
    )
    assert nodes == [None, None, None, None]

    nodes = bggutil.xml_subelement_attr_list(
        list_root, "li", attribute="attr", convert=int, quiet=True, default=1
    )
    assert nodes == [1, 1, 1, 1]


def test_get_xml_subelement_text(xml):
    node = bggutil.xml_subelement_text(None, "node1")
    assert node is None

    node = bggutil.xml_subelement_text(xml, None)
    assert node is None

    node = bggutil.xml_subelement_text(None, "")
    assert node is None

    node = bggutil.xml_subelement_text(xml, "node1")
    assert node == "text"

    # test that default is working
    node = bggutil.xml_subelement_text(
        xml, "node_thats_missing", default="default text"
    )
    assert node == "default text"

    # test that quiet is working
    with pytest.raises(Exception):
        node = bggutil.xml_subelement_text(xml, "node1", convert=int)

    node = bggutil.xml_subelement_text(xml, "node1", convert=int, quiet=True)
    assert node is None

    node = bggutil.xml_subelement_text(
        xml, "node1", convert=int, quiet=True, default="asd"
    )
    assert node == "asd"


@pytest.mark.serialize
def test_serialization():
    dummy_plays = Thing({"id": "10", "name": "fubar"})

    s = pickle.dumps(dummy_plays)
    assert s is not None

    dummy_unserialized = pickle.loads(s)
    assert isinstance(dummy_unserialized, Thing)


@pytest.mark.integration
def test_rate_limiting_for_requests():
    # create two threads, give each a list of games to fetch, disable cache and time the amount needed to
    # fetch the data. requests should be serialized, even if made from two different threads

    test_set_1 = [5, 31260, 72125]  # acquire  # agricola  # "eclipse"

    test_set_2 = [18602, 28720, 53953]  # caylus  # brass  # thunderstone]

    def _worker_thread(games):
        bgg = BGGClient(cache=None, requests_per_minute=20)
        for g in games:
            bgg.game(game_id=g)

    t1 = threading.Thread(target=_worker_thread, args=(test_set_1,))
    t2 = threading.Thread(target=_worker_thread, args=(test_set_2,))

    start_time = time.time()
    t1.start()
    t2.start()

    t1.join(timeout=10000)
    t2.join(timeout=10000)
    end_time = time.time()

    # 20 requests per minute => a request every 3 seconds x 6 games => should take around 18 seconds
    assert 15 < end_time - start_time < 21  # +/- a few seconds...

    # second test, use caching and confirm it's working when combined with the rate limiting algorithm
    # do cached requests for the test set, then do them again. should take only half of the time

    bgg = BGGClient(requests_per_minute=20)

    start_time = time.time()
    for g in test_set_1:
        bgg.game(game_id=g)
    end_time = time.time()

    assert 7 < end_time - start_time < 17  # 3 games should take ~9 seconds

    # repeat requests, should be served from cache
    for g in test_set_1:
        bgg.game(game_id=g)

    assert 0 < time.time() - end_time < 2


def test_html_unescape_function():
    escaped = "&lt;tag&gt;"

    unescaped = bggutil.html_unescape(escaped)

    assert unescaped == "<tag>"
