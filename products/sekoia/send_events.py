import json
from meshroom.decorators import produce
from .api import SekoiaAPI
from meshroom.model import Plug, Instance


@produce("events")
def send_events(
    instance: Instance,
    data: str | bytes | dict,
    plug: Plug | None = None,
):
    """Watch events received by a Sekoia intake (when plug is provided) or by a whole Sekoia.io community otherwise."""
    from meshroom.interaction import log

    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    if isinstance(data, bytes):
        data = data.decode()
    if not isinstance(data, str):
        data = json.dumps(data)
    log(f"Send event to intake {plug.settings['intake_uuid']}:\n\n{data}\n\n")
    return api.send_event_http(plug.get_secret("intake_key"), data)
