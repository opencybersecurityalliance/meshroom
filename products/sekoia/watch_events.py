from meshroom.decorators import watch
from .api import SekoiaAPI
from meshroom.model import Plug, Instance


@watch("events")
def watch_events(instance: Instance, plug: Plug | None = None):
    """Watch events received by a Sekoia intake (when plug is provided) or by a whole Sekoia.io community otherwise."""
    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    yield from api.watch_events(plug.settings["intake_uuid"] if plug else None)
