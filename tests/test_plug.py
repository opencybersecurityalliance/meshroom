import pytest
from meshroom.model import Integration, Plug, get_plug, list_integrations, list_plugs, plug, set_project_dir, unplug


def test_plug():
    set_project_dir("tests/fixtures/project1")

    # otherproduct -[stuff]-> myproduct (pull mode, generic, no setup hook)
    assert list_integrations("otherproduct", "myproduct", "stuff") == [
        Integration(
            product="otherproduct",
            target_product="myproduct",
            topic="stuff",
            role="producer",
            mode="pull",
            format="json",
            is_generic=True,
        )
    ]
    assert not list_integrations("otherproduct", "myproduct", "stuff")[0].owns_both
    assert not list_integrations("otherproduct", "myproduct", "stuff")[0].owns_self

    # myproduct <-[stuff]- otherproduct (pull mode, generic, setup hook has owns_both=True)
    assert list_integrations("myproduct", "otherproduct", "stuff") == [
        Integration(
            product="myproduct",
            target_product="otherproduct",
            topic="stuff",
            role="consumer",
            mode="pull",
            format="json",
            is_generic=True,
        )
    ]
    assert list_integrations("myproduct", "otherproduct", "stuff")[0].owns_both
    assert not list_integrations("myproduct", "otherproduct", "stuff")[0].owns_self

    # Cleanup any existing plug
    try:
        unplug("stuff", "otherproduct", "myproduct", "pull")
    except ValueError:
        ...

    # Shouldn't be able to plug without a setup hook
    with pytest.raises(ValueError, match="couldn't find any @setup hook"):
        plug("stuff", "otherproduct", "myproduct", "pull", "json", owner="otherproduct")

    p = plug("stuff", "otherproduct", "myproduct", "pull", "json")

    assert p == Plug(
        topic="stuff",
        src_instance="otherproduct",
        dst_instance="myproduct",
        mode="pull",
        format="json",
        owner=None,
    )

    # Check matching integrations
    a, b = p.get_matching_integrations()
    assert a, b == (
        Integration(
            product="otherproduct", target_product="myproduct", topic="stuff", role="producer", mode="pull", format="json", documentation_url="", settings=[], description="", is_generic=True
        ),
        Integration(
            product="myproduct", target_product="otherproduct", topic="stuff", role="consumer", mode="pull", format="json", documentation_url="", settings=[], description="", is_generic=True
        ),
    )

    # Check that the integrations correctly owning
    assert not a.owns_both
    assert not a.owns_self
    assert b.owns_both
    assert not b.owns_self
    assert list(list_plugs()) == [p]

    assert get_plug("stuff", "otherproduct", "myproduct", "pull") == p

    assert list(list_plugs("otherproduct", "myproduct")) == [p]
    assert list(list_plugs(topic="stuff")) == [p]

    # Replug should be nop
    plug("stuff", "otherproduct", "myproduct", "pull", "json")
    assert list(list_plugs()) == [p]

    unplug("stuff", "otherproduct", "myproduct", "pull")

    # After unplug, there should be no plugs
    with pytest.raises(ValueError):
        get_plug("stuff", "otherproduct", "myproduct", "pull")
