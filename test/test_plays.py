import datetime
import logging

import _common
import pytest

from boardgamegeek import BGGError, BGGItemNotFoundError, BGGValueError
from boardgamegeek.objects.plays import GamePlays, Plays, PlaySession, UserPlays

progress_called = False


def progress_cb(items, total):
    global progress_called
    logging.debug(f"progress_cb: fetched {items} items out of {total}")
    progress_called = True


def test_get_plays_with_invalid_parameters(bgg):
    with pytest.raises(BGGValueError):
        bgg.plays(name=None, game_id=None)

    with pytest.raises(BGGValueError):
        bgg.plays(name="", game_id=None)

    with pytest.raises(BGGValueError):
        bgg.plays(name=None, game_id="asd")


def test_get_plays_with_unknown_username_and_id(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    with pytest.raises(BGGItemNotFoundError):
        bgg.plays(name=_common.TEST_INVALID_USER)

    with pytest.raises(BGGItemNotFoundError):
        bgg.plays(name=None, game_id=1928391829)


def test_get_plays_with_invalid_dates(bgg):
    # A string is invalid so should raise an error
    with pytest.raises(BGGValueError):
        bgg.plays(name=_common.TEST_VALID_USER, min_date="2014-01-01")

    with pytest.raises(BGGValueError):
        bgg.plays(name=_common.TEST_VALID_USER, max_date="2014-12-31")


def test_get_plays_with_valid_dates(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    min_date = datetime.date(2014, 1, 1)
    max_date = datetime.date(2014, 12, 31)
    plays = bgg.plays(_common.TEST_VALID_USER, min_date=min_date, max_date=max_date)
    assert len(plays) > 0


def test_get_plays_of_user(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    global progress_called

    plays = bgg.plays(name=_common.TEST_VALID_USER, progress=progress_cb)

    assert isinstance(plays, UserPlays)
    assert plays.user == _common.TEST_VALID_USER
    assert plays.user_id == _common.TEST_VALID_USER_ID

    for p in plays.plays:
        assert isinstance(p.id, int)
        assert p.user_id == _common.TEST_VALID_USER_ID
        assert isinstance(p.date, datetime.datetime)
        assert p.quantity >= 0
        assert p.duration >= 0
        assert isinstance(p.incomplete, bool)
        assert isinstance(p.nowinstats, int)
        assert isinstance(p.game_id, int)
        assert isinstance(p.game_name, str)
        assert type(p.comment) in [type(None), str]

        assert isinstance(p.players, list)
        if p.players:
            for player in p.players:
                assert hasattr(player, "startposition")
                assert hasattr(player, "username")
                assert hasattr(player, "user_id")
                assert hasattr(player, "name")
                assert hasattr(player, "score")
                assert hasattr(player, "new")
                assert hasattr(player, "win")
                assert hasattr(player, "rating")
                assert hasattr(player, "color")
                assert hasattr(player, "location")

    plays._format(null_logger)


def test_get_plays_of_game(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    global progress_called

    plays = bgg.plays(game_id=_common.TEST_GAME_ID_2, progress=progress_cb)

    assert isinstance(plays, GamePlays)

    assert plays.game_id == _common.TEST_GAME_ID_2

    for p in plays.plays:
        assert isinstance(p.id, int)
        assert isinstance(p.user_id, int)
        assert type(p.date) in [datetime.datetime, type(None)]
        assert p.quantity >= 0
        assert p.duration >= 0
        assert isinstance(p.incomplete, bool)
        assert isinstance(p.nowinstats, int)
        assert p.game_id == _common.TEST_GAME_ID_2
        assert p.game_name == _common.TEST_GAME_NAME_2

    plays._format(null_logger)


def test_create_plays_with_initial_data():
    with pytest.raises(BGGError):
        Plays({"plays": [{"user_id": 10}]})

    p = Plays({"plays": [{"id": 10, "user_id": 102, "date": "2014-01-02"}]})

    assert len(p) == 1
    assert isinstance(p[0], PlaySession)
    assert p[0].id == 10
    assert p[0].user_id == 102
    assert isinstance(p[0].date, datetime.datetime)
    assert p[0].date.strftime("%Y-%m-%d") == "2014-01-02"

    # it also accepts datetime objects
    now = datetime.datetime.utcnow()
    p = Plays({"plays": [{"id": 10, "user_id": 102, "date": now}]})

    assert p[0].date == now
