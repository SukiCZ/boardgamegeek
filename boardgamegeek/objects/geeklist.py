from ..utils import DictObject
from ..exceptions import BGGError
from .things import Thing


class GeekListComment(DictObject):
    """
    Object containing details about a comment in a geeklist
    """

    def __init__(self, data):
        super().__init__(data)

    def __repr__(self):
        return f"GeekListComment (on {self.date} by [{self.username}])"

    def _format(self, log):
        log.info(f"  date         : {self.date}")
        log.info(f"  username     : {self.username}")
        log.info(f"  postdate     : {self.postdate}")
        log.info(f"  editdate     : {self.editdate}")
        log.info(f"  thumbs count : {self.thumbs}")
        log.info(f"  text         : {self.text}")


class GeekList(Thing):
    """
    Object containing information about a geeklist
    """

    def __init__(self, data):
        self._comments = []
        self._items = []
        super().__init__(data)

    def __repr__(self):
        return f"GeekList (id: {self.id})"

    def __len__(self):
        return len(self._items)

    def add_comment(self, comment_data):
        """
        Add a comment to the ``GeekList``

        :param dict comment_data: comment data
        :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
        """
        try:
            comment = GeekListComment(comment_data)
        except KeyError:
            raise BGGError("invalid item data")
        self._comments.append(comment)
        return comment

    def add_item(self, item_data):
        """
        Add an item to the ``GeekList``

        :param dict item_data: item data
        :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
        """
        try:
            item = GeekListItem(item_data)
        except KeyError:
            raise BGGError("invalid item data")
        self._items.append(item)
        return item

    @property
    def comments(self):
        """
        Returns the comments in the collection

        :returns: the comments in the geeklist
        :rtype: list of :py:class:`boardgamegeek.games.CollectionBoardGame`
        """
        return self._comments

    @property
    def items(self):
        """
        Returns the items in the geeklist

        :returns: the items in the geeklist
        :rtype: list of :py:class:`boardgamegeek.games.CollectionBoardGame`
        """
        return self._items

    def __iter__(self):
        yield from self._items

    def _format(self, log):
        log.info(f"geeklist id           : {self.id}")
        log.info(f"geeklist name (title) : {self.name}")
        log.info(f"geeklist posted at    : {self.postdate}")
        log.info(f"geeklist edited at    : {self.editdate}")
        log.info(f"geeklist thumbs count : {self.thumbs}")
        log.info(f"geeklist numitems     : {self.numitems}")
        log.info(f"geeklist description  : {self.description}")
        log.info("comments")
        for c in self.comments:
            c._format(log)
            log.info("")
        log.info("items")
        for i in self:
            i._format(log)
            log.info("")

    @property
    def title(self):
        # alias for name
        return self.name


class GeekListItem(DictObject):
    """
    Object containing information about a geeklist item
    """

    def __init__(self, data):
        self._comments = []
        super().__init__(data)

    def __repr__(self):
        return f"GeekListItem (id: {self.id})"

    def set_object(self, object_data):
        """
        Set the object in the ``GeekListItem``

        :param dict object_data: objects data
        :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
        """
        try:
            self._object = GeekListObject(object_data)
        except KeyError:
            raise BGGError("invalid object data")
        return self._object

    def add_comment(self, comment_data):
        """
        Add a comment to the ``GeekList``

        :param dict comment_data: comment data
        :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
        """
        try:
            comment = GeekListComment(comment_data)
        except KeyError:
            raise BGGError("invalid item data")
        self._comments.append(comment)
        return comment

    @property
    def comments(self):
        """
        Returns the comments in the collection

        :returns: the comments in the geeklist
        :rtype: list of :py:class:`boardgamegeek.games.CollectionBoardGame`
        """
        return self._comments

    def _format(self, log):
        log.info(f"id                 : {self.id}")
        log.info(f"username           : {self.username}")
        log.info("object")
        self.object._format(log)
        log.info(f"posted at          : {self.postdate}")
        log.info(f"edited at          : {self.editdate}")
        log.info(f"thumbs count       : {self.thumbs}")
        log.info(f"body (description) : {self.body}")
        log.info("comments")
        for c in self.comments:
            c._format(log)
            log.info("")

    @property
    def object(self):
        return self._object

    @property
    def description(self):
        # alias for body
        return self.body


class GeekListObject(Thing):
    """
    Object containing information about a geeklist object (e.g. a game reference)
    """

    def __init__(self, data):
        self._items = []
        super().__init__(data)

    def __repr__(self):
        return f"GeekListItem (id: {self.id})"

    def _format(self, log):
        log.info(f"id      : {self.id}")
        log.info(f"name    : {self.name}")
        log.info(f"imageid : {self.imageid}")
        log.info(f"type    : {self.type}")
        log.info(f"subtype : {self.subtype}")
