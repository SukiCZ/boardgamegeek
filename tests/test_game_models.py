import datetime

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
