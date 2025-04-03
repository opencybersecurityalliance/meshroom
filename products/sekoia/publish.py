import shutil
from uuid import uuid4
from meshroom.model import Integration
from meshroom.decorators import publish


@publish(role="consumer", topic="events")
def publish_intake_format(integration: Integration):
    """
    Publish an intake format as a PR to Sekoia.io's https://github.com/SEKOIA-IO/intake-formats opensource repo

    The integration is required to point to a github fork of the intake format's repo.
    If not, the user will be prompted to provide a valid fork URL.

    We proceed by cloning the intake-formats repo to a tmp_path, copying the intake format files to it and pushing to a branch
    """
    from meshroom.git import Git
    from meshroom.template import generate_files_from_template
    from meshroom import interaction

    REPO = "https://github.com/SEKOIA-IO/intake-formats"

    name = integration.target_product
    module_name = name

    # Prompt the user to provide a github fork URL if not already set
    fork_url = integration.get_or_prompt(
        "intake_formats_fork_url",
        f"Please provide a github.com fork URL of {REPO}\n(open a browser to {REPO}/fork to create one)",
    )

    path = integration.path.parent / "dist" / "formats" / name
    tmp_path = integration.path.parent / "dist" / f"tmp-{uuid4()}"

    # Clone the fork to tmp_path and create a new branch
    Git(tmp_path).pull(fork_url)
    Git(tmp_path).create_branch(f"intake-format-{name}")

    # Scaffold a dummy module from templates/intake_format_module
    generate_files_from_template(
        integration.get_product().path / "templates/intake_format_module",
        tmp_path / module_name,
        {
            "{{UUID}}": integration.intake_format_uuid,
            "{{NAME}}": name,
        },
    )

    # Copy intake-format files
    for d in ("_meta", "ingest"):
        if (path / d).exists():
            shutil.copytree(path / d, tmp_path / module_name / name / d)

    # Push the changes to the remote branch
    Git(tmp_path).add(".")
    Git(tmp_path).commit(f"Publish {name} intake format")
    Git(tmp_path).push(False, remote="origin", force=True)

    # Propose to create a PR from the fork to SEKOIA-IO/intake-formats
    pr_source = Git(tmp_path).get_remote().split(":")[-1].split(".git")[0].split("/")[0]
    interaction.box(
        "Open a browser to",
        f"{REPO}/compare/main...{pr_source}:{Git(tmp_path).get_branch()}?expand=1",
        "To create a PR to SEKOIA-IO/intake-formats",
    )

    # Clean up tmp_path
    shutil.rmtree(tmp_path)

    # Pull intakes also involve an automation connector, let's publish a PR for it too
    if integration.mode == "pull":
        publish_automation_connector(integration)


def publish_automation_connector(integration: Integration):
    """Publish an automation connector as a PR to Sekoia.io's https://github.com/SEKOIA-IO/automation-library"""
    from meshroom.git import Git
    from meshroom import interaction

    REPO = "https://github.com/SEKOIA-IO/automation-library"

    name = integration.target_product

    # Prompt the user to provide a github fork URL if not already set
    fork_url = integration.get_or_prompt(
        "automation_library_fork_url",
        f"Please provide a github.com fork URL of {REPO}\n(open a browser to {REPO}/fork to create one)",
    )

    path = integration.path.parent / "dist" / "formats" / name
    tmp_path = integration.path.parent / "dist" / f"tmp-{uuid4()}"

    # Clone the fork to tmp_path and create a new branch
    Git(tmp_path).pull(fork_url)
    Git(tmp_path).create_branch(f"connector-{name}")

    # Copy connector files
    shutil.copytree(path, tmp_path / name)

    # Remove unrelated files
    for f in ("_meta", "ingest"):
        shutil.rmtree(tmp_path / name / f, ignore_errors=True)

    # Push the changes to the remote branch
    Git(tmp_path).add(".")
    Git(tmp_path).commit(f"Publish {name} connector")
    Git(tmp_path).push(False, remote="origin", force=True)

    # Propose to create a PR from the fork to SEKOIA-IO/automation-library
    pr_source = Git(tmp_path).get_remote().split(":")[-1].split(".git")[0].split("/")[0]
    interaction.box(
        "Open a browser to",
        f"{REPO}/compare/main...{pr_source}:{Git(tmp_path).get_branch()}?expand=1",
        "To create a PR to SEKOIA-IO/automation-library",
    )

    # Clean up tmp_path
    shutil.rmtree(tmp_path)


@publish(role="trigger")
def publish_automation_action(integration: Integration):
    """Publish an automation action as a PR to Sekoia.io's https://github.com/SEKOIA-IO/automation-library"""
    from meshroom.git import Git
    from meshroom import interaction

    REPO = "https://github.com/SEKOIA-IO/automation-library"

    name = integration.target_product

    # Prompt the user to provide a github fork URL if not already set
    fork_url = integration.get_or_prompt(
        "automation_library_fork_url",
        f"Please provide a github.com fork URL of {REPO}\n(open a browser to {REPO}/fork to create one)",
    )

    path = integration.path.parent / "dist" / "automations" / name
    tmp_path = integration.path.parent / "dist" / f"tmp-{uuid4()}"

    if not path.is_dir():
        raise FileNotFoundError(f"Automation action {path} does not exist")

    # Clone the fork to tmp_path and create a new branch
    Git(tmp_path).pull(fork_url)
    Git(tmp_path).create_branch(f"automation-{name}")

    # Copy automation action files
    shutil.copytree(path, tmp_path / name)

    # Remove unrelated files
    for f in ("_meta", "ingest"):
        shutil.rmtree(tmp_path / name / f, ignore_errors=True)

    # Push the changes to the remote branch
    Git(tmp_path).add(".")
    Git(tmp_path).commit(f"Publish {name} action")
    Git(tmp_path).push(False, remote="origin", force=True)

    # Propose to create a PR from the fork to SEKOIA-IO/automation-library
    *_, org, _fork = Git(tmp_path).get_remote().split(".git")[0].rsplit("/", 2)
    org = org.split(":")[-1]
    interaction.box(
        "Open a browser to",
        f"{REPO}/compare/main...{org}:{Git(tmp_path).get_branch()}?expand=1",
        "To create a PR to SEKOIA-IO/automation-library",
    )

    # Clean up tmp_path
    shutil.rmtree(tmp_path)
