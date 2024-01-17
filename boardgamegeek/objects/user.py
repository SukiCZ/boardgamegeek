"""
:mod:`boardgamegeek.user` - BoardGameGeek "Users"
=================================================

.. module:: boardgamegeek.user
   :platform: Unix, Windows
   :synopsis: class handling user information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from copy import copy

from .things import Thing


class User(Thing):
    """
    Information about an user.
    """

    def __init__(self, data):
        kw = copy(data)
        if "buddies" not in kw:
            kw["buddies"] = []

        self._buddies = []
        for i in kw["buddies"]:
            self._buddies.append(Thing(i))

        if "guilds" not in kw:
            kw["guilds"] = []
        self._guilds = []
        for i in kw["guilds"]:
            self._guilds.append(Thing(i))

        if "hot" not in kw:
            kw["hot"] = []
        self._hot = []
        for i in kw["hot"]:
            self._hot.append(Thing(i))

        if "top" not in kw:
            kw["top"] = []
        self._top = []
        for i in kw["top"]:
            self._top.append(Thing(i))

        super().__init__(kw)

    def __str__(self):
        return f"User: {self.firstname} {self.lastname}"

    def __repr__(self):
        return f"User: {self.name} (id: {self.id})"

    def add_buddy(self, data):
        """
        Add a buddy to this user

        :param dict data: buddy's data
        """
        self._buddies.append(Thing(data))
        # self._data["buddies"].append(data)

    def add_guild(self, data):
        self._guilds.append(Thing(data))
        # self._data["guilds"].append(data)

    def add_top_item(self, data):
        self._data["top"].append(data)
        self._top.append(Thing(data))

    def add_hot_item(self, data):
        self._data["hot"].append(data)
        self._hot.append(Thing(data))

    def _format(self, log):
        log.info(f"id          : {self.id}")
        log.info(f"login name  : {self.name}")
        log.info(f"first name  : {self.firstname}")
        log.info(f"last name   : {self.lastname}")
        log.info(f"state       : {self.state}")
        log.info(f"country     : {self.country}")
        log.info(f"home page   : {self.homepage}")
        log.info(f"avatar      : {self.avatar}")
        log.info(f"xbox acct   : {self.xbox_account}")
        log.info(f"wii acct    : {self.wii_account}")
        log.info(f"steam acct  : {self.steam_account}")
        log.info(f"psn acct    : {self.psn_account}")
        log.info(f"last login  : {self.last_login}")
        log.info(f"trade rating: {self.trade_rating}")

        log.info(
            "user has {} buddies{}".format(
                self.total_buddies,
                " (forever alone :'( )" if self.total_buddies == 0 else "",
            )
        )
        buddies = self.buddies
        if buddies:
            for b in buddies:
                log.info(f"- {b.name}")

        log.info(f"user is member in {self.total_guilds} guilds")
        guilds = self.guilds
        if guilds:
            for g in guilds:
                log.info(f"- {g.name}")

        log.info("top10 items")
        for i in self.top10:
            log.info(f"- {i.name} (id: {i.id})")

        log.info("hot10 items")
        for i in self.hot10:
            log.info(f"- {i.name} (id: {i.id})")

    @property
    def total_buddies(self):
        """
        :return: number of buddies
        :rtype: integer
        """
        return len(self._buddies)

    @property
    def total_guilds(self):
        """
        :return: number of guilds
        :rtype: integer
        """
        return len(self._guilds)

    @property
    def top10(self):
        """
        :return: user's top10
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self._top

    @property
    def hot10(self):
        """
        :return: user's hot10
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self._hot

    @property
    def buddies(self):
        """
        :return: user's buddies
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self._buddies

    @property
    def guilds(self):
        """
        :return: user's guilds
        :rtype: list of :py:class:`boardgamegeek.things.Thing`
        """
        return self._guilds

    @property
    def firstname(self):
        """
        :return: user's first name
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("firstname")

    @property
    def lastname(self):
        """
        :return: user's last name
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("lastname")

    @property
    def avatar(self):
        """
        :return: avatar's URL
        :rtype: str
        :return: ``None`` if n/a
        """
        return self._data.get("avatarlink")

    @property
    def last_login(self):
        return self._data.get("lastlogin")

    @property
    def state(self):
        return self._data.get("stateorprovince")

    @property
    def country(self):
        return self._data.get("country")

    @property
    def homepage(self):
        return self._data.get("webaddress")

    @property
    def xbox_account(self):
        return self._data.get("xboxaccount")

    @property
    def wii_account(self):
        return self._data.get("wiiaccount")

    @property
    def steam_account(self):
        return self._data.get("steam_account")

    @property
    def psn_account(self):
        return self._data.get("psnaccount")

    @property
    def trade_rating(self):
        return self._data.get("trade_rating")
