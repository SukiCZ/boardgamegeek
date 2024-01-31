import datetime

import _common
import pytest

from boardgamegeek import BGGError, BGGItemNotFoundError, BGGValueError
from boardgamegeek.objects.games import (
    BoardGameRank,
    BoardGameVersion,
    BoardGameVideo,
    MarketplaceListing,
    PlayerSuggestion,
)


def test_get_unknown_game_info(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    with pytest.raises(BGGItemNotFoundError):
        bgg.game(_common.TEST_INVALID_GAME_NAME)


def test_get_game_with_invalid_parameters(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    with pytest.raises(BGGError):
        bgg.game(name=None, game_id=None)

    for invalid in [None, ""]:
        with pytest.raises(BGGError):
            bgg.game(invalid)

    for invalid in [None, "", "asd"]:
        with pytest.raises(BGGError):
            bgg.game(None, game_id=invalid)


def check_game(game):
    assert game is not None
    assert game.name == _common.TEST_GAME_NAME
    assert game.id == _common.TEST_GAME_ID
    assert game.year == 2007
    assert game.mechanics == [
        "Area Enclosure",
        "Card Drafting",
        "Hand Management",
        "Variable Player Powers",
        "Worker Placement",
    ]
    assert game.min_players == 1
    assert game.max_players == 5
    assert game.thumbnail == "https://cf.geekdo-images.com/images/pic259085_t.jpg"
    assert game.image == "https://cf.geekdo-images.com/images/pic259085.jpg"
    assert game.playing_time > 100
    assert game.min_age == 12

    assert "Economic" in game.categories
    assert "Farming" in game.categories

    assert game.families == [
        "Agricola",
        "Animals: Cattle",
        "Animals: Horses",
        "Animals: Pigs",
        "Animals: Sheep",
        "Harvest Series",
        "Solitaire Games",
        "Tableau Building",
    ]
    assert game.designers == ["Uwe Rosenberg"]

    assert "Lookout Games" in game.publishers
    assert "Compaya.hu - Gamer Café Kft." in game.publishers

    assert "Агрикола" in game.alternative_names
    assert "아그리콜라" in game.alternative_names

    # some not so exact assertions
    assert game.users_rated >= 34000
    assert 0.0 <= game.rating_average <= 10.0
    assert 0.0 <= game.rating_bayes_average <= 10.0

    assert isinstance(game.rating_stddev, float)
    assert isinstance(game.rating_median, float)
    assert game.rating_num_weights >= 0
    assert isinstance(game.rating_average_weight, float)

    assert isinstance(game.boardgame_rank, int)

    # check for videos
    assert isinstance(game.videos, list)
    assert len(game.videos) > 0
    for vid in game.videos:
        assert isinstance(vid, BoardGameVideo)
        assert isinstance(vid.id, int)
        assert type(vid.name) in _common.STR_TYPES_OR_NONE
        assert type(vid.category) in _common.STR_TYPES_OR_NONE
        assert type(vid.language) in _common.STR_TYPES_OR_NONE
        assert type(vid.uploader) in _common.STR_TYPES_OR_NONE
        assert vid.link.startswith("http")
        assert isinstance(vid.uploader_id, int)
        assert isinstance(vid.post_date, datetime.datetime)

    # check for versions
    assert isinstance(game.versions, list)
    assert len(game.versions) > 0
    for ver in game.versions:
        assert isinstance(ver, BoardGameVersion)
        assert isinstance(ver.id, int)
        assert type(ver.name) in _common.STR_TYPES_OR_NONE
        assert type(ver.language) in _common.STR_TYPES_OR_NONE
        assert type(ver.publisher) in _common.STR_TYPES_OR_NONE
        assert type(ver.artist) in _common.STR_TYPES_OR_NONE
        assert type(ver.product_code) in _common.STR_TYPES_OR_NONE
        assert isinstance(ver.year, int)
        assert isinstance(ver.width, float)
        assert isinstance(ver.length, float)
        assert isinstance(ver.depth, float)
        assert isinstance(ver.weight, float)

    # check the ranks of the result, to make sure everything is returned properly
    assert isinstance(game.ranks, list)
    for rank in game.ranks:
        assert isinstance(rank, BoardGameRank)
        assert type(rank.type) in _common.STR_TYPES_OR_NONE

    # check player suggestions were retrieved
    assert isinstance(game.player_suggestions, list)
    suggestions_not_found = set(range(game.min_players, game.max_players + 1))

    for sg in game.player_suggestions:
        assert isinstance(sg, PlayerSuggestion)
        assert isinstance(sg.player_count, str)
        assert isinstance(sg.numeric_player_count, int)
        assert isinstance(sg.best, int)
        assert isinstance(sg.not_recommended, int)
        assert isinstance(sg.recommended, int)
        try:
            # the test game has a number of players between 1 and 5, but also a suggestion for 5+ players (huh?)
            # That's why the try...except here.
            suggestions_not_found.remove(sg.numeric_player_count)
        except KeyError:
            pass

    # should have found suggestions for all number of players
    assert not len(suggestions_not_found)

    # check marketplace listings were retrieved
    assert isinstance(game.marketplace, list)
    for listing in game.marketplace:
        assert isinstance(listing, MarketplaceListing)
        assert isinstance(listing.price, float)
        assert isinstance(listing.currency, str)
        assert isinstance(listing.condition, str)
        assert isinstance(listing.link, str)
        assert isinstance(listing.list_date, datetime.datetime)
        assert isinstance(listing.notes, str)

    # make sure no exception gets thrown
    repr(game)


def test_get_known_game_info(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    # use an older game that's not so likely to change
    game = bgg.game(
        _common.TEST_GAME_NAME, videos=True, versions=True, marketplace=True
    )

    check_game(game)

    # for coverage's sake
    game._format(null_logger)

    assert type(game.data()) == dict


def test_get_known_game_info_by_id(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    game = bgg.game(
        None, game_id=_common.TEST_GAME_ID, videos=True, versions=True, marketplace=True
    )
    check_game(game)


def test_get_known_game_info_by_id_list(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    game_list = bgg.game_list(
        game_id_list=[_common.TEST_GAME_ID, _common.TEST_GAME_ID_2],
        videos=True,
        versions=True,
        marketplace=True,
    )
    check_game(game_list[0])


def test_game_id_with_invalid_params(bgg):
    with pytest.raises(BGGValueError):
        bgg.get_game_id(_common.TEST_GAME_NAME, choose="voodoo")


def test_get_game_id_by_name(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    game_id = bgg.get_game_id(_common.TEST_GAME_NAME)
    assert game_id == _common.TEST_GAME_ID

    # Use the game "Eclipse" to test the game choosing methods
    all_eclipse_games = bgg.games("eclipse")

    game_id = bgg.get_game_id("eclipse", choose="first")
    assert game_id == all_eclipse_games[0].id

    game_id = bgg.get_game_id("eclipse", choose="recent")
    recent_year = -100000
    recent_id = None
    for g in all_eclipse_games:
        if g.year > recent_year:
            recent_id = g.id
            recent_year = g.year
    assert game_id == recent_id

    game_id = bgg.get_game_id("eclipse", choose="best-rank")
    best_rank = 1000000000
    best_id = None
    for g in all_eclipse_games:
        if g.boardgame_rank is not None and g.boardgame_rank < best_rank:
            best_id = g.id
            best_rank = g.boardgame_rank
    assert game_id == best_id


def test_get_game_by_name_not_exact(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    game = bgg.game("scythe the rise of fenris", exact=False)
    assert game.name == "Scythe: The Rise of Fenris"


def test_get_games_by_name(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    games = bgg.games("coup")

    for g in games:
        assert g is not None
        assert isinstance(g.id, int)
        assert g.name == "Coup"
        g._format(null_logger)

    assert len(games) > 1


def test_get_accessory(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    game = bgg.game(game_id=_common.TEST_GAME_ACCESSORY_ID)

    assert game.id == _common.TEST_GAME_ACCESSORY_ID
    assert game.accessory
