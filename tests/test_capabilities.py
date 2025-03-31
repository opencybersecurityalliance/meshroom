from meshroom.model import Capability, Integration, get_product, list_integrations, set_project_dir


def test_capabilities():
    set_project_dir("tests/fixtures/project1")
    assert set(get_product("myproduct").list_capabilities()) == {
        Capability(topic="stuff", role="consumer", mode="pull", format=None),
        Capability(topic="events", role="consumer", mode="pull", format="ecs"),
        Capability(topic="detection_rules", role="consumer", mode="push", format="sigma"),
        Capability(topic="events", role="consumer", mode="push", format="ecs"),
        Capability(topic="intelligence", role="producer", mode="pull", format="stix"),
        Capability(topic="alerts", role="producer", mode="pull", format=None),
    }

    assert set(get_product("otherproduct").list_capabilities("events")) == {
        Capability(topic="events", role="producer", mode="push", format=None),
        Capability(topic="stuff", role="producer", mode="pull", format="json"),
    }


def test_matching_integrations():
    set_project_dir("tests/fixtures/project1")
    assert set(list_integrations()) == {
        Integration(product="otherproduct", target_product="myproduct", topic="events", role="producer", mode="push", format="ecs"),
        Integration(product="myproduct", target_product="otherproduct", topic="events", role="consumer", mode="push", format="ecs"),
        Integration(product="otherproduct", target_product="myproduct", topic="stuff", role="producer", mode="pull", format="json"),
        Integration(product="myproduct", target_product="otherproduct", topic="stuff", role="consumer", mode="pull", format="json"),
    }

    assert list_integrations("myproduct", topic="stuff") == [
        Integration(product="myproduct", target_product="otherproduct", topic="stuff", role="consumer", mode="pull", format="json"),
    ]

    assert list_integrations("otherproduct", topic="stuff") == [
        Integration(product="otherproduct", target_product="myproduct", topic="stuff", role="producer", mode="pull", format="json"),
    ]
