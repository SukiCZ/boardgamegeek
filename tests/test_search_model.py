import pytest
from pydantic import ValidationError

from boardgamegeek.objects.search import SearchResult


def test_search_result_basic():
    r = SearchResult.model_validate(
        {
            "id": 1,
            "name": "Agricola",
            "type": "boardgame",
            "yearpublished": 2007,
        }
    )
    assert r.id == 1
    assert r.type == "boardgame"
    assert r.year == 2007


def test_search_result_negative_year_fix():
    unsigned_neg = 0x100000000 - 3000  # -3000 stored as uint32
    r = SearchResult.model_validate(
        {
            "id": 1,
            "name": "Ancient",
            "type": "boardgame",
            "yearpublished": unsigned_neg,
        }
    )
    assert r.year == -3000


def test_search_result_missing_id_raises():
    with pytest.raises(ValidationError):
        SearchResult.model_validate({"name": "X", "type": "boardgame"})


def test_search_result_missing_type_raises():
    with pytest.raises(ValidationError):
        SearchResult.model_validate({"id": 1, "name": "X"})
