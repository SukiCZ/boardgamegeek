import pytest
from pydantic import ValidationError
from boardgamegeek.objects.things import Thing


def test_thing_valid():
    t = Thing.model_validate({"id": "42", "name": "Agricola"})
    assert t.id == 42
    assert t.name == "Agricola"


def test_thing_extra_fields_accessible():
    t = Thing.model_validate({"id": 1, "name": "X", "yearpublished": 2007})
    assert t.yearpublished == 2007


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
