from uuid import uuid4
from meshroom.model import Integration, Instance
from meshroom.decorators import scaffold_trigger
from .api import SekoiaAPI


@scaffold_trigger()
def scaffold_custom_action_trigger(integration: Integration):
    """Scaffold a new action trigger backed by a custom Sekoia.io automation action"""
    from meshroom.template import generate_files_from_template

    # NOTE: We can't leverage the sekoia automation SDK here since it is Pydantic-v1 based, which conflicts with Meshroom's Pydantic-v2
    #       so let's scaffold module files by ourself from static templates/

    name = integration.target_product
    path = integration.path.parent / "dist" / "automations" / name
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
        integration.add_setup_step("Push action to git repo", git_push_automation_module, order=0, owns_both=True)
        integration.add_setup_step("Sync action from git repo", update_playbook_module_from_git, order=1)

    # Scaffold files from templates/action_trigger when they don't exist
    generate_files_from_template(
        integration.get_product().path / "templates/action_trigger",
        path,
        {
            "{{UUID}}": uuid,
            "{{NAME}}": name,
        },
    )

    integration.automation_action_uuid = uuid
    integration.automation_module_uuid = uuid
    integration.save()


def git_push_automation_module(integration: Integration):
    """A setup hook that pushes the automation module to a git repo"""
    from meshroom.git import Git
    from meshroom.interaction import log

    name = integration.target_product
    path = integration.path.parent / "dist" / "automations" / name
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
    path = integration.path.parent / "dist" / "automations" / name
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
