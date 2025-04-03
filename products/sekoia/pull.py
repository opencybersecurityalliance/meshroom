import json
from pathlib import Path
import re
from meshroom.model import Integration, Plug, ProductSetting, create_product, get_integration, get_product
from meshroom.utils import overwrite_directory
from meshroom.git import Git
from meshroom.decorators import pull
from meshroom.interaction import info, error
import yaml


@pull(order=0)
def pull_automation_library(path: Path):
    """Pull automation library from Sekoia's public automation-library repo"""
    sekoia = get_product("sekoia")
    path = path / "automation-library"
    Git(path).pull("https://github.com/SEKOIA-IO/automation-library.git")

    # Collect all automation library manifests
    for manifest in path.rglob("manifest.json"):
        module = manifest.parent

        with open(manifest, "r") as file:
            manifest_data = json.load(file)

        product_name = re.sub(r"[-\s]+", "_", manifest_data["slug"]).lower()

        # Lazily create products if needed
        try:
            product = get_product(product_name)
        except ValueError:
            info("Create product", product_name)
            product = create_product(product_name)

            if description := manifest_data.get("description"):
                product.description = description

            product.settings = ProductSetting.from_json_schema(
                manifest_data.get("configuration"),
                force_secret={r"intake_key|secret|password|token"},
            )

            for fmt in ("svg", "png", "jpg"):
                if (module / f"logo.{fmt}").is_file():
                    product.set_logo(module / f"logo.{fmt}")
                    break

            product.save()

        # Copy automation files to the integration folder
        overwrite_directory(module, sekoia.path / "integrations" / product_name / "dist" / "automation")

        for action_file in module.glob("action_*.json"):
            try:
                with open(action_file, "r") as file:
                    action_data = json.load(file)

                action_uuid = action_data.get("uuid")
                action_name = re.sub(rf"^action_({product_name})?_*", "", action_file.stem)

                # Create the Sekoia trigger integration
                i = Integration(product="sekoia", target_product=product_name, topic=action_name, role="trigger")
                i.automation_action_uuid = action_uuid
                i.automation_module_uuid = manifest_data.get("uuid")
                i.save()

                # Create the 3rd-party executor integration
                get_product(product_name).add_capability("executor", action_name)
                info(f"✓ Created integration {i}")
            except Exception as e:
                error(f"Error creating integration for {action_file}: {e}")


def get_automation_module_by_uuid(repo: Path, uuid: str):
    """Get an automation module's path from Sekoia's public automation-library repo given its UUID"""
    repo = repo / "automation-library"
    for manifest in repo.rglob("manifest.json"):
        with open(manifest, "r") as file:
            manifest_data = json.load(file)
            if manifest_data.get("uuid") == uuid:
                return manifest.parent
    return None


def get_automation_connector_by_uuid(repo: Path, module_uuid: str, uuid: str) -> dict | None:
    """Get automation connector from Sekoia's public automation-library repo given its UUID"""
    module = get_automation_module_by_uuid(repo, module_uuid)
    if not module:
        return None
    for manifest in module.rglob("connector_*.json"):
        with open(manifest, "r") as file:
            manifest_data = json.load(file)
            if manifest_data.get("uuid") == uuid:
                return manifest_data
    return None


@pull(order=1)
def pull_intake_formats(path: Path):
    """Pull intake formats from Sekoia's public intakes repo"""
    path = path / "intake-formats"
    Git(path).pull("https://github.com/SEKOIA-IO/intake-formats.git")

    # Collect all intake formats manifests
    for manifest in path.rglob("_meta/manifest.yml"):
        module_manifest = manifest.parent.parent.parent / "_meta" / "manifest.yml"

        # Skip the utils/ folder
        if manifest.is_relative_to(path / "utils"):
            continue

        # Intake manifests are expected to be nested under a module folder
        if not module_manifest.is_file():
            continue

        # Intakes without an ingest parser.yml manifest aren't considered valid
        if not (manifest.parent.parent / "ingest" / "parser.yml").is_file():
            continue

        with open(module_manifest, "r") as file:
            module_manifest_data = yaml.safe_load(file)

        with open(manifest, "r") as file:
            manifest_data = yaml.safe_load(file)
            product_name = re.sub(r"[-\s]+", "_", manifest_data["slug"]).lower()

        uuid = manifest_data.get("uuid")
        automation_connector_uuid = manifest_data.get("automation_connector_uuid")
        automation_module_uuid = manifest_data.get("automation_module_uuid")
        settings = []

        # Map the intake format to the corresponding automation module if any
        # (automation library being the prefered source of truth for the product name)
        # If no automation module is found, the product name is derived from the intake format's slug
        if automation_module_uuid and (automation_module := get_automation_module_by_uuid(path.parent, manifest_data["automation_module_uuid"])):
            with open(automation_module / "manifest.json", "r") as file:
                automation_module_data = json.load(file)
                settings = ProductSetting.from_json_schema(
                    automation_module_data.get("configuration"),
                    force_secret={r"intake_key|password|token|secret"},  # Ensure intake_keys and password/token are stored as secrets
                )

        # Intakes with an automation connector UUID are pull mode
        mode = "pull" if automation_connector_uuid else "push"

        # Lazily create products if needed
        try:
            product = get_product(product_name)
        except ValueError:
            info("Create product", product_name)
            product = create_product(product_name)

            if description := manifest_data.get("description"):
                product.description = description
            if vendor := module_manifest_data.get("name"):
                product.vendor = vendor

            for fmt in ("svg", "png", "jpg"):
                if (manifest.parent / f"logo.{fmt}").is_file():
                    product.set_logo(manifest.parent / f"logo.{fmt}")
                    break

        product.add_capability("producer", mode=mode, topic="events")
        product.save()

        # Copy intake format files to the integration folder
        i = Integration(product="sekoia", target_product=product_name, topic="events", role="consumer", mode=mode)
        overwrite_directory(manifest.parent.parent, i.path / "dist" / "intake-format")

        # Create the Sekoia end of the integration
        i.mode = mode
        i.documentation_url = f"https://docs.sekoia.io/operation_center/integration_catalog/uuid/{uuid}"
        i.intake_format_uuid = uuid

        # Push intakes require manual setup instructions for the 3rd party
        if mode == "push":
            # Create the 3rd-party setup if it doesn't exist yet, linking to Sekoia.io documentation
            if not get_integration(product_name, "sekoia", "events", "producer", mode):
                dst = Integration(product=product_name, target_product="sekoia", topic="events", role="producer", mode=mode)
                dst.documentation_url = f"https://docs.sekoia.io/operation_center/integration_catalog/uuid/{uuid}/#instructions-on-the-3rd-party-solution"
                dst.add_setup_step("Follow syslog forwarding instructions", syslog_forwarding_instructions)
                dst.save()
                info("✓ Created integration", dst)

        if mode == "pull":
            connector = get_automation_connector_by_uuid(path.parent, automation_module_uuid, automation_connector_uuid)
            connector_settings = [
                s
                for s in ProductSetting.from_json_schema(
                    connector.get("arguments") or {},
                    force_secret={r"intake_key|password|token|secret"},  # Ensure intake_keys and passwords/tokens are stored as secrets
                )
                if s.name not in ("intake_key", "intake_server")  # intake_key and intake_server are automatically handled at intake creation
            ]
            i.automation_connector_uuid = automation_connector_uuid
            i.automation_module_uuid = automation_module_uuid
            i.settings = []
            if settings:
                i.settings.append(ProductSetting(name="module_configuration", type="object", properties=settings))
            if connector_settings:
                i.settings.append(ProductSetting(name="connector_configuration", type="object", properties=connector_settings))

        i.save()
        info("✓ Created integration", i)


# 3rd-party setup steps stubs


def syslog_forwarding_instructions(integration: Integration, plug: Plug):
    """Manual setup instructions for the 3rd party to forward syslog events to Sekoia.io"""
    from meshroom import interaction

    interaction.box(
        f"To setup {plug}, please follow {integration.documentation_url}",
        f"You'll be asked for the following intake key : {plug.get_secret('intake_key')}",
        block=True,
    )
    input()

    plug.save()
