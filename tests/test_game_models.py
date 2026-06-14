import datetime

import pytest

from boardgamegeek.objects.games import (
    BaseGame,
    BoardGame,
    BoardGameComment,
    BoardGameRank,
    BoardGameStats,
    BoardGameVersion,
    BoardGameVideo,
    CollectionBoardGame,
    MarketplaceListing,
    PlayerSuggestion,
)


def test_board_game_rank_aliases():
    rank = BoardGameRank.model_validate(
        {
            "id": "1",
            "name": "boardgame",
            "friendlyname": "Board Game Rank",
            "value": "42",
            "bayesaverage": 7.5,
            "type": "subtype",
        }
    )
    assert rank.id == 1
    assert rank.friendly_name == "Board Game Rank"
    assert rank.rating_bayes_average == 7.5
    assert rank.value == "42"
    assert rank.type == "subtype"


def test_board_game_stats_builds_bgg_rank():
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
    assert stats.users_owned == 500
    assert stats.bgg_rank == 5
    assert len(stats.ranks) == 2
    assert stats.ranks[0].friendly_name == "Board Game Rank"


def test_board_game_stats_no_boardgame_rank():
    stats = BoardGameStats.model_validate(
        {"ranks": [{"id": "2", "name": "strategygames", "value": 3, "friendlyname": "X"}]}
    )
    assert stats.bgg_rank is None


def test_player_suggestion_numeric_count_plus():
    ps = PlayerSuggestion.model_validate({"player_count": "4+", "best": 10, "recommended": 5, "not_recommended": 1})
    assert ps.numeric_player_count == 5


def test_player_suggestion_numeric_count_plain():
    ps = PlayerSuggestion.model_validate({"player_count": "4", "best": 10, "recommended": 5, "not_recommended": 1})
    assert ps.numeric_player_count == 4


def test_board_game_comment_alias():
    c = BoardGameComment.model_validate({"username": "alice", "comment": "great game", "rating": 8.5})
    assert c.commenter == "alice"
    assert c.comment == "great game"
    assert c.rating == 8.5


def test_board_game_video_date_parsing():
    vid = BoardGameVideo.model_validate(
        {
            "id": "100",
            "name": "Review",
            "post_date": "2023-05-15T10:00:00+00:00",
            "uploader_id": "999",
        }
    )
    assert vid.id == 100
    assert isinstance(vid.post_date, datetime.datetime)
    assert vid.uploader_id == 999


def test_board_game_video_bad_date():
    vid = BoardGameVideo.model_validate(
        {
            "id": "1",
            "name": "X",
            "post_date": "not-a-date",
            "uploader_id": "1",
        }
    )
    assert vid.post_date is None


def test_board_game_version_url_fix():
    ver = BoardGameVersion.model_validate(
        {
            "id": "1",
            "name": "English Edition",
            "thumbnail": "//cf.geekdo-images.com/pic.jpg",
            "image": "//cf.geekdo-images.com/pic_full.jpg",
            "yearpublished": 2007,
        }
    )
    assert ver.thumbnail.startswith("http://")
    assert ver.year == 2007


def test_marketplace_listing():
    ml = MarketplaceListing.model_validate(
        {
            "list_date": datetime.datetime(2023, 1, 1),
            "price": 19.99,
            "currency": "USD",
            "condition": "good",
        }
    )
    assert ml.price == 19.99
    assert ml.currency == "USD"


MINIMAL_STATS = {
    "usersrated": 0,
    "average": 0.0,
    "bayesaverage": 0.0,
    "stddev": 0.0,
    "median": 0.0,
    "owned": 0,
    "trading": 0,
    "wanting": 0,
    "wishing": 0,
    "numcomments": 0,
    "numweights": 0,
    "averageweight": 0.0,
    "ranks": [],
}


def test_base_game_construction():
    data = {
        "id": 1,
        "name": "Test",
        "stats": MINIMAL_STATS,
        "thumbnail": "//cf.geekdo-images.com/pic.jpg",
        "yearpublished": 2007,
        "minplayers": 2,
        "maxplayers": 4,
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
        "id": 1,
        "name": "Test",
        "stats": MINIMAL_STATS,
        "expansions": [],
        "expands": [],
        "videos": [],
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
    data = {"id": 1, "name": "Test", "stats": MINIMAL_STATS}
    game = BoardGame.model_validate(data)
    game.add_comment({"username": "alice", "comment": "fun!", "rating": 9.0})
    assert len(game.comments) == 1
    assert game.comments[0].commenter == "alice"


def test_board_game_player_suggestions():
    data = {
        "id": 1,
        "name": "Test",
        "stats": MINIMAL_STATS,
        "suggested_players": {
            "total_votes": 100,
            "results": {
                "4": {"best_rating": 80, "recommended_rating": 15, "not_recommended_rating": 5},
            },
        },
    }
    game = BoardGame.model_validate(data)
    assert len(game.player_suggestions) == 1
    assert game.player_suggestions[0].player_count == "4"
    assert game.player_suggestions[0].best == 80


def test_collection_board_game_status_fields():
    data = {
        "id": 1,
        "name": "Test",
        "stats": MINIMAL_STATS,
        "own": "1",
        "prevowned": "0",
        "want": "1",
        "wanttobuy": "0",
        "wanttoplay": "1",
        "fortrade": "0",
        "wishlist": "0",
        "preordered": "1",
    }
    game = CollectionBoardGame.model_validate(data)
    assert game.owned is True
    assert game.prev_owned is False
    assert game.want is True
    assert game.want_to_buy is False
    assert game.preordered is True
