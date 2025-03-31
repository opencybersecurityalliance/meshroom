from meshroom.decorators import trigger
from meshroom.model import Integration, Instance


@trigger("workflow")
def trigger_workflow(instance: Instance, integration: Integration, playbook: str | None = None, data: dict | None = None):
    """Within Sekoia.io, a workflow is a playbook. This triggers a full playbook given its UUID or name."""
    from .api import SekoiaAPI

    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    playbook_uuid = getattr(integration, "automation_playbook_uuid", None)

    if not playbook_uuid:
        if not playbook:
            raise ValueError("An playbook name or UUID must be provided")
        playbook_uuid = api.get_playbook_uuid(playbook)

    if not playbook_uuid:
        raise ValueError(f"No such playbook {playbook}")

    return api.trigger_playbook(playbook_uuid, data)
