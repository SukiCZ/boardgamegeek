=======
BGG-API
=======

A Python API wrapper for BoardGameGeek_

.. note::

   The documentation is a work in progress. You can check out the unit tests for examples on how to use the library.


Introduction
============


``bgg-api`` is a Python wrapper to easily access data from BoardGameGeek_ XML API.

It's continuation of boardgamegeek2_, which is an almost completely rewritten fork of libBGG_.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   modules
   changelog


Features
========

This library exposes (as Python objects with properties) the following BoardGameGeek_ entities:

* Games
* Users
* User collections
* Player guilds
* Plays
* Hot items

requests-cache_ is used for locally caching replies in order to reduce the amount of requests sent to the server.

.. note::
    The cache is enabled by default and it's configured to use memory only. It's also possible to use SQLite for a
    persistent cache.


Installation
============

.. code-block:: shell

        pip install bgg-api

Usage
=====

.. code-block:: python

    from boardgamegeek import BGGClient

    bgg = BGGClient()

    game = bgg.game("Monopoly")

    print(game.year)  # 1935
    print(game.rating_average)  # 4.36166


TODO
====

* Not all the information exposed by the official API is stored into the Python objects. Need to improve this.
* Try to support the other sites from the boardgamegeek's family
* Allow better control for configuring the cache
* Improve documentation :)


Contributions/suggestions are welcome!

Credits
=======

Original authors:

* Cosmin Luță (github:lcosmin)
* Phil S. Stein (github:philsstein)
* Geoff Lawler (github:glawler)

Contributions to this fork:

* Tom Usher (github:tomusher)
* Brent Ropp (github:bar350)
* Michał Machnicki (github:machnic)
* Philip Kendall (github:pak21)
* David Feng (github:selwyth)
* Emil Stenström (github:EmilStenstrom)
* Bill Sacks (github:billsacks)
* Arnauld Van Muysewinkel (github:arnauldvm)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _BoardGameGeek: http://www.boardgamegeek.com
.. _boardgamegeek2: https://github.com/lcosmin/boardgamegeek
.. _libBGG: https://github.com/philsstein/libBGG
.. _requests-cache: https://pypi.python.org/pypi/requests-cache
