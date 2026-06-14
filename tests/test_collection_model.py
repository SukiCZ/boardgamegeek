from boardgamegeek.objects.collection import Collection

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
GAME_DATA = {"id": 1, "name": "Agricola", "stats": MINIMAL_STATS}


def test_collection_add_game():
    c = Collection.model_validate({"owner": "alice"})
    c.add_game(GAME_DATA)
    assert len(c) == 1
    assert c[0].name == "Agricola"


def test_collection_deduplicates_by_id():
    c = Collection.model_validate({"owner": "alice"})
    c.add_game(GAME_DATA)
    c.add_game(GAME_DATA)
    assert len(c) == 1


def test_collection_owner():
    c = Collection.model_validate({"owner": "bob"})
    assert c.owner == "bob"


def test_collection_iter():
    c = Collection.model_validate({"owner": "alice"})
    c.add_game(GAME_DATA)
    items = list(c)
    assert len(items) == 1
