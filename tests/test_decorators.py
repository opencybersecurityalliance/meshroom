from meshroom.decorators import Hook, all_hooks
from meshroom.model import Integration, list_integrations, set_project_dir


def test_setup_decorator():
    all_hooks.clear()  # Ensure the hooks cache is flushed

    set_project_dir("tests/fixtures/project1")
    assert set(list_integrations("myproduct")) == {
        Integration(product="myproduct", target_product="otherproduct", topic="events", role="consumer", mode="push", format="ecs", documentation_url="", settings=[]),
        Integration(product="myproduct", target_product="otherproduct", topic="stuff", role="consumer", mode="pull", format="json", documentation_url="", settings=[]),
    }

    i = list_integrations("myproduct", topic="events")[0]
    assert i.get_hooks() == [
        Hook(
            product="myproduct",
            target_product=None,
            role="consumer",
            topic="events",
            func=i.get_hooks()[0].func,
            mode=None,
            format="ecs",
            keep_when_overloaded=False,
            order=None,
            title="setup_consumer_for_events",
            type="setup",
        ),
    ]

    assert set(Hook.get_all()) == {
        Hook(
            product="myproduct",
            target_product=None,
            role="consumer",
            topic="stuff",
            func=[x.func for x in Hook.get_all() if x.topic == "stuff"][0],
            mode="pull",
            format=None,
            keep_when_overloaded=False,
            order=None,
            title="Make magic happen",
            type="setup",
            owns_both=True,
        ),
        Hook(
            product="myproduct",
            target_product=None,
            role="consumer",
            topic="events",
            func=[x.func for x in Hook.get_all() if x.topic == "events"][0],
            mode=None,
            format="ecs",
            keep_when_overloaded=False,
            order=None,
            title="setup_consumer_for_events",
            type="setup",
        ),
    }
