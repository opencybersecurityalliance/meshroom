from meshroom.model import Capability, get_product, list_products, set_project_dir


def test_list_capabilities():
    set_project_dir("tests/fixtures/project1")
    assert set(get_product("myproduct").list_capabilities("consumer")) == {
        Capability(topic="stuff", role="consumer", mode="pull", format=None),
        Capability(topic="alerts", role="producer", mode="pull", format=None),
        Capability(topic="intelligence", role="producer", mode="pull", format="stix"),
        Capability(topic="detection_rules", role="consumer", mode="push", format="sigma"),
        Capability(topic="events", role="consumer", mode="pull", format="ecs"),
        Capability(topic="events", role="consumer", mode="push", format="ecs"),
    }
    assert set(get_product("myproduct").list_capabilities("producer")) == {
        Capability(topic="detection_rules", role="consumer", mode="push", format="sigma"),
        Capability(topic="alerts", role="producer", mode="pull", format=None),
        Capability(topic="intelligence", role="producer", mode="pull", format="stix"),
    }

    assert {str(x) for x in get_product("myproduct").list_capabilities()} == {
        "alerts producer (pull)",
        "stuff consumer (pull)",
        "events consumer (pull ecs)",
        "intelligence producer (pull stix)",
        "events consumer (ecs)",
        "detection_rules consumer (sigma)",
    }


def test_list_products():
    set_project_dir("tests/fixtures/project1")
    assert {x.name for x in list_products()} == {"myproduct", "otherproduct"}


def test_match_capabilities():
    set_project_dir("tests/fixtures/project1")
    myproduct = get_product("myproduct")
    otherproduct = get_product("otherproduct")
    assert myproduct.list_capabilities("consumer", "stuff")[0].matches(Capability(topic="stuff", role="producer", mode="pull", format="anything"))
    assert myproduct.list_capabilities("consumer", "stuff")[0].matches(otherproduct.list_capabilities("producer", "stuff")[0])
