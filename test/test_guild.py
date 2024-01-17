import logging

import _common
import pytest

from boardgamegeek import BGGItemNotFoundError, BGGValueError

progress_called = False


def progress_cb(items, total):
    global progress_called
    logging.debug(f"progress_cb: fetched {items} items out of {total}")
    progress_called = True


def test_get_guild_with_invalid_parameters(bgg):
    # test how the module reacts to unexpected parameters
    for invalid in [None, [], {}]:
        with pytest.raises(BGGValueError):
            bgg.guild(invalid)


def test_get_valid_guild_info(bgg, mocker, null_logger):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    global progress_called

    progress_called = False
    # Test with a guild with a big number members so that we can cover the code that fetches the next pages
    guild = bgg.guild(_common.TEST_GUILD_ID, progress=progress_cb)

    assert progress_called
    assert guild.id == _common.TEST_GUILD_ID
    assert guild.name == "Geek Tools"

    assert guild.addr1 is None
    assert guild.addr2 is None
    assert guild.address is None

    for member in guild:
        pass

    repr(guild)

    assert len(guild) > 0

    # for coverage's sake
    guild._format(null_logger)
    assert type(guild.data()) == dict

    # try to fetch a guild that also has an address besides members :D
    guild = bgg.guild(_common.TEST_GUILD_ID_2)

    assert guild.id == _common.TEST_GUILD_ID_2
    assert guild.addr1 is not None
    assert guild.addr2 is not None
    assert guild.address == f"{guild.addr1} {guild.addr2}"

    # fetch guild, but without members this time
    guild = bgg.guild(_common.TEST_GUILD_ID, members=False)

    assert guild.members_count == 0
    assert guild.members == set()


def test_get_invalid_guild_info(bgg, mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    with pytest.raises(BGGItemNotFoundError):
        bgg.guild(0, progress=progress_cb)
