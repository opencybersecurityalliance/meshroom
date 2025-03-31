from meshroom.model import Integration, list_integrations, set_project_dir


def test_list_integrations():
    set_project_dir("tests/fixtures/project1")
    assert set(list_integrations()) == {
        Integration(product="otherproduct", target_product="myproduct", topic="events", role="producer", mode="push", format="ecs", is_generic=True),
        Integration(product="otherproduct", target_product="myproduct", topic="stuff", role="producer", mode="pull", format="json", is_generic=True),
        Integration(product="myproduct", target_product="otherproduct", topic="events", role="consumer", mode="push", format="ecs", is_generic=True),
        Integration(product="myproduct", target_product="otherproduct", topic="stuff", role="consumer", mode="pull", format="json", is_generic=True),
    }

    assert Integration(
        product="myproduct",
        target_product="otherproduct",
        topic="events",
        role="consumer",
        mode="push",
        format="ecs",
        is_generic=True,
    ) in list_integrations("myproduct", "otherproduct")

    assert Integration(
        product="otherproduct",
        target_product="myproduct",
        topic="stuff",
        role="producer",
        mode="pull",
        format="json",
        is_generic=True,
    ) in list_integrations("otherproduct", "myproduct")
