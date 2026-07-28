import datetime
import pytest
from pydantic import ValidationError

from boardgamegeek.objects.plays import (
    GamePlays,
    PlaysessionPlayer,
    PlaySession,
    UserPlays,
)


def test_playsession_player():
    p = PlaysessionPlayer.model_validate(
        {
            "username": "alice",
            "user_id": 42,
            "score": "100",
            "win": "1",
        }
    )
    assert p.username == "alice"
    assert p.user_id == 42


def test_playsession_date_parsing():
    ps = PlaySession.model_validate(
        {
            "id": 1,
            "date": "2023-05-15",
            "quantity": 1,
            "duration": 90,
            "game_id": 100,
            "game_name": "Chess",
        }
    )
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


def test_user_plays_user_property():
    up = UserPlays.model_validate({"username": "bob", "user_id": 2})
    assert up.user == "bob"
