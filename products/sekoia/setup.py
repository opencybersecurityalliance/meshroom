from meshroom.decorators import setup_consumer, teardown_consumer
from meshroom.model import Integration, Plug, Instance
from .api import SekoiaAPI


@setup_consumer("events", order="first", owns_both=True)
def create_intake_key(integration: Integration, plug: Plug, instance: Instance):
    """Create an intake key to consume events"""
    from meshroom.interaction import debug, info

    if intake_key := plug.get_secret("intake_key"):
        debug("🚫 Intake key already exists")
        return intake_key

    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    if not getattr(integration, "intake_format_uuid", None):
        raise ValueError("Intakes can't be created without an intake format, see products/sekoia/templates/event_consumer for inspiration")

    intake_name = integration.target_product.replace("_", " ")

    # Get or create main entity (because we need one to create an intake key)
    entity_uuid = api.get_or_create_main_entity()["uuid"]

    # Pull intakes require an automation connector
    if integration.mode == "pull":
        if not getattr(integration, "automation_module_uuid", None):
            raise ValueError("Pull intakes require a connector, see products/sekoia/templates/event_consumer_pull for inspiration")

        # Find or create a suitable module configuration
        module_configuration = plug.dst_config.get("module_configuration") or {}
        connector_configuration = plug.dst_config.get("connector_configuration") or {}
        module_configuration_uuid = api.get_or_create_module_configuration(
            integration.automation_module_uuid,
            "Meshroom",
            module_configuration,
        )["uuid"]

        # Create the pull intake along with the automation connector
        intake = api.create_intake_key(
            entity_uuid,
            integration.intake_format_uuid,
            intake_name,
            connector_configuration=connector_configuration,
            connector_module_configuration_uuid=module_configuration_uuid,
        )
    else:
        # Create the push intake
        intake = api.create_intake_key(
            entity_uuid,
            integration.intake_format_uuid,
            intake_name,
        )

    # Securely store the intake key
    plug.set_secret("intake_key", intake["intake_key"])
    plug.settings["intake_uuid"] = intake["uuid"]
    plug.save()

    info(f"✓ Intake {intake_name} created")


@teardown_consumer("events")
def delete_intake_key(integration: Integration, plug: Plug, instance: Instance):
    """Delete the intake key when the plug is torn down"""
    from meshroom.interaction import info

    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    intake_name = integration.target_product.replace("_", " ")

    intake_keys = api.get_intake_keys(intake_name, integration.intake_format_uuid)
    for intake_key in intake_keys:
        api.delete_intake_key(intake_key["uuid"])
        info(f"✓ Intake {intake_key['name']} deleted")

    plug.delete_secret("intake_key")
    if plug.settings.get("intake_uuid"):
        del plug.settings["intake_uuid"]
