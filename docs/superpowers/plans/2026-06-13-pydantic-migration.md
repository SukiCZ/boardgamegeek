# Pydantic Data Models Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hand-rolled `DictObject`/`Thing` base classes in `boardgamegeek/objects/` with Pydantic `BaseModel`, gaining type validation, serialization, and IDE introspection across all domain models.

**Architecture:** Each domain object currently wraps a raw `dict[str, Any]` via `DictObject.__getattr__` and explicit `@property` accessors. The migration replaces `DictObject` with `pydantic.BaseModel` (using `extra="allow"` to preserve implicit dict-key attribute access) and converts properties that rename BGG API keys into `Field(alias=...)` declarations. Pre-processing logic in `__init__` (URL fixing, date parsing, nested model construction) moves into `@model_validator(mode='before')`. Dedup tracking sets (like `_expansions_set`) become `PrivateAttr`. The `data()` method is kept as a `model_dump()` wrapper for backward compatibility.

**Tech Stack:** Python 3.11+, pydantic ≥ 2.0, existing pytest suite as regression harness.

---

## Behavior Change to be Aware Of

- Direct model construction with missing required fields (`id`, `name`, etc.) now raises `pydantic.ValidationError` instead of `BGGError`. The **API layer** (`api.py`) still raises `BGGError`—those tests are unaffected.
- `model_dump()` is the new canonical serialization; `data()` wraps it for backward compat.
- `extra="allow"` means fields not explicitly declared are still accessible as attributes (e.g., `geeklist_item.body`, `geeklist_comment.thumbs`).

---

## File Map

| File | Change |
|---|---|
| `pyproject.toml` | Add `pydantic>=2.0` dependency |
| `boardgamegeek/objects/things.py` | Replace `Thing(DictObject)` with `Thing(BaseModel)` |
| `boardgamegeek/objects/games.py` | Migrate all 8 game model classes |
| `boardgamegeek/objects/user.py` | Migrate `User` |
| `boardgamegeek/objects/plays.py` | Migrate `PlaysessionPlayer`, `PlaySession`, `Plays`, `UserPlays`, `GamePlays` |
| `boardgamegeek/objects/collection.py` | Migrate `Collection` |
| `boardgamegeek/objects/hotitems.py` | Migrate `HotItem`, `HotItems` |
| `boardgamegeek/objects/geeklist.py` | Migrate `GeekListComment`, `GeekList`, `GeekListItem`, `GeekListObject` |
| `boardgamegeek/objects/search.py` | Migrate `SearchResult` |
| `boardgamegeek/utils.py` | Remove `DictObject`; keep it as a deprecated shim pointing to `BaseModel` |

---

## Task 1: Add Pydantic Dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pydantic to project dependencies**

In `pyproject.toml`, update the `dependencies` list:
```toml
dependencies = [
    "requests>=2.31.0,<3.0.0",
    "requests-cache>=1.1.1,<2.0.0",
    "pydantic>=2.0,<3.0"
]
```

- [ ] **Step 2: Install the new dependency**

```bash
uv sync
```

Expected: resolves and installs pydantic without errors.

- [ ] **Step 3: Run full test suite to confirm baseline is green**

```bash
pytest -x -q
```

Expected: all tests pass (establishes baseline before any changes).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add pydantic dependency"
```

---

## Task 2: Migrate `things.py` — `Thing` Base Class

**Files:**
- Modify: `boardgamegeek/objects/things.py`

This is the foundation everything else builds on. `Thing` needs `id: int` and `name: str` as required fields. Pydantic handles coercion from string IDs automatically. `extra="allow"` replaces `DictObject.__getattr__`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_things.py`:

```python
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.things import Thing


def test_thing_valid():
    t = Thing.model_validate({"id": "42", "name": "Agricola"})
    assert t.id == 42
    assert t.name == "Agricola"


def test_thing_extra_fields_accessible():
    t = Thing.model_validate({"id": 1, "name": "X", "yearpublished": 2007})
    assert t.yearpublished == 2007  # extra fields accessible via __getattr__


def test_thing_missing_id_raises():
    with pytest.raises(ValidationError):
        Thing.model_validate({"name": "X"})


def test_thing_missing_name_raises():
    with pytest.raises(ValidationError):
        Thing.model_validate({"id": 1})


def test_thing_data_method():
    t = Thing.model_validate({"id": 1, "name": "X"})
    d = t.data()
    assert d["id"] == 1
    assert d["name"] == "X"


def test_thing_repr():
    t = Thing.model_validate({"id": 5, "name": "X"})
    assert "5" in repr(t)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_things.py -v
```

Expected: FAIL — `Thing` doesn't have `model_validate`, still uses `DictObject`.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/things.py`**

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from ..exceptions import BGGError  # noqa: F401  kept for import compat


class Thing(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int
    name: str

    def data(self) -> dict[str, Any]:
        return self.model_dump()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id: {self.id})"
```

> Note: `BGGError` import is kept so existing code that does `from .things import Thing` and then `from ..exceptions import BGGError` still resolves. The old `Thing.__init__` raised `BGGError` for missing fields — Pydantic now raises `ValidationError` for the same cases.

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass. `tests/test_things.py` should now pass too.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/things.py tests/test_things.py
git commit -m "feat: migrate Thing base class to pydantic BaseModel"
```

---

## Task 3: Migrate Leaf Game Models

**Files:**
- Modify: `boardgamegeek/objects/games.py`

Migrate `BoardGameRank`, `PlayerSuggestion`, `BoardGameStats`, `BoardGameComment`, `BoardGameVideo`, `BoardGameVersion`, `MarketplaceListing` — the leaf classes that don't depend on each other.

- [ ] **Step 1: Write failing tests**

Add `tests/test_game_models.py`:

```python
import datetime
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.games import (
    BoardGameRank,
    BoardGameStats,
    BoardGameComment,
    BoardGameVideo,
    BoardGameVersion,
    MarketplaceListing,
    PlayerSuggestion,
)


def test_board_game_rank_aliases():
    rank = BoardGameRank.model_validate({
        "id": "1",
        "name": "boardgame",
        "friendlyname": "Board Game Rank",
        "value": "42",
        "bayesaverage": 7.5,
        "type": "subtype",
    })
    assert rank.id == 1
    assert rank.friendly_name == "Board Game Rank"
    assert rank.rating_bayes_average == 7.5
    assert rank.value == "42"
    assert rank.type == "subtype"


def test_board_game_stats_builds_ranks():
    data = {
        "usersrated": 1000,
        "average": 7.8,
        "bayesaverage": 7.6,
        "stddev": 1.2,
        "median": 0.0,
        "owned": 500,
        "trading": 10,
        "wanting": 50,
        "wishing": 200,
        "numcomments": 100,
        "numweights": 80,
        "averageweight": 3.6,
        "ranks": [
            {"id": "1", "name": "boardgame", "value": 5, "friendlyname": "Board Game Rank"},
            {"id": "2", "name": "strategygames", "value": 3, "friendlyname": "Strategy Game Rank"},
        ],
    }
    stats = BoardGameStats.model_validate(data)
    assert stats.users_rated == 1000
    assert stats.rating_average == 7.8
    assert stats.rating_bayes_average == 7.6
    assert stats.users_owned == 500
    assert stats.bgg_rank == 5
    assert len(stats.ranks) == 2
    assert stats.ranks[0].friendly_name == "Board Game Rank"


def test_board_game_stats_bgg_rank_none_when_no_boardgame_rank():
    stats = BoardGameStats.model_validate({"ranks": [{"id": "2", "name": "strategygames", "value": 3, "friendlyname": "X"}]})
    assert stats.bgg_rank is None


def test_player_suggestion_numeric_count():
    ps = PlayerSuggestion.model_validate({"player_count": "4+", "best": 10, "recommended": 5, "not_recommended": 1})
    assert ps.numeric_player_count == 5
    ps2 = PlayerSuggestion.model_validate({"player_count": "4", "best": 10, "recommended": 5, "not_recommended": 1})
    assert ps2.numeric_player_count == 4


def test_board_game_comment():
    c = BoardGameComment.model_validate({"username": "alice", "comment": "great game", "rating": 8.5})
    assert c.commenter == "alice"
    assert c.comment == "great game"
    assert c.rating == 8.5


def test_board_game_video_date_parsing():
    vid = BoardGameVideo.model_validate({
        "id": "100",
        "name": "Review",
        "post_date": "2023-05-15T10:00:00+00:00",
        "uploader_id": "999",
    })
    assert vid.id == 100
    assert isinstance(vid.post_date, datetime.datetime)
    assert vid.uploader_id == 999


def test_board_game_video_bad_date():
    vid = BoardGameVideo.model_validate({
        "id": "1",
        "name": "X",
        "post_date": "not-a-date",
        "uploader_id": "1",
    })
    assert vid.post_date is None


def test_board_game_version_url_fix():
    ver = BoardGameVersion.model_validate({
        "id": "1",
        "name": "English Edition",
        "thumbnail": "//cf.geekdo-images.com/pic.jpg",
        "image": "//cf.geekdo-images.com/pic_full.jpg",
        "yearpublished": 2007,
    })
    assert ver.thumbnail.startswith("http://")
    assert ver.year == 2007


def test_marketplace_listing():
    import datetime
    ml = MarketplaceListing.model_validate({
        "list_date": datetime.datetime(2023, 1, 1),
        "price": 19.99,
        "currency": "USD",
        "condition": "good",
        "notes": "some wear",
        "link": "https://example.com",
    })
    assert ml.price == 19.99
    assert ml.currency == "USD"
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_game_models.py -v
```

Expected: FAIL — classes still use `DictObject`.

- [ ] **Step 3: Replace leaf models in `boardgamegeek/objects/games.py`**

Replace the top of the file and the 7 leaf classes. Leave `BaseGame`, `CollectionBoardGame`, `BoardGame` unchanged for now (they still reference the old `DictObject`/`Thing` which still needs to work because `Thing` was already migrated — so temporarily keep any `BaseGame` etc. as-is):

```python
"""
:mod:`boardgamegeek.games` - Games information
==============================================

.. module:: boardgamegeek.objects.games
   :platform: Unix, Windows
   :synopsis: classes for storing games information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""

from __future__ import annotations

import datetime
import logging
import warnings
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field, model_validator

from ..exceptions import BGGError
from ..utils import fix_unsigned_negative, fix_url
from .things import Thing


class BoardGameRank(Thing):
    type: str | None = None
    friendly_name: str | None = Field(None, alias="friendlyname")
    value: str | None = None
    rating_bayes_average: float | None = Field(None, alias="bayesaverage")


class PlayerSuggestion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    player_count: str
    best: int
    recommended: int
    not_recommended: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def numeric_player_count(self) -> int:
        if "+" in self.player_count:
            return int(self.player_count[:-1]) + 1
        return int(self.player_count)

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BoardGameStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    users_rated: int | None = Field(None, alias="usersrated")
    rating_average: float | None = Field(None, alias="average")
    rating_bayes_average: float | None = Field(None, alias="bayesaverage")
    rating_stddev: float | None = Field(None, alias="stddev")
    rating_median: float | None = Field(None, alias="median")
    users_owned: int | None = Field(None, alias="owned")
    users_trading: int | None = Field(None, alias="trading")
    users_wanting: int | None = Field(None, alias="wanting")
    users_wishing: int | None = Field(None, alias="wishing")
    users_commented: int | None = Field(None, alias="numcomments")
    rating_num_weights: int | None = Field(None, alias="numweights")
    rating_average_weight: float | None = Field(None, alias="averageweight")
    ranks: list[BoardGameRank] = Field(default_factory=list)
    bgg_rank: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _build_ranks(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        rank_dicts = data.get("ranks", [])
        bgg_rank: int | None = None
        for rank in rank_dicts:
            if rank.get("name") == "boardgame":
                try:
                    bgg_rank = int(rank["value"])
                except (KeyError, TypeError, ValueError):
                    pass
        data["bgg_rank"] = bgg_rank
        return data

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BoardGameComment(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    commenter: str = Field(alias="username")
    comment: str
    rating: float

    def _format(self, log: logging.Logger) -> None:
        log.info(f"comment by {self.commenter} (rating: {self.rating}): {self.comment}")

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class BoardGameVideo(Thing):
    category: str | None = None
    link: str | None = None
    language: str | None = None
    uploader: str | None = None
    uploader_id: int | None = None
    post_date: datetime.datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _process_video_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "post_date" in data and not isinstance(data["post_date"], datetime.datetime):
            try:
                data["post_date"] = datetime.datetime.strptime(data["post_date"][:-6], "%Y-%m-%dT%H:%M:%S")
            except (ValueError, TypeError, IndexError):
                data["post_date"] = None
        if "uploader_id" in data and not isinstance(data["uploader_id"], int):
            try:
                data["uploader_id"] = int(data["uploader_id"])
            except (ValueError, TypeError):
                data["uploader_id"] = None
        return data

    def _format(self, log: logging.Logger) -> None:
        log.info(f"video id          : {self.id}")
        log.info(f"video title       : {self.name}")
        log.info(f"video category    : {self.category}")
        log.info(f"video link        : {self.link}")
        log.info(f"video language    : {self.language}")
        log.info(f"video uploader    : {self.uploader}")
        log.info(f"video uploader id : {self.uploader_id}")
        log.info(f"video posted at   : {self.post_date}")


class BoardGameVersion(Thing):
    artist: str | None = None
    depth: float | None = None
    length: float | None = None
    language: str | None = None
    product_code: str | None = None
    publisher: str | None = None
    weight: float | None = None
    width: float | None = None
    year: int | None = Field(None, alias="yearpublished")
    thumbnail: str | None = None
    image: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _fix_urls(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["thumbnail", "image"]:
            if field in data:
                data[field] = fix_url(data[field])
        return data

    def __repr__(self) -> str:
        return f"BoardGameVersion (id: {self.id})"

    def _format(self, log: logging.Logger) -> None:
        log.info(f"version id           : {self.id}")
        log.info(f"version name         : {self.name}")
        log.info(f"version language     : {self.language}")
        log.info(f"version publisher    : {self.publisher}")
        log.info(f"version artist       : {self.artist}")
        log.info(f"version product code : {self.product_code}")
        log.info(f"W x L x D            : {self.width} x {self.length} x {self.depth}")
        log.info(f"weight               : {self.weight}")
        log.info(f"year                 : {self.year}")


class MarketplaceListing(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    list_date: datetime.datetime | None = None
    price: float | None = None
    currency: str | None = None
    condition: str | None = None
    notes: str | None = None
    link: str | None = None

    def _format(self, log: logging.Logger) -> None:
        log.info(f"listing date       : {self.list_date}")
        log.info(f"listing price      : {self.price}")
        log.info(f"listing currency   : {self.currency}")
        log.info(f"listing condition  : {self.condition}")
        log.info(f"listing notes      : {self.notes}")
        log.info(f"listing link       : {self.link}")

    def data(self) -> dict[str, Any]:
        return self.model_dump()
```

Then keep `BaseGame`, `CollectionBoardGame`, `BoardGame` exactly as they were (they'll continue to work through duck-typing with the new `Thing` base since `Thing` still supports `.id`, `.name`, and attribute access via `extra="allow"`).

> Important: The old `BaseGame.__init__` calls `super().__init__(data)` which now hits `Thing.__init__` → `BaseModel.__init__`. This breaks `BaseGame`. **Leave `BaseGame`, `CollectionBoardGame`, `BoardGame` in their current form for now — they'll be rewritten in Task 4.**

- [ ] **Step 4: Run tests**

```bash
pytest -x -q
```

Expected: all tests pass (leaf models migrated, game hierarchy tasks still pending).

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/games.py tests/test_game_models.py
git commit -m "feat: migrate BoardGameRank, PlayerSuggestion, BoardGameStats, BoardGameComment, BoardGameVideo, BoardGameVersion, MarketplaceListing to pydantic"
```

---

## Task 4: Migrate Game Hierarchy — `BaseGame`, `CollectionBoardGame`, `BoardGame`

**Files:**
- Modify: `boardgamegeek/objects/games.py`

These three classes form the main game hierarchy. `BaseGame` holds stats/versions/marketplace. `CollectionBoardGame` adds collection-specific user status fields. `BoardGame` adds expansions, videos, comments, player suggestions.

**Key decisions:**
- Mutation methods (`add_expansion`, `add_expanded_game`, `add_comment`) now append to Pydantic list fields directly instead of mutating `self._data`.
- Dedup tracking sets become `PrivateAttr`, populated in `model_post_init`.
- `suggested_players` dict → `player_suggestions` list transformation moves to `@model_validator(mode='before')`.
- Collection status boolean fields (`own`, `prevowned`, etc.) are string "0"/"1" from XML — the before validator converts them to int for Pydantic's bool coercion.

- [ ] **Step 1: Write failing tests**

Add to `tests/test_game_models.py`:

```python
from boardgamegeek.objects.games import BaseGame, CollectionBoardGame, BoardGame


MINIMAL_STATS = {
    "usersrated": 0, "average": 0.0, "bayesaverage": 0.0,
    "stddev": 0.0, "median": 0.0, "owned": 0, "trading": 0,
    "wanting": 0, "wishing": 0, "numcomments": 0, "numweights": 0,
    "averageweight": 0.0, "ranks": [],
}


def test_base_game_construction():
    data = {
        "id": 1, "name": "Test", "stats": MINIMAL_STATS,
        "thumbnail": "//cf.geekdo-images.com/pic.jpg",
        "image": "//cf.geekdo-images.com/pic_full.jpg",
        "yearpublished": 2007,
        "minplayers": 2, "maxplayers": 4,
    }
    game = BaseGame.model_validate(data)
    assert game.id == 1
    assert game.thumbnail == "http://cf.geekdo-images.com/pic.jpg"
    assert game.year == 2007
    assert game.min_players == 2


def test_base_game_missing_stats_raises():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        BaseGame.model_validate({"id": 1, "name": "Test"})


def test_board_game_add_expansion():
    data = {
        "id": 1, "name": "Test", "stats": MINIMAL_STATS,
        "expansions": [], "expands": [], "videos": [],
    }
    game = BoardGame.model_validate(data)
    assert len(game.expansions) == 0
    game.add_expansion({"id": 99, "name": "Big Expansion"})
    assert len(game.expansions) == 1
    assert game.expansions[0].id == 99
    # dedup: adding same id again is a no-op
    game.add_expansion({"id": 99, "name": "Big Expansion"})
    assert len(game.expansions) == 1


def test_board_game_add_comment():
    data = {
        "id": 1, "name": "Test", "stats": MINIMAL_STATS,
        "expansions": [], "expands": [], "videos": [],
    }
    game = BoardGame.model_validate(data)
    game.add_comment({"username": "alice", "comment": "fun!", "rating": 9.0})
    assert len(game.comments) == 1
    assert game.comments[0].commenter == "alice"


def test_board_game_player_suggestions():
    data = {
        "id": 1, "name": "Test", "stats": MINIMAL_STATS,
        "expansions": [], "expands": [], "videos": [],
        "suggested_players": {
            "total_votes": 100,
            "results": {
                "4": {"best_rating": 80, "recommended_rating": 15, "not_recommended_rating": 5},
            }
        }
    }
    game = BoardGame.model_validate(data)
    assert len(game.player_suggestions) == 1
    assert game.player_suggestions[0].player_count == "4"
    assert game.player_suggestions[0].best == 80


def test_collection_board_game_status_fields():
    data = {
        "id": 1, "name": "Test", "stats": MINIMAL_STATS,
        "own": "1", "prevowned": "0", "want": "1",
        "wanttobuy": "0", "wanttoplay": "1", "fortrade": "0",
        "wishlist": "0", "preordered": "1",
    }
    game = CollectionBoardGame.model_validate(data)
    assert game.owned is True
    assert game.prev_owned is False
    assert game.want is True
    assert game.want_to_buy is False
    assert game.preordered is True
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_game_models.py::test_base_game_construction -v
```

Expected: FAIL — `BaseGame` still uses old `DictObject.__init__`.

- [ ] **Step 3: Replace `BaseGame`, `CollectionBoardGame`, `BoardGame` in `boardgamegeek/objects/games.py`**

Append these three classes after the leaf classes (replace the old implementations):

```python
class BaseGame(Thing):
    thumbnail: str | None = None
    image: str | None = None
    year: int | None = Field(None, alias="yearpublished")
    min_players: int | None = Field(None, alias="minplayers")
    max_players: int | None = Field(None, alias="maxplayers")
    min_playing_time: int | None = Field(None, alias="minplaytime")
    max_playing_time: int | None = Field(None, alias="maxplaytime")
    playing_time: int | None = Field(None, alias="playingtime")
    stats: BoardGameStats
    versions: list[BoardGameVersion] = Field(default_factory=list)
    marketplace: list[MarketplaceListing] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _fix_base_game(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["thumbnail", "image"]:
            if field in data:
                data[field] = fix_url(data[field])
        return data

    @property
    def users_rated(self) -> int | None:
        return self.stats.users_rated

    @property
    def rating_average(self) -> float | None:
        return self.stats.rating_average

    @property
    def rating_bayes_average(self) -> float | None:
        return self.stats.rating_bayes_average

    @property
    def rating_stddev(self) -> float | None:
        return self.stats.rating_stddev

    @property
    def rating_median(self) -> float | None:
        return self.stats.rating_median

    @property
    def ranks(self) -> list[BoardGameRank]:
        return self.stats.ranks

    @property
    def bgg_rank(self) -> int | None:
        return self.stats.bgg_rank

    @property
    def boardgame_rank(self) -> int | None:
        warnings.warn("deprecated, use 'bgg_rank' instead", DeprecationWarning, stacklevel=2)
        return self.bgg_rank


class CollectionBoardGame(BaseGame):
    last_modified: str | None = Field(None, alias="lastmodified")
    numplays: int = 0
    rating: float | None = None
    owned: bool = Field(False, alias="own")
    preordered: bool = False
    prev_owned: bool = Field(False, alias="prevowned")
    want: bool = False
    want_to_buy: bool = Field(False, alias="wanttobuy")
    want_to_play: bool = Field(False, alias="wanttoplay")
    for_trade: bool = Field(False, alias="fortrade")
    wishlist: bool = False
    wishlist_priority: str | None = Field(None, alias="wishlistpriority")
    comment: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_status_bools(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["own", "preordered", "prevowned", "want", "wanttobuy",
                       "wanttoplay", "fortrade", "wishlist"]:
            if field in data and data[field] is not None:
                try:
                    data[field] = bool(int(data[field]))
                except (ValueError, TypeError):
                    data[field] = False
        return data

    @property
    def lastmodified(self) -> str | None:
        warnings.warn("deprecated, use 'last_modified' instead", DeprecationWarning, stacklevel=2)
        return self.last_modified

    @property
    def version(self) -> BoardGameVersion | None:
        if self.versions:
            return self.versions[0]
        return None

    def _format(self, log: logging.Logger) -> None:
        log.info(f"boardgame id      : {self.id}")
        log.info(f"boardgame name    : {self.name}")
        log.info(f"number of plays   : {self.numplays}")
        log.info(f"last modified     : {self.last_modified}")
        log.info(f"rating            : {self.rating}")
        log.info(f"own               : {self.owned}")
        log.info(f"preordered        : {self.preordered}")
        log.info(f"previously owned  : {self.prev_owned}")
        log.info(f"want              : {self.want}")
        log.info(f"want to buy       : {self.want_to_buy}")
        log.info(f"want to play      : {self.want_to_play}")
        log.info(f"wishlist          : {self.wishlist}")
        log.info(f"wishlist priority : {self.wishlist_priority}")
        log.info(f"for trade         : {self.for_trade}")
        log.info(f"comment           : {self.comment}")
        for v in self.versions:
            v._format(log)


class BoardGame(BaseGame):
    alternative_names: list[str] = Field(default_factory=list)
    description: str = ""
    families: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    mechanics: list[str] = Field(default_factory=list)
    implementations: list[str] = Field(default_factory=list)
    designers: list[str] = Field(default_factory=list)
    artists: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    expansion: bool = False
    accessory: bool = False
    min_age: int | None = Field(None, alias="minage")
    expansions: list[Thing] = Field(default_factory=list)
    expands: list[Thing] = Field(default_factory=list)
    videos: list[BoardGameVideo] = Field(default_factory=list)
    comments: list[BoardGameComment] = Field(default_factory=list)
    player_suggestions: list[PlayerSuggestion] = Field(default_factory=list)

    _expansion_ids: set[int] = PrivateAttr(default_factory=set)
    _expands_ids: set[int] = PrivateAttr(default_factory=set)
    _video_ids: set[int] = PrivateAttr(default_factory=set)

    @model_validator(mode="before")
    @classmethod
    def _build_board_game(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # Convert suggested_players dict → player_suggestions list
        suggested = data.get("suggested_players", {})
        if suggested and "results" in suggested:
            suggestions = []
            for count, result in suggested["results"].items():
                suggestions.append({
                    "player_count": count,
                    "best": result.get("best_rating", 0),
                    "recommended": result.get("recommended_rating", 0),
                    "not_recommended": result.get("not_recommended_rating", 0),
                })
            data.setdefault("player_suggestions", suggestions)
        # Deduplicate expansions/expands/videos by id
        for field in ["expansions", "expands"]:
            seen: set[Any] = set()
            unique = []
            for item in data.get(field, []):
                item_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
                if item_id not in seen:
                    seen.add(item_id)
                    unique.append(item)
            data[field] = unique
        return data

    def model_post_init(self, __context: Any) -> None:
        self._expansion_ids = {exp.id for exp in self.expansions}
        self._expands_ids = {exp.id for exp in self.expands}
        self._video_ids = {vid.id for vid in self.videos}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} (id: {self.id})"

    def add_comment(self, data: dict[str, Any]) -> None:
        self.comments.append(BoardGameComment.model_validate(data))

    def add_expanded_game(self, data: dict[str, Any]) -> None:
        try:
            if data["id"] not in self._expands_ids:
                self._expands_ids.add(data["id"])
                self.expands.append(Thing.model_validate(data))
        except KeyError:
            raise BGGError("invalid expanded game data")

    def add_expansion(self, data: dict[str, Any]) -> None:
        try:
            if data["id"] not in self._expansion_ids:
                self._expansion_ids.add(data["id"])
                self.expansions.append(Thing.model_validate(data))
        except KeyError:
            raise BGGError("invalid expansion data")

    @property
    def users_owned(self) -> int | None:
        return self.stats.users_owned

    @property
    def users_trading(self) -> int | None:
        return self.stats.users_trading

    @property
    def users_wanting(self) -> int | None:
        return self.stats.users_wanting

    @property
    def users_wishing(self) -> int | None:
        return self.stats.users_wishing

    @property
    def users_commented(self) -> int | None:
        return self.stats.users_commented

    @property
    def rating_num_weights(self) -> int | None:
        return self.stats.rating_num_weights

    @property
    def rating_average_weight(self) -> float | None:
        return self.stats.rating_average_weight

    def _format(self, log: logging.Logger) -> None:
        log.info(f"boardgame id      : {self.id}")
        log.info(f"boardgame name    : {self.name}")
        log.info(f"boardgame rank    : {self.bgg_rank}")
        for alt in self.alternative_names:
            log.info(f"alternative name  : {alt}")
        log.info(f"year published    : {self.year}")
        log.info(f"minimum players   : {self.min_players}")
        log.info(f"maximum players   : {self.max_players}")
        log.info(f"playing time      : {self.playing_time}")
        log.info(f"minimum age       : {self.min_age}")
        log.info(f"thumbnail         : {self.thumbnail}")
        log.info(f"image             : {self.image}")
        log.info(f"is expansion      : {self.expansion}")
        log.info(f"is accessory      : {self.accessory}")
        log.info(f"users rated game  : {self.users_rated}")
        log.info(f"description       : {self.description}")
        for c in self.comments:
            c._format(log)
```

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_game.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/games.py tests/test_game_models.py
git commit -m "feat: migrate BaseGame, CollectionBoardGame, BoardGame to pydantic"
```

---

## Task 5: Migrate `user.py` — `User`

**Files:**
- Modify: `boardgamegeek/objects/user.py`

`User` has `buddies`, `guilds`, `hot`, `top` lists of `Thing`, all populated from nested dicts. Mutation methods (`add_buddy`, `add_guild`, `add_top_item`, `add_hot_item`) append to these lists directly. Many properties use BGG API field names (e.g., `avatarlink`, `stateorprovince`, `webaddress`, `xboxaccount`).

- [ ] **Step 1: Write failing test**

Add `tests/test_user_model.py`:

```python
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.user import User


MINIMAL_USER = {"id": "1", "name": "alice"}


def test_user_basic_fields():
    u = User.model_validate({
        **MINIMAL_USER,
        "firstname": "Alice",
        "lastname": "Smith",
        "avatarlink": "http://example.com/avatar.jpg",
        "stateorprovince": "California",
        "country": "USA",
        "webaddress": "http://alice.com",
    })
    assert u.id == 1
    assert u.name == "alice"
    assert u.firstname == "Alice"
    assert u.avatar == "http://example.com/avatar.jpg"
    assert u.state == "California"
    assert u.homepage == "http://alice.com"


def test_user_buddies_and_guilds():
    u = User.model_validate({
        **MINIMAL_USER,
        "buddies": [{"id": 2, "name": "bob"}],
        "guilds": [{"id": 10, "name": "chess club"}],
    })
    assert u.total_buddies == 1
    assert u.buddies[0].name == "bob"
    assert u.total_guilds == 1


def test_user_add_buddy():
    u = User.model_validate(MINIMAL_USER)
    u.add_buddy({"id": 3, "name": "carol"})
    assert u.total_buddies == 1
    assert u.buddies[0].name == "carol"


def test_user_add_top_item():
    u = User.model_validate(MINIMAL_USER)
    u.add_top_item({"id": 5, "name": "Agricola"})
    assert len(u.top10) == 1


def test_user_missing_id_raises():
    with pytest.raises(ValidationError):
        User.model_validate({"name": "alice"})
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_user_model.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/user.py`**

```python
from __future__ import annotations

import datetime
import logging
from typing import Any

from pydantic import Field, model_validator

from .things import Thing


class User(Thing):
    firstname: str | None = None
    lastname: str | None = None
    avatar: str | None = Field(None, alias="avatarlink")
    last_login: datetime.datetime | None = Field(None, alias="lastlogin")
    state: str | None = Field(None, alias="stateorprovince")
    country: str | None = None
    homepage: str | None = Field(None, alias="webaddress")
    xbox_account: str | None = Field(None, alias="xboxaccount")
    wii_account: str | None = Field(None, alias="wiiaccount")
    steam_account: str | None = Field(None, alias="steam_account")
    psn_account: str | None = Field(None, alias="psnaccount")
    trade_rating: str | None = None
    buddies: list[Thing] = Field(default_factory=list)
    guilds: list[Thing] = Field(default_factory=list)
    hot: list[Thing] = Field(default_factory=list)
    top: list[Thing] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _ensure_lists(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for field in ["buddies", "guilds", "hot", "top"]:
            data.setdefault(field, [])
        return data

    def __str__(self) -> str:
        return f"User: {self.firstname} {self.lastname}"

    def __repr__(self) -> str:
        return f"User: {self.name} (id: {self.id})"

    def add_buddy(self, data: dict[str, Any]) -> None:
        self.buddies.append(Thing.model_validate(data))

    def add_guild(self, data: dict[str, Any]) -> None:
        self.guilds.append(Thing.model_validate(data))

    def add_top_item(self, data: dict[str, Any]) -> None:
        self.top.append(Thing.model_validate(data))

    def add_hot_item(self, data: dict[str, Any]) -> None:
        self.hot.append(Thing.model_validate(data))

    @property
    def total_buddies(self) -> int:
        return len(self.buddies)

    @property
    def total_guilds(self) -> int:
        return len(self.guilds)

    @property
    def top10(self) -> list[Thing]:
        return self.top

    @property
    def hot10(self) -> list[Thing]:
        return self.hot

    def _format(self, log: logging.Logger) -> None:
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
        log.info("user has {} buddies{}".format(
            self.total_buddies,
            " (forever alone :'( )" if self.total_buddies == 0 else "",
        ))
        for b in self.buddies:
            log.info(f"- {b.name}")
        log.info(f"user is member in {self.total_guilds} guilds")
        for g in self.guilds:
            log.info(f"- {g.name}")
        log.info("top10 items")
        for i in self.top10:
            log.info(f"- {i.name} (id: {i.id})")
        log.info("hot10 items")
        for i in self.hot10:
            log.info(f"- {i.name} (id: {i.id})")
```

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_user.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/user.py tests/test_user_model.py
git commit -m "feat: migrate User to pydantic"
```

---

## Task 6: Migrate `plays.py`

**Files:**
- Modify: `boardgamegeek/objects/plays.py`

Five classes: `PlaysessionPlayer`, `PlaySession`, `Plays`, `UserPlays`, `GamePlays`. `PlaySession` parses dates and wraps players. `Plays` wraps a list of `PlaySession`. `UserPlays`/`GamePlays` are subclasses that add `add_play` mutation.

- [ ] **Step 1: Write failing test**

Add `tests/test_plays_models.py`:

```python
import datetime
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.plays import (
    GamePlays, PlaysessionPlayer, PlaySession, UserPlays,
)


def test_playsession_player():
    p = PlaysessionPlayer.model_validate({
        "username": "alice", "user_id": 42, "score": "100", "win": "1",
    })
    assert p.username == "alice"
    assert p.user_id == 42


def test_playsession_date_parsing():
    ps = PlaySession.model_validate({
        "id": 1, "date": "2023-05-15", "quantity": 1, "duration": 90,
        "game_id": 100, "game_name": "Chess",
    })
    assert isinstance(ps.date, datetime.datetime)
    assert ps.date.year == 2023


def test_playsession_missing_id_raises():
    with pytest.raises(ValidationError):
        PlaySession.model_validate({"date": "2023-01-01"})


def test_user_plays_add_play():
    up = UserPlays.model_validate({"username": "alice", "user_id": 1, "plays_count": 0})
    up.add_play({"id": 10, "game_id": 5, "game_name": "Chess"})
    assert len(up.plays) == 1
    assert up.plays[0].user_id == 1


def test_game_plays_add_play():
    gp = GamePlays.model_validate({"game_id": 5, "plays_count": 0})
    gp.add_play({"id": 11, "game_id": 5, "game_name": "Chess"})
    assert len(gp.plays) == 1
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plays_models.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/plays.py`**

```python
from __future__ import annotations

import datetime
import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from boardgamegeek.exceptions import BGGError


class PlaysessionPlayer(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    username: str | None = None
    user_id: int | None = None
    name: str | None = None
    startposition: str | None = None
    new: str | None = None
    win: str | None = None
    rating: str | None = None
    score: str | None = None
    color: str | None = None

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class PlaySession(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: int
    user_id: int | None = None
    date: datetime.datetime | None = None
    quantity: int | None = None
    duration: int | None = None
    incomplete: bool = False
    nowinstats: int | None = None
    location: str | None = None
    game_id: int | None = None
    game_name: str | None = None
    comment: str | None = None
    players: list[PlaysessionPlayer] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _parse_date(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "date" in data and not isinstance(data["date"], datetime.datetime):
            try:
                data["date"] = datetime.datetime.strptime(data["date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                data["date"] = None
        return data

    def _format(self, log: logging.Logger) -> None:
        log.info(f"play id         : {self.id}")
        log.info(f"play user id    : {self.user_id}")
        if self.date:
            try:
                log.info("play date       : {}".format(self.date.strftime("%Y-%m-%d")))
            except ValueError:
                pass
        log.info(f"play quantity   : {self.quantity}")
        log.info(f"play duration   : {self.duration}")
        log.info(f"play incomplete : {self.incomplete}")
        log.info(f"play nowinstats : {self.nowinstats}")
        log.info(f"play game       : {self.game_name} ({self.game_id})")
        log.info(f"play comment    : {self.comment}")
        if self.players:
            log.info("players")
            for player in self.players:
                log.info(f"\t{player.username} ({player.user_id}): name: {player.name}, score: {player.score}")

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class Plays(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    plays_count: int = 0
    plays: list[PlaySession] = Field(default_factory=list)

    def __getitem__(self, item: int) -> PlaySession:
        return self.plays[item]

    def __len__(self) -> int:
        return len(self.plays)

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class UserPlays(Plays):
    username: str | None = None
    user_id: int | None = None

    @property
    def user(self) -> str | None:
        return self.username

    def add_play(self, data: dict[str, Any]) -> None:
        from copy import copy
        kw = copy(data)
        kw["user_id"] = self.user_id
        self.plays.append(PlaySession.model_validate(kw))

    def _format(self, log: logging.Logger) -> None:
        log.info(f"plays of        : {self.user} ({self.user_id})")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")


class GamePlays(Plays):
    game_id: int | None = None

    def add_play(self, data: dict[str, Any]) -> None:
        self.plays.append(PlaySession.model_validate(data))

    def _format(self, log: logging.Logger) -> None:
        log.info(f"plays of game id: {self.game_id}")
        log.info(f"count           : {len(self)}")
        for p in self.plays:
            p._format(log)
            log.info("")
```

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_plays.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/plays.py tests/test_plays_models.py
git commit -m "feat: migrate play session models to pydantic"
```

---

## Task 7: Migrate `collection.py` — `Collection`

**Files:**
- Modify: `boardgamegeek/objects/collection.py`

`Collection` is a container that wraps a list of `CollectionBoardGame`. It deduplicates by game ID and exposes `add_game` for the loader.

- [ ] **Step 1: Write failing test**

Add `tests/test_collection_model.py`:

```python
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.collection import Collection


MINIMAL_STATS = {
    "usersrated": 0, "average": 0.0, "bayesaverage": 0.0,
    "stddev": 0.0, "median": 0.0, "owned": 0, "trading": 0,
    "wanting": 0, "wishing": 0, "numcomments": 0, "numweights": 0,
    "averageweight": 0.0, "ranks": [],
}

GAME_DATA = {
    "id": 1, "name": "Agricola", "stats": MINIMAL_STATS,
}


def test_collection_add_game():
    c = Collection.model_validate({"owner": "alice"})
    c.add_game(GAME_DATA)
    assert len(c) == 1
    assert c[0].name == "Agricola"


def test_collection_deduplicates_by_id():
    c = Collection.model_validate({"owner": "alice"})
    c.add_game(GAME_DATA)
    c.add_game(GAME_DATA)  # same id
    assert len(c) == 1


def test_collection_owner():
    c = Collection.model_validate({"owner": "bob"})
    assert c.owner == "bob"


def test_collection_iter():
    c = Collection.model_validate({"owner": "alice"})
    c.add_game(GAME_DATA)
    items = list(c)
    assert len(items) == 1
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_collection_model.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/collection.py`**

```python
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ..exceptions import BGGError
from .games import CollectionBoardGame


class Collection(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    owner: str | None = None
    items: list[CollectionBoardGame] = Field(default_factory=list)

    _game_ids: set[int] = PrivateAttr(default_factory=set)

    def model_post_init(self, __context: Any) -> None:
        self._game_ids = {item.id for item in self.items}

    def add_game(self, game: dict[str, Any]) -> None:
        try:
            if game["id"] not in self._game_ids:
                self._game_ids.add(game["id"])
                self.items.append(CollectionBoardGame.model_validate(game))
        except KeyError:
            raise BGGError("invalid game data")

    def __getitem__(self, item: int) -> CollectionBoardGame:
        return self.items[item]

    def __str__(self) -> str:
        return f"{self.owner}'s collection, {len(self)} items"

    def __repr__(self) -> str:
        return f"Collection: (owner: {self.owner}, items: {len(self)})"

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Generator[CollectionBoardGame]:
        yield from self.items

    def _format(self, log: logging.Logger) -> None:
        log.info(f"owner    : {self.owner}")
        log.info(f"size     : {len(self)} items")
        log.info("items")
        for i in self:
            i._format(log)
            log.info("")

    def data(self) -> dict[str, Any]:
        return self.model_dump()
```

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_collection.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/collection.py tests/test_collection_model.py
git commit -m "feat: migrate Collection to pydantic"
```

---

## Task 8: Migrate `hotitems.py` — `HotItem`, `HotItems`

**Files:**
- Modify: `boardgamegeek/objects/hotitems.py`

`HotItem` extends `Thing` with `rank`, `year`, `thumbnail`. `HotItems` is a container with `add_hot_item`. Current `HotItems.__iter__` creates new `HotItem` instances from `self._data["items"]` on each iteration — this should be fixed to iterate `self.items` directly.

- [ ] **Step 1: Write failing test**

Add `tests/test_hotitems_model.py`:

```python
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.hotitems import HotItem, HotItems


def test_hot_item():
    item = HotItem.model_validate({
        "id": 1, "name": "Ark Nova", "rank": 1,
        "thumbnail": "//cf.geekdo-images.com/pic.jpg",
        "yearpublished": 2021,
    })
    assert item.rank == 1
    assert item.thumbnail.startswith("http://")
    assert item.year == 2021


def test_hot_item_missing_rank_raises():
    with pytest.raises(ValidationError):
        HotItem.model_validate({"id": 1, "name": "X"})


def test_hot_items_add():
    hi = HotItems.model_validate({"items": []})
    hi.add_hot_item({"id": 1, "name": "Ark Nova", "rank": 1})
    assert len(hi) == 1
    assert hi[0].rank == 1


def test_hot_items_iter():
    hi = HotItems.model_validate({
        "items": [
            {"id": 1, "name": "A", "rank": 1},
            {"id": 2, "name": "B", "rank": 2},
        ]
    })
    names = [item.name for item in hi]
    assert names == ["A", "B"]
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_hotitems_model.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/hotitems.py`**

```python
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from pydantic import Field, model_validator

from .things import Thing
from ..exceptions import BGGError
from ..utils import fix_url


class HotItem(Thing):
    rank: int
    year: int | None = Field(None, alias="yearpublished")
    thumbnail: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _fix_thumbnail(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "thumbnail" in data:
            data["thumbnail"] = fix_url(data["thumbnail"])
        return data

    def __repr__(self) -> str:
        return f"HotItem (id: {self.id})"

    def _format(self, log: logging.Logger) -> None:
        log.info(f"hot item id        : {self.id}")
        log.info(f"hot item name      : {self.name}")
        log.info(f"hot item rank      : {self.rank}")
        log.info(f"hot item published : {self.year}")
        log.info(f"hot item thumbnail : {self.thumbnail}")


class HotItems(Thing):
    items: list[HotItem] = Field(default_factory=list)

    def add_hot_item(self, data: dict[str, Any]) -> None:
        self.items.append(HotItem.model_validate(data))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Generator[HotItem]:
        yield from self.items

    def __getitem__(self, item: int) -> HotItem:
        return self.items[item]

    def data(self) -> dict[str, Any]:
        return self.model_dump()
```

> Note: `HotItems` previously extended `DictObject` (not `Thing`). Check if the loader or tests pass `id`/`name` when constructing `HotItems`. If not, change the base class to `BaseModel` with `model_config = ConfigDict(populate_by_name=True, extra="allow")` and add `id: int = 0` and `name: str = ""` as optional fields, or keep `HotItems(BaseModel)`.

Check the hot items loader:

```bash
grep -n "HotItems(" boardgamegeek/loaders/hotitems.py
```

If `HotItems` is constructed without `id`/`name`, use `BaseModel` as the base. If it gets `id`/`name`, use `Thing`.

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_hot_items.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/hotitems.py tests/test_hotitems_model.py
git commit -m "feat: migrate HotItem, HotItems to pydantic"
```

---

## Task 9: Migrate `geeklist.py`

**Files:**
- Modify: `boardgamegeek/objects/geeklist.py`

Four classes: `GeekListComment`, `GeekList`, `GeekListItem`, `GeekListObject`. Several use implicit `extra="allow"` access (e.g., `geeklist_comment.thumbs`, `geeklist_item.body`). Mutation methods: `GeekList.add_comment`, `GeekList.add_item`, `GeekListItem.set_object`, `GeekListItem.add_comment`.

- [ ] **Step 1: Write failing test**

Add `tests/test_geeklist_model.py`:

```python
import pytest

from boardgamegeek.objects.geeklist import GeekList, GeekListComment, GeekListItem, GeekListObject


def test_geeklist_comment_extra_fields():
    c = GeekListComment.model_validate({
        "username": "alice", "date": "2023-01-01",
        "thumbs": 5, "text": "Great list!",
    })
    assert c.username == "alice"
    assert c.thumbs == 5  # extra field accessible


def test_geeklist_add_item_and_comment():
    gl = GeekList.model_validate({"id": 1, "name": "My List"})
    item = gl.add_item({"id": 10, "username": "alice", "body": "Nice game"})
    assert len(gl.items) == 1
    assert item.description == "Nice game"
    item.set_object({"id": 99, "name": "Agricola"})
    assert item.object.id == 99
    item.add_comment({"username": "bob", "text": "Agree!"})
    assert len(item.comments) == 1


def test_geeklist_iter():
    gl = GeekList.model_validate({"id": 1, "name": "My List"})
    gl.add_item({"id": 10, "username": "alice"})
    gl.add_item({"id": 11, "username": "bob"})
    assert len(list(gl)) == 2
    assert len(gl) == 2
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_geeklist_model.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/geeklist.py`**

```python
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..utils import DictObject  # noqa: F401  keep for any remaining callers
from ..exceptions import BGGError
from .things import Thing


class GeekListComment(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def __repr__(self) -> str:
        return f"GeekListComment (on {self.date} by [{self.username}])"  # type: ignore[attr-defined]

    def _format(self, log: logging.Logger) -> None:
        log.info(f"  date         : {self.date}")           # type: ignore[attr-defined]
        log.info(f"  username     : {self.username}")       # type: ignore[attr-defined]
        log.info(f"  postdate     : {self.postdate}")       # type: ignore[attr-defined]
        log.info(f"  editdate     : {self.editdate}")       # type: ignore[attr-defined]
        log.info(f"  thumbs count : {self.thumbs}")         # type: ignore[attr-defined]
        log.info(f"  text         : {self.text}")           # type: ignore[attr-defined]

    def data(self) -> dict[str, Any]:
        return self.model_dump()


class GeekListObject(Thing):
    def __repr__(self) -> str:
        return f"GeekListItem (id: {self.id})"

    def _format(self, log: logging.Logger) -> None:
        log.info(f"id      : {self.id}")
        log.info(f"name    : {self.name}")
        log.info(f"imageid : {self.imageid}")    # type: ignore[attr-defined]
        log.info(f"type    : {self.type}")        # type: ignore[attr-defined]
        log.info(f"subtype : {self.subtype}")     # type: ignore[attr-defined]


class GeekListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    comments: list[GeekListComment] = Field(default_factory=list)
    _object: GeekListObject | None = None  # set via set_object()

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
        return str(self.body)  # type: ignore[attr-defined]  body is an extra field

    def _format(self, log: logging.Logger) -> None:
        log.info(f"id                 : {self.id}")          # type: ignore[attr-defined]
        log.info(f"username           : {self.username}")    # type: ignore[attr-defined]
        log.info("object")
        self.object._format(log)
        log.info(f"posted at          : {self.postdate}")    # type: ignore[attr-defined]
        log.info(f"edited at          : {self.editdate}")    # type: ignore[attr-defined]
        log.info(f"thumbs count       : {self.thumbs}")      # type: ignore[attr-defined]
        log.info(f"body (description) : {self.body}")        # type: ignore[attr-defined]
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

    def __iter__(self) -> Generator[GeekListItem]:
        yield from self.items

    @property
    def title(self) -> str:
        return self.name

    def _format(self, log: logging.Logger) -> None:
        log.info(f"geeklist id           : {self.id}")
        log.info(f"geeklist name (title) : {self.name}")
        log.info(f"geeklist posted at    : {self.postdate}")    # type: ignore[attr-defined]
        log.info(f"geeklist edited at    : {self.editdate}")    # type: ignore[attr-defined]
        log.info(f"geeklist thumbs count : {self.thumbs}")      # type: ignore[attr-defined]
        log.info(f"geeklist numitems     : {self.numitems}")    # type: ignore[attr-defined]
        log.info(f"geeklist description  : {self.description}") # type: ignore[attr-defined]
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
```

> Note: `GeekListItem._object` is a plain Python attribute (not a Pydantic field) since it's set post-construction via `set_object()`. This is a `PrivateAttr`-less pattern — fine for a private mutable state that doesn't need validation.

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_geeklist.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/geeklist.py tests/test_geeklist_model.py
git commit -m "feat: migrate GeekList models to pydantic"
```

---

## Task 10: Migrate `search.py` — `SearchResult`

**Files:**
- Modify: `boardgamegeek/objects/search.py`

`SearchResult` extends `Thing` with `type` and `year`. The year is fixed for unsigned negatives in the constructor — this moves to a `@model_validator`.

- [ ] **Step 1: Write failing test**

Add `tests/test_search_model.py`:

```python
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.search import SearchResult


def test_search_result_basic():
    r = SearchResult.model_validate({"id": 1, "name": "Agricola", "type": "boardgame", "yearpublished": 2007})
    assert r.id == 1
    assert r.type == "boardgame"
    assert r.year == 2007


def test_search_result_negative_year_fix():
    # BGG API returns years like BC 3000 as huge unsigned ints
    unsigned_neg = 0x100000000 - 3000  # -3000 as uint32
    r = SearchResult.model_validate({"id": 1, "name": "Ancient", "type": "boardgame", "yearpublished": unsigned_neg})
    assert r.year == -3000


def test_search_result_missing_id_raises():
    with pytest.raises(ValidationError):
        SearchResult.model_validate({"name": "X", "type": "boardgame"})
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_search_model.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `boardgamegeek/objects/search.py`**

```python
from __future__ import annotations

import logging
from typing import Any

from pydantic import Field, model_validator

from boardgamegeek.objects.things import Thing
from boardgamegeek.utils import fix_unsigned_negative


class SearchResult(Thing):
    type: str
    year: int | None = Field(None, alias="yearpublished")

    @model_validator(mode="before")
    @classmethod
    def _fix_year(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "yearpublished" in data and data["yearpublished"] is not None:
            try:
                data["yearpublished"] = fix_unsigned_negative(int(data["yearpublished"]))
            except (ValueError, TypeError):
                data["yearpublished"] = None
        return data

    def _format(self, log: logging.Logger) -> None:
        log.info(f"searched item id   : {self.id}")
        log.info(f"searched item name : {self.name}")
        log.info(f"searched item type : {self.type}")
        log.info(f"searched item year : {self.year}")
```

- [ ] **Step 4: Run all tests**

```bash
pytest -x -q
```

Expected: all pass including `tests/test_search.py`.

- [ ] **Step 5: Commit**

```bash
git add boardgamegeek/objects/search.py tests/test_search_model.py
git commit -m "feat: migrate SearchResult to pydantic"
```

---

## Task 11: Remove `DictObject` from `utils.py`

**Files:**
- Modify: `boardgamegeek/utils.py`
- Modify: `boardgamegeek/objects/__init__.py` (if it re-exports `DictObject`)

`DictObject` is now unused since all objects extend `BaseModel` or `Thing`. Remove it, keeping the rest of the utilities in `utils.py` unchanged.

- [ ] **Step 1: Verify nothing still imports DictObject**

```bash
grep -rn "DictObject" boardgamegeek/ tests/
```

Expected: no results (or only the `geeklist.py` noqa import comment from Task 9 — remove that too).

- [ ] **Step 2: Remove `DictObject` class from `boardgamegeek/utils.py`**

Delete the `DictObject` class (lines ~93–115 in the original):

```python
# DELETE these lines entirely:
class DictObject:
    """
    Just a fancy wrapper over a dictionary
    """

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, item: str) -> Any:
        try:
            return self._data[item]
        except Exception:
            raise AttributeError

    def data(self) -> dict[str, Any]:
        return self._data
```

- [ ] **Step 3: Remove `DictObject` import from `geeklist.py`**

In `boardgamegeek/objects/geeklist.py`, remove the `from ..utils import DictObject` line added in Task 9.

- [ ] **Step 4: Run full test suite**

```bash
pytest -x -q
```

Expected: all pass.

- [ ] **Step 5: Run mypy**

```bash
uv run mypy boardgamegeek/
```

Review and fix any type errors introduced. Common issues:
- `extra="allow"` fields accessed without explicit type declarations show up as `Any` — acceptable.
- `_object` attribute on `GeekListItem` may need a `PrivateAttr` or explicit annotation.

- [ ] **Step 6: Commit**

```bash
git add boardgamegeek/utils.py boardgamegeek/objects/geeklist.py
git commit -m "refactor: remove DictObject, all models now use pydantic BaseModel"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] `DictObject` replaced by `BaseModel` with `extra="allow"`
- [x] `Thing` migrated (Task 2)
- [x] All 8 game models migrated (Tasks 3-4)
- [x] `User` migrated (Task 5)
- [x] Play session models migrated (Task 6)
- [x] `Collection` migrated (Task 7)
- [x] `HotItem`/`HotItems` migrated (Task 8)
- [x] GeeKlist models migrated (Task 9)
- [x] `SearchResult` migrated (Task 10)
- [x] `DictObject` removed (Task 11)
- [x] `data()` backward-compat kept on all models
- [x] Mutation methods (`add_expansion`, `add_play`, etc.) updated to use model fields
- [x] Dedup sets become `PrivateAttr`
- [x] Boolean XML fields ("0"/"1") coerced correctly
- [x] URL-fixing logic preserved via `@model_validator(mode='before')`
- [x] Date-parsing logic preserved via `@model_validator(mode='before')`

**Placeholder scan:** None found — all steps have concrete code.

**Type consistency:**
- `Thing.model_validate(data)` used consistently (not `Thing(data)`)
- `BoardGameComment.model_validate(data)` matches its definition
- `BoardGameStats.bgg_rank` matches the field name used in `BaseGame.bgg_rank` delegation
