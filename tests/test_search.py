import _common
import pytest

from boardgamegeek import BGGRestrictSearchResultsTo, BGGValueError


def test_search(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    res = bgg.search("some invalid game name", exact=True)
    assert not len(res)

    res = bgg.search("Twilight Struggle", exact=True)
    assert len(res)

    # test that the new type of search works
    res = bgg.search("Agricola", search_type=[BGGRestrictSearchResultsTo.BOARD_GAME])
    assert isinstance(res[0].id, int)

    with pytest.raises(BGGValueError):
        bgg.search("Agricola", search_type=["invalid-search-type"])
