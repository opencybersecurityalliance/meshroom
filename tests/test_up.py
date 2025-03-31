from meshroom.model import Integration, plug, set_project_dir


def test_up():
    set_project_dir("tests/fixtures/project1")
    p = plug("stuff", "otherproduct", "myproduct", "pull", "json")
    assert p.get_consumer() == Integration(
        product="myproduct",
        target_product="otherproduct",
        topic="stuff",
        role="consumer",
        mode="pull",
        format="json",
    )
    assert p.get_producer() == Integration(
        product="otherproduct",
        target_product="myproduct",
        topic="stuff",
        role="producer",
        mode="pull",
        format="json",
    )

    p.up()

    assert p.get_secret("youpi") == "42"

    p.delete()
