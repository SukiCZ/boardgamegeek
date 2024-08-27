Changelog
=========


1.1.9
-----

* Set item comments when parsing geeklists. Thanks @darnir
* Fix parsing yearpublished on Collection. Fixes: #80


1.1.8
-----

* Replace question mark in tests/xml files to be able to clone on Windows


1.1.7
-----

* Add geeklist from legacy API

1.1.6
-----

* Except TypeError when initializing year published

1.1.5
-----

* Move test folder to tests

1.1.4
-----

* Remove progress callback

1.1.3
-----

* Add marketplace listing to Game

1.1.2
-----

* Use Trusted Publishers for PyPI


1.1.1
-----

* Upgrade Sphinx documentation
* Publish documentation to `readthedocs.io <https://bgg-api.readthedocs.io>`_
* Initialize Github Publish Action


1.1.0
-----

* Fix compatibility with request-cache 1.+
* Align code with PEP8


1.0.1
-----

* Fix: Parameter `versions` should be `version` when retrieving the collection data
* Some code cleanup


1.0.0
-----

* Massive refactoring. Module is now incompatible with the previous version and it can be installed via `pip install boardgamegeek2`
* Bug fixes

0.13.2
------

* Forgot to bump up version with the previous release

0.13.1
------

Changes

* If :py:meth:`boardgamegeek.games.BoardGame.search` is called without specifying `search_type`, this defaults to ["boardgame"]

Fixes

* Correcting negative years that are returned by BGG's XMLAPI (when doing searches) as very large numbers.

0.13.0
------

Features

* Added the ``choose`` parameter to :py:meth:`boardgamegeek.api.BoardGameGeek.game` which lets you control how the "right" game is selected when searching by name. One of "first", "recent" and "best-rank" can be specified in order to select the first search result, the most recently published one or the best ranked.

0.12.1
------

Changes

* Properties which returned lists no longer return ``None`` in case data is missing, but an empty list (e.g. for :py:class:`boardgamegeek.games.BoardGame`)
* Updated documentation

0.12.0
------

Changes

* Deprecated numeric values for the `search_type` parameter of :py:meth:`boardgamegeek.games.BoardGame.search`. Accepts list of strings as arguments instead, for consistency with the rest of the functions.

0.11.2
------

Fixes

* Searching for games with spaces in the name didn't work because of manually replacing the spaces with '+'

0.11.1
------

Changes

* Documentation fixups

0.11.0
------

Changes

* URLs for images and thumbnails are converted to proper URLs (the API returns them as "//cf.geekdo-images.com/images/...")

Features

* The :py:class:`boardgamegeek.games.BoardGame` has a new integer property (`None` if missing), `boardgame_rank`
* The `boardgamegeek` tool: added `-i`, which allows querying by game id
* The `boardgamegeek` tool: added `--most-recent` (default) and `--most-popular` which allow the `-g` option to give information on a different game when the "search-by-name" returns multiple results.


0.10.1
------

Changes

* Reduced default requests_per_minute to 30, for safety

0.10.0
------

Features

* Added a mechanism which makes sure the library doesn't send requests too fast to BGG, triggering their protection (HTTP error 503). It does this by serializing all the requests and making sure there's enough waiting time between them so that the configured `requests_per_minute` is respected.

Fixes

* Fixed the retry mechanism, allowing retries=0 (meaning no retries at all). Before, the code would fail if the user specified retires=0

0.9.0
-----

Changes

* Since the BoardGameGeek API and site support HTTPS along with HTTP (and will be fully transitioned to HTTPS in the future), this library now uses HTTPS by default. To disable this behaviour, pass disable_ssl=True when creating a :py:class:`boardgamegeek.api.BoardGameGeek`


0.8.1
-----

Fixes

* Infinite recursion when unpickling objects

0.8.0
-----

Features

* Fetching plays has support for min_date, max_date (thanks tomusher!)

0.7.1
-----

Fixes

* Not expecting the score of a player to be a number anymore (using the string as returned by the BGG API)

0.7.0
-----

Changes

* The XML API2 seems to throttle requests by returning HTTP 503 ; added a delay and retry in the code to try to deal with this

Features

* When retrieving the plays, players are also returned, along with their data.


0.6.0
-----

Changes

* Improved code in an attempt to prevent exceptions when trying to deal with invalid data coming from the remote XML data

Fixes

* Fixed issue #12 (an edge case which lead to comparing None to int)

0.5.0
-----

Features

* Added a new function :py:func:`boardgamegeek.api.BoardGameGeek.games()` which takes a name as argument and returns a list of :py:class:`boardgamegeek.games.BoardGame` with all the games with that name.

0.4.3
-----

Changes

* When calling :py:func:`boardgamegeek.api.BoardGameGeek.game()` with a name, return the most recently published result instead of the first one, in case of multiple results.

0.4.2
-----

Changes

* Increased default number of retries and timeout

0.4.0
-----

Changes

* The calls to the BGG API will be automatically retried two times, with a timeout of 10 seconds. This behaviour can be controlled via the retries=, timeout= and retry_delay= parameters.

Features

* Added patch from philsstein to automatically increase timeout and retry request on timeout

0.3.0
-----

Changes

* Added a property to :class:`boardgamegeek.games.BoardGame`, ``expansion`` which indicates if this item is an expansion or not
* Changed the ``expansions`` property of :class:`boardgamegeek.games.BoardGame`, now it returns a list of :class:`boardgamegeek.things.Thing` for each expansion the game has
* Added a property to :class:`boardgamegeek.games.BoardGame`, ``extends`` which returns a list of :class:`boardgamegeek.things.Thing` for each item this game is an extension to


0.2.0 (unreleased)
------------------

Changes

* Changed the object hierarchy, replaced ``BasicUser``, ``BasicGuild``, ``BasicGame`` with a :class:`boardgamegeek.things.Thing` which has a name and an id

Features

* Added support for retrieving the hot lists


0.1.0
-----

Features

* Allowing the user to specify timeouts for the requests library

0.0.14
------

Changes

* The ``.last_login`` property of an :class:`boardgamegeek.user.User` object now returns a ``datetime.datetime``

Features

* Added support for an user's top and hot lists

Bugfixes

* Exceptions raised from :func:`get_parsed_xml_response` where not properly propagated to the calling code

0.0.13
------

Features

* Improved code for fetching an user's buddies and guilds
* Improved code for fetching guild members
* Added support for listing Plays by user and by game


0.0.12
------

Features

* Added some basic argument validation to prevent pointless calls to BGG's API
* When some object (game, user name, etc.) is not found, the functions return None instead of raising an exception


0.0.11
------

Features

* Collections and Guilds are now iterable

Bugfixes

* Fixed __str__ for Collection

0.0.10
------

Features

* Updated documentation
* Improved Python 3.x compatibility (using unicode_literals)
* Added Travis integration

Bugfixes

* Fixed float division for Python 3.x

0.0.9
-----

Features

* Added support for retrieving an user's buddy and guild lists
* Started implementing some basic unit tests

Bugfixes

* Fixed handling of non-existing user names
* Properly returning the maximum number of players for a game
