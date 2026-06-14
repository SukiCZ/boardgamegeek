import pytest
from pydantic import ValidationError

from boardgamegeek.objects.user import User


MINIMAL_USER = {"id": "1", "name": "alice"}


def test_user_basic_fields():
    u = User.model_validate(
        {
            **MINIMAL_USER,
            "firstname": "Alice",
            "lastname": "Smith",
            "avatarlink": "http://example.com/avatar.jpg",
            "stateorprovince": "California",
            "country": "USA",
            "webaddress": "http://alice.com",
        }
    )
    assert u.id == 1
    assert u.name == "alice"
    assert u.firstname == "Alice"
    assert u.avatar == "http://example.com/avatar.jpg"
    assert u.state == "California"
    assert u.homepage == "http://alice.com"


def test_user_buddies_and_guilds():
    u = User.model_validate(
        {
            **MINIMAL_USER,
            "buddies": [{"id": 2, "name": "bob"}],
            "guilds": [{"id": 10, "name": "chess club"}],
        }
    )
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


def test_user_defaults():
    u = User.model_validate(MINIMAL_USER)
    assert u.total_buddies == 0
    assert u.total_guilds == 0
    assert u.avatar is None
