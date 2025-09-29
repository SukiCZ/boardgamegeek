import _common

from boardgamegeek import BGGRestrictSearchResultsTo


def test_search(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    res = bgg.search("some invalid game name", exact=True)
    assert not len(res)

    res = bgg.search("Twilight Struggle", exact=True)
    assert len(res)

    # test that the search type is ignored
    res = bgg.search("Agricola", search_type=[BGGRestrictSearchResultsTo.BOARD_GAME])
    assert isinstance(res[0].id, int)
