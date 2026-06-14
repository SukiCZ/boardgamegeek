from boardgamegeek.objects.geeklist import GeekList, GeekListComment


def test_geeklist_comment_extra_fields():
    c = GeekListComment.model_validate(
        {
            "username": "alice",
            "date": "2023-01-01",
            "thumbs": 5,
            "text": "Great list!",
        }
    )
    assert c.username == "alice"  # type: ignore
    assert c.thumbs == 5  # type: ignore


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


def test_geeklist_title_alias():
    gl = GeekList.model_validate({"id": 1, "name": "Cool List"})
    assert gl.title == "Cool List"
