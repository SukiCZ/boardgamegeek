import _common
import pytest

from boardgamegeek import BGGError, BGGValueError
from boardgamegeek.objects.hotitems import HotItem, HotItems


def test_get_hot_items_invalid_type(bgg):
    with pytest.raises(BGGValueError):
        bgg.hot_items("invalid type")


def test_get_hot_items_boardgames(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    for item in bgg.hot_items("boardgame"):
        assert isinstance(item.id, int)
        assert len(item.name) > 0
        assert isinstance(item.rank, int)
        assert type(item.year) in [int, type(None)]
        # test that all thumbnails have been fixed (http:// added)
        # note: I guess this could fail if the boardgame has no thumbnail...
        assert item.thumbnail.startswith("https://")
        item._format(null_logger)


def test_get_hot_items_boardgamepersons(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    for item in bgg.hot_items("boardgameperson"):
        assert isinstance(item.id, int)
        assert len(item.name) > 0
        assert isinstance(item.rank, int)
        assert item.year is None

        item._format(null_logger)


def test_hot_items_initial_data():
    # test that exception is raised if invalid initial data is given when trying to create a HotItems object
    with pytest.raises(BGGError):
        HotItems({"items": [{"id": 100, "name": "hotitem"}]})

    h = HotItems({"items": [{"id": 100, "name": "hotitem", "rank": 10}]})
    with pytest.raises(BGGError):
        h.add_hot_item({"id": 100, "name": "hotitem"})

    assert isinstance(h[0], HotItem)
    assert len(h) == 1
    assert h[0].id == 100
    assert h[0].name == "hotitem"
    assert h[0].rank == 10
