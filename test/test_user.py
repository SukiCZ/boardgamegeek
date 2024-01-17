import datetime
import logging

import _common
import pytest

from boardgamegeek import BGGItemNotFoundError, BGGValueError

progress_called = False


def progress_cb(items, total):
    global progress_called
    logging.debug(f"progress_cb: fetched {items} items out of {total}")
    progress_called = True


def test_get_user_with_invalid_parameters(bgg):
    # test how the module reacts to unexpected parameters
    for invalid in [None, ""]:
        with pytest.raises(BGGValueError):
            bgg.user(invalid)

    with pytest.raises(BGGValueError):
        bgg.user(_common.TEST_VALID_USER, domain="voodoo")


def test_get_invalid_user_info(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    with pytest.raises(BGGItemNotFoundError):
        bgg.user(_common.TEST_INVALID_USER, progress=progress_cb)


def test_get_valid_user_info(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    global progress_called

    progress_called = False
    user = bgg.user(_common.TEST_USER_WITH_LOTS_OF_FRIENDS, progress=progress_cb)

    assert user is not None
    assert user.name == _common.TEST_USER_WITH_LOTS_OF_FRIENDS
    assert isinstance(user.id, int)
    assert progress_called

    assert isinstance(user.buddies, list)
    assert isinstance(user.guilds, list)
    assert isinstance(user.last_login, datetime.datetime)

    str(user)
    repr(user)

    for buddy in user.buddies:
        str(buddy)
        repr(buddy)

    for guild in user.guilds:
        repr(guild)

    for i in user.top10:
        repr(i)
        assert i.id >= 0
        assert i.name is not None

    for i in user.hot10:
        repr(i)
        assert i.id >= 0
        assert i.name is not None

    # for coverage's sake
    user._format(null_logger)
    assert type(user.data()) == dict

    # test that fetching user's data without buddies, guilds, hot & top works
    user = bgg.user(
        _common.TEST_VALID_USER,
        progress=progress_cb,
        buddies=False,
        guilds=False,
        hot=False,
        top=False,
    )

    assert user is not None
    assert user.name == _common.TEST_VALID_USER
    assert user.id == _common.TEST_VALID_USER_ID

    assert user.buddies == []
    assert user.guilds == []
    assert user.top10 == []
    assert user.hot10 == []
