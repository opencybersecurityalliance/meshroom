from meshroom.decorators import trigger
from meshroom.model import Integration, Instance


@trigger()
def trigger_action(instance: Instance, integration: Integration, action: str | None = None, data: dict | None = None):
    """A generic Trigger for Sekoia.io playbook action, given its UUID or name"""
    from .api import SekoiaAPI

    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    action_uuid = getattr(integration, "automation_action_uuid", None)

    if not action_uuid:
        if not action:
            raise ValueError("An action name or UUID must be provided")
        action_uuid = api.get_action_uuid(action)

    if not action_uuid:
        raise ValueError(f"No such action {action}")

    return api.trigger_action(action_uuid, data)
