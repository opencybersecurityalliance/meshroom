import json
from uuid import uuid4
import yaml

from .setup import create_intake_key
from meshroom.model import Integration, Plug, Instance
from meshroom.decorators import scaffold_consumer
from .api import SekoiaAPI


@scaffold_consumer("events")
def scaffold_custom_events_consumer(integration: Integration):
    """Scaffold a new events consumer backed by a custom Sekoia.io intake format"""
    from meshroom.template import generate_files_from_template

    # NOTE: We can't leverage the sekoia automation SDK here since it is Pydantic-v1 based, which conflicts with Meshroom's Pydantic-v2
    #       so let's scaffold module files by ourself from static templates/

    name = integration.target_product
    path = integration.path.parent / "dist" / "formats" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    uuid = str(uuid4())

    # Scaffold setup steps if needed
    python_file = integration.path.with_suffix(".py")
    if not python_file.is_file() or not python_file.read_text():
        # Add required import statements
        python_file.write_text("""
from ...api import SekoiaAPI
import yaml
import json
""")
        # To setup a custom pull intake, we need to push and sync the connector's code via git repo
        if integration.mode == "pull":
            integration.add_setup_step("Push connector to git repo", git_push_automation_module, order=0)
            integration.add_setup_step("Sync connector from git repo", update_playbook_module_from_git, order=1)
            integration.automation_module_uuid = uuid
            integration.automation_connector_uuid = uuid

        # Since the intake format is not part of Sekoia.io catalog, prepend a setup step to
        # create the custom intake format into the Instance
        integration.add_setup_step(f"Create custom intake format '{name}'", create_custom_intake_format, order=2, owns_both=True)

        # Then we can instanciate the actual intake
        integration.add_setup_step(f"Create intake '{name}'", create_intake_key, order=3)

    # Scaffold files from templates/events_consumer when they don't exist
    if integration.mode == "pull":
        example_path = integration.get_product().path / "templates/events_consumer_pull"
    else:
        example_path = integration.get_product().path / "templates/events_consumer"

    generate_files_from_template(
        example_path,
        path,
        {
            "{{UUID}}": uuid,
            "{{NAME}}": name,
        },
    )

    # Update the integration's YAML definition with the new intake format UUID
    if not getattr(integration, "intake_format_uuid", None):
        integration.intake_format_uuid = uuid

    integration.save()


def create_custom_intake_format(integration: Integration, plug: Plug, instance: Instance):
    """A setup hook that setup a custom Sekoia.io intake format from integration's files"""
    from meshroom.interaction import info

    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )
    name = integration.target_product
    path = integration.path.parent / "dist" / "formats" / name

    try:
        # Read the parser definition
        with open(path / "ingest/parser.yml", "r") as f:
            parser = yaml.safe_load(f)
    except FileNotFoundError:
        parser = None

    try:
        # Read the taxonomy
        with open(path / "_meta/fields.yml", "r") as f:
            taxonomy = yaml.safe_load(f) or {}
    except FileNotFoundError:
        taxonomy = {}

    try:
        # Read the smart descriptions
        with open(path / "_meta/smart-descriptions.json", "r") as f:
            smart_descriptions = json.load(f)
    except FileNotFoundError:
        smart_descriptions = None

    # Read the format's manifest
    with open(path / "_meta/manifest.yml", "r") as f:
        manifest = yaml.safe_load(f)
    data_sources = list(manifest.get("data_sources", {}).keys())

    api.create_or_update_custom_intake_format(
        manifest["uuid"],
        name,
        manifest.get("description", ""),
        parser,
        data_sources,
        manifest.get("slug") or name,
        list(taxonomy.values()),
        smart_descriptions,
        logo=(path / "_meta/logo.png"),
        automation_module_uuid=manifest.get("automation_module_uuid") or integration.intake_format_uuid if integration.mode == "pull" else None,
        automation_connector_uuid=manifest.get("automation_connector_uuid") or integration.intake_format_uuid if integration.mode == "pull" else None,
    )
    info(f"✓ Custom intake format {name} successfully pushed")


def git_push_automation_module(integration: Integration):
    """A setup hook that pushes the automation module to a git repo"""
    from meshroom.git import Git
    from meshroom.interaction import log

    name = integration.target_product
    path = integration.path.parent / "dist" / "formats" / name
    if Git(path).push(True, ".", f"Update {name} automation module"):
        log(f"Automation module {name} successfully pushed to git repo")
    else:
        log(f"Automation module {name} is up-to-date in git repo")


def update_playbook_module_from_git(integration: Integration, instance: Instance):
    """A setup hook that syncs an integration's automation module from the git repo"""
    from meshroom.git import Git
    from meshroom.model import get_project_dir
    from uuid import uuid4

    name = integration.target_product
    path = integration.path.parent / "dist" / "formats" / name
    api = SekoiaAPI(
        instance.settings.get("region", "fra1"),
        instance.get_secret("API_KEY"),
    )

    # Trigger a pull of the automation module's code from the git repo
    api.pull_custom_integration(
        Git().get_remote(scheme="https"),
        Git().get_branch(),
        path.relative_to(get_project_dir()).as_posix(),
        str(uuid4()),
    )
