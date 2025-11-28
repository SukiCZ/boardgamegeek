import os
import tempfile

import _common
import pytest

from boardgamegeek import BGGClient, BGGValueError, CacheBackendNone, CacheBackendSqlite


#
# Test caches
#
def test_no_caching(mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    # test that we can disable caching
    bgg = BGGClient(access_token="token", cache=CacheBackendNone())

    user = bgg.user(_common.TEST_VALID_USER)

    assert user is not None
    assert user.name == _common.TEST_VALID_USER


@pytest.mark.integration
def test_sqlite_caching(mocker):
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    # test that we can use the SQLite cache
    # generate a temporary file
    fd, name = tempfile.mkstemp(suffix=".cache")

    # close the file and unlink it, we only need the temporary name
    os.close(fd)
    os.unlink(name)

    assert not os.path.isfile(name)

    with pytest.raises(BGGValueError):
        # invalid value for the ttl parameter
        BGGClient(access_token="token", cache=CacheBackendSqlite(name, ttl="blabla", fast_save=False))

    bgg = BGGClient(access_token="token", cache=CacheBackendSqlite(name, ttl=1000))

    user = bgg.user(_common.TEST_VALID_USER)
    assert user is not None
    assert user.name == _common.TEST_VALID_USER

    assert os.path.isfile(name)

    # clean up..
    os.unlink(name)


def test_invalid_parameter_values_for_bggclient():
    with pytest.raises(BGGValueError):
        BGGClient(access_token="token", retries="asd")

    with pytest.raises(BGGValueError):
        BGGClient(access_token="token", retry_delay="asd")

    with pytest.raises(BGGValueError):
        BGGClient(access_token="token", timeout="asd")


def test_bggclient_with_access_token_parameter():
    """Test that access_token parameter works correctly."""
    # Test with valid token
    bgg = BGGClient(access_token="valid_token")
    assert bgg._access_token == "valid_token"

    # Test with None token (default)
    with pytest.raises(TypeError):
        BGGClient()  # noqa

    # Test with empty string token
    bgg = BGGClient(access_token="")
    assert bgg._access_token == ""
