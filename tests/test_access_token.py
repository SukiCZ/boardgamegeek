import pytest

import _common
from boardgamegeek import BGGClient, BGGClientLegacy, CacheBackendNone
from boardgamegeek.exceptions import BGGApiUnauthorizedError


def test_bgg_client_with_access_token(mocker):
    """Test that BGGClient passes access token in Authorization header."""
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg

    # Create client with access token
    access_token = "test_access_token_12345"
    bgg = BGGClient(access_token=access_token, cache=CacheBackendNone())

    # Store the access token
    assert bgg._access_token == access_token

    # Make a request that will trigger the authentication
    bgg.user(_common.TEST_VALID_USER)

    # Verify that the request was made with the correct Authorization header
    mock_get.assert_called()
    call_args = mock_get.call_args

    # Check that headers were passed
    assert "headers" in call_args.kwargs
    headers = call_args.kwargs["headers"]

    # Check that the Authorization header contains our token
    assert headers is not None
    assert "Authorization" in headers
    assert headers["Authorization"] == f"Bearer {access_token}"


def test_bgg_client_with_invalid_access_token(mocker):
    """Test that BGGClient handles invalid access token gracefully."""
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_bgg_401

    # Create client with an invalid access token (empty string)
    access_token = ""
    bgg = BGGClient(access_token=access_token, cache=CacheBackendNone())

    # Store the access token
    assert bgg._access_token == access_token

    with pytest.raises(BGGApiUnauthorizedError):
        # Make a request
        bgg.user(_common.TEST_VALID_USER)

    # Verify that the request was made
    mock_get.assert_called()
    call_args = mock_get.call_args

    # Check that headers parameter is None when token is empty
    assert "headers" in call_args.kwargs
    headers = call_args.kwargs["headers"]
    assert headers is None


def test_bgg_client_legacy_with_access_token(mocker):
    """Test that BGGClientLegacy also supports access tokens."""
    mock_get = mocker.patch("requests.sessions.Session.get")
    mock_get.side_effect = _common.simulate_legacy_bgg

    # Create legacy client with access token
    access_token = "legacy_test_token_67890"
    bgg = BGGClientLegacy(access_token=access_token, cache=CacheBackendNone())

    # Store the access token
    assert bgg._access_token == access_token

    # Make a request
    bgg.geeklist(_common.TEST_GEEKLIST_ID)

    # Verify that the request was made with the correct Authorization header
    mock_get.assert_called()
    call_args = mock_get.call_args

    # Check that headers were passed
    assert "headers" in call_args.kwargs
    headers = call_args.kwargs["headers"]

    # Check that the Authorization header contains our token
    assert headers is not None
    assert "Authorization" in headers
    assert headers["Authorization"] == f"Bearer {access_token}"


def test_auth_headers_method():
    """Test the _get_auth_headers method directly."""
    # Test with token
    bgg_with_token = BGGClient(access_token="my_token")
    headers = bgg_with_token._get_auth_headers()
    assert headers == {"Authorization": "Bearer my_token"}
