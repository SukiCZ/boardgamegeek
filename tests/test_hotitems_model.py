import pytest
from pydantic import ValidationError

from boardgamegeek.objects.hotitems import HotItem, HotItems


def test_hot_item():
    item = HotItem.model_validate(
        {
            "id": 1,
            "name": "Ark Nova",
            "rank": 1,
            "thumbnail": "//cf.geekdo-images.com/pic.jpg",
            "yearpublished": 2021,
        }
    )
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
    hi = HotItems.model_validate(
        {
            "items": [
                {"id": 1, "name": "A", "rank": 1},
                {"id": 2, "name": "B", "rank": 2},
            ]
        }
    )
    names = [item.name for item in hi]
    assert names == ["A", "B"]
