from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..exceptions import BGGError
from .things import Thing


class GeekListComment(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def __repr__(self) -> str:
        return f"GeekListComment (on {self.date} by [{self.username}])"  # type: ignore[attr-defined]

    def _format(self, log: logging.Logger) -> None:
        log.info(f"  date         : {self.date}")  # type: ignore[attr-defined]
        log.info(f"  username     : {self.username}")  # type: ignore[attr-defined]
        log.info(f"  postdate     : {self.postdate}")  # type: ignore[attr-defined]
        log.info(f"  editdate     : {self.editdate}")  # type: ignore[attr-defined]
        log.info(f"  thumbs count : {self.thumbs}")  # type: ignore[attr-defined]
        log.info(f"  text         : {self.text}")  # type: ignore[attr-defined]

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class GeekListObject(Thing):
    def __repr__(self) -> str:
        return f"GeekListItem (id: {self.id})"

    def _format(self, log: logging.Logger) -> None:
        log.info(f"id      : {self.id}")
        log.info(f"name    : {self.name}")
        log.info(f"imageid : {self.imageid}")  # type: ignore[attr-defined]
        log.info(f"type    : {self.type}")  # type: ignore[attr-defined]
        log.info(f"subtype : {self.subtype}")  # type: ignore[attr-defined]


class GeekListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    comments: list[GeekListComment] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._object: GeekListObject | None = None

    def __repr__(self) -> str:
        return f"GeekListItem (id: {self.id})"  # type: ignore[attr-defined]

    def set_object(self, object_data: dict[str, Any]) -> GeekListObject:
        try:
            self._object = GeekListObject.model_validate(object_data)
        except Exception:
            raise BGGError("invalid object data")
        return self._object

    def add_comment(self, comment_data: dict[str, Any]) -> GeekListComment:
        try:
            comment = GeekListComment.model_validate(comment_data)
        except Exception:
            raise BGGError("invalid item data")
        self.comments.append(comment)
        return comment

    @property
    def object(self) -> GeekListObject:
        return self._object  # type: ignore[return-value]

    @property
    def description(self) -> str:
        return str(self.body)  # type: ignore[attr-defined]

    def _format(self, log: logging.Logger) -> None:
        log.info(f"id                 : {self.id}")  # type: ignore[attr-defined]
        log.info(f"username           : {self.username}")  # type: ignore[attr-defined]
        log.info("object")
        self.object._format(log)
        log.info(f"posted at          : {self.postdate}")  # type: ignore[attr-defined]
        log.info(f"edited at          : {self.editdate}")  # type: ignore[attr-defined]
        log.info(f"thumbs count       : {self.thumbs}")  # type: ignore[attr-defined]
        log.info(f"body (description) : {self.body}")  # type: ignore[attr-defined]
        log.info("comments")
        for c in self.comments:
            c._format(log)
            log.info("")

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class GeekList(Thing):
    comments: list[GeekListComment] = Field(default_factory=list)
    items: list[GeekListItem] = Field(default_factory=list)

    def __repr__(self) -> str:
        return f"GeekList (id: {self.id})"

    def __len__(self) -> int:
        return len(self.items)

    def add_comment(self, comment_data: dict[str, Any]) -> GeekListComment:
        try:
            comment = GeekListComment.model_validate(comment_data)
        except Exception:
            raise BGGError("invalid item data")
        self.comments.append(comment)
        return comment

    def add_item(self, item_data: dict[str, Any]) -> GeekListItem:
        try:
            item = GeekListItem.model_validate(item_data)
        except Exception:
            raise BGGError("invalid item data")
        self.items.append(item)
        return item

    def __iter__(self) -> Generator[GeekListItem]:  # type: ignore[override]
        yield from self.items

    @property
    def title(self) -> str:
        return self.name

    def _format(self, log: logging.Logger) -> None:
        log.info(f"geeklist id           : {self.id}")
        log.info(f"geeklist name (title) : {self.name}")
        log.info(f"geeklist posted at    : {self.postdate}")  # type: ignore[attr-defined]
        log.info(f"geeklist edited at    : {self.editdate}")  # type: ignore[attr-defined]
        log.info(f"geeklist thumbs count : {self.thumbs}")  # type: ignore[attr-defined]
        log.info(f"geeklist numitems     : {self.numitems}")  # type: ignore[attr-defined]
        log.info(f"geeklist description  : {self.description}")  # type: ignore[attr-defined]
        log.info("comments")
        for c in self.comments:
            c._format(log)
            log.info("")
        log.info("items")
        for i in self:
            i._format(log)
            log.info("")

    def data(self) -> dict[str, Any]:
        return self.model_dump()
