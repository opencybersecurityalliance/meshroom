from functools import cache, cached_property
import json
import logging
from pathlib import Path
from re import Pattern
import re
import sys
from typing import Any, Callable, Generator, Literal, cast
from pydantic import BaseModel, ConfigDict, field_validator
import yaml
import shutil

from meshroom import interaction, secrets
from meshroom.ast import AST
from meshroom.template import generate_files_from_template
from meshroom.utils import import_module
from meshroom.interaction import debug, info, log, error

Role = Literal["consumer", "producer", "trigger", "executor"]
Mode = Literal["push", "pull"]

TEMPLATES_DIR = Path(__file__).parent / "templates"
PROJECT_DIR = Path(".")


class Model(BaseModel):
    """Base model for all Meshroom models"""

    model_config = ConfigDict(
        json_encoders={
            set: list,
        }
    )

    def model_dump(self, *args, **kw):
        kw["exclude_defaults"] = True
        kw["exclude_none"] = True
        return super().model_dump(*args, **kw)


class Cap(Model):
    format: str | None = None
    mode: Mode = "push"


class Capability(Model):
    """
    Definition of a Product's generic consumer/producer capability
    """

    topic: str | None = None
    role: Role
    mode: Mode = "push"
    format: str | None = None

    def __hash__(self):
        return (self.topic, self.role, self.mode, self.format).__hash__()

    def __eq__(self, value: "Capability"):
        return self.topic == value.topic and self.role == value.role and self.mode == value.mode and self.format == value.format

    def matches(self, capability: "Capability"):
        """Check if this capability matches a complementary capability (e.g., consumer/producer)"""
        return (
            (self.topic == capability.topic or None in (self.topic, capability.topic))
            and (sorted((self.role, capability.role)) in (["consumer", "producer"], ["executor", "trigger"]))
            and self.mode == capability.mode
            and (self.format == capability.format or None in (self.format, capability.format))
        )

    def __str__(self):
        x = []
        if self.mode not in ("push", None):
            x.append(self.mode)
        if self.format is not None:
            x.append(self.format)
        out = f"{self.topic or '-'} {self.role}"
        if x:
            out += f" ({' '.join(x)})"
        return out

    def __repr__(self):
        return str(self)


class Product(Model):
    """
    Definition of a product's capabilities
    :name: The name of the product, which is also the directory name under /products
    :tags: A set of tags that describe the product's functional scopes
    """

    name: str
    description: str = ""
    vendor: str = ""
    tags: set[str] = set()
    settings: list["ProductSetting"] = []
    consumes: dict[str, list[Cap]] = {}
    produces: dict[str, list[Cap]] = {}
    triggers: dict[str, list[Cap]] = {}
    executes: dict[str, list[Cap]] = {}

    model_config = ConfigDict(
        extra="allow",
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[\w\.]+$", v):
            raise ValueError("Invalid product name. Only alphanumeric characters, dots and underscores are allowed.")
        return v

    @staticmethod
    def load(path: Path):
        # Optionally read the definition.yaml file
        path = path_in_project(path)
        definition = {}
        if (path / "definition.yaml").is_file():
            with open(path / "definition.yaml") as f:
                definition = yaml.safe_load(f)
        definition["name"] = path.name
        return Product.model_validate(definition)

    def save(self):
        definition = json.loads(self.model_dump_json(exclude_none=True, exclude_defaults=True))
        self.path.mkdir(parents=True, exist_ok=True)
        with open(self.path / "definition.yaml", "w") as f:
            yaml.safe_dump(definition, f)
        return self

    def update(self, description: str | None = None, tags: set[str] | None = None):
        if description is not None:
            self.description = description
        if tags is not None:
            self.tags = set(tags)
        return self.save()

    def set_logo(self, image_path: Path | str):
        image_path = Path(image_path)
        return shutil.copy(image_path, self.path / f"logo{image_path.suffix}")

    @property
    def path(self):
        return path_in_project(PROJECT_DIR / "products" / self.name)

    @property
    def nb_integrations(self):
        return len(list(list_integrations(product=self.name)))

    @property
    def instances(self):
        return list(list_instances(self.name))

    def add_capability(self, role: Role, topic: str, mode: Mode = "push", format: str | None = None):
        """
        Add a generic capability to the product's definition
        """
        field = {
            "consumer": "consumes",
            "producer": "produces",
            "trigger": "triggers",
            "executor": "executes",
        }[role]
        if topic not in getattr(self, field):
            getattr(self, field)[topic] = []
        getattr(self, field)[topic].append(Cap(mode=mode, format=format))
        return self

    def add_setup_hook(
        self,
        role: Role,
        title: str,
        func: Callable | str,
        topic: str,
        mode: Mode = "push",
        order: str | None = None,
    ):
        """
        Generate a generic setup step to the product's setup.py
        to setup a consumer for the given topic
        """
        import meshroom.decorators

        ast = AST(self.path / "setup.py")
        if f := ast.append_function(func):
            ast.add_imports(Integration, Plug)
            f.decorate(
                {
                    "consumer": meshroom.decorators.setup_consumer,
                    "producer": meshroom.decorators.setup_producer,
                    "trigger": meshroom.decorators.setup_trigger,
                    "executor": meshroom.decorators.setup_executor,
                }[role],
                order=order,
                topic=topic,
                mode=mode,
                title=title,
            )
        ast.save()
        return self

    def add_teardown_hook(
        self,
        role: Role,
        title: str,
        func: Callable | str,
        topic: str,
        mode: Mode = "push",
        order: str | None = None,
    ):
        """
        Generate a generic teardown step to the product's setup.py
        to teardown a consumer for the given topic
        """
        import meshroom.decorators

        ast = AST(self.path / "setup.py")
        if f := ast.append_function(func):
            ast.add_imports(Integration, Plug)
            f.decorate(
                {
                    "consumer": meshroom.decorators.teardown_consumer,
                    "producer": meshroom.decorators.teardown_producer,
                    "trigger": meshroom.decorators.teardown_trigger,
                    "executor": meshroom.decorators.teardown_executor,
                }[role],
                order=order,
                topic=topic,
                mode=mode,
                title=title,
            )
        ast.save()
        return self

    def list_capabilities(self, role: Role | None = None, topic: str | None = None, format: str | None = None, mode: Mode | None = None):
        """
        List the Product's generic consumer/producer/trigger/executor capabilities, either declared:
        - in definition.yaml's "consumes","produces","triggers", and "executes" sections
        - via meshroom.decorators.setup_xxx(...) decorators in setup.py
        """
        from meshroom.decorators import Hook

        out: set[Capability] = set()

        mappings = {
            "consumer": "consumes",
            "producer": "produces",
            "trigger": "triggers",
            "executor": "executes",
        }

        for r, field in mappings.items():
            for t, caps in getattr(self, field).items():
                for c in cast(list[Cap], caps):
                    if (not topic or topic == t) and (not format or format == c.format or c.format is None) and (not mode or mode == c.mode):
                        out.add(Capability(topic=t, role=r, mode=c.mode, format=c.format))

        # Collect capabilities declared in setup hooks
        self.import_python_modules()
        for sf in Hook.get_all("setup"):
            if sf.product == self.name and sf.target_product is None:
                if (
                    (role is None or sf.role == role)
                    and (topic is None or sf.topic == topic)
                    and (format is None or sf.format == format or sf.format is None)
                    and (mode is None or sf.mode == mode)
                ):
                    # If the hook is mode-agnostic, consider that the product's capability supports both push and pull
                    if sf.mode is None:
                        for m in ("push", "pull"):
                            out.add(Capability(topic=sf.topic, role=sf.role, mode=m, format=sf.format))
                    else:
                        out.add(Capability(topic=sf.topic, role=sf.role, mode=sf.mode, format=sf.format))

        return list(out)

    def scaffold(self, template: str | Path):
        template = Path(TEMPLATES_DIR / "product" / template)
        if not template.is_dir():
            available_templates = "\n".join([f"- {t}" for t in TEMPLATES_DIR.glob("product/*")])
            raise ValueError(f"Template {template} not found\nAvailable templates are: {available_templates}")

        info("Scaffold product", self.name, "from", template)
        generate_files_from_template(template, self.path, {"{{NAME}}": self.name}, overwrite_files=True)

        return self

    def pull(self):
        """
        Pull the product's integration catalog using @pull hooks
        """
        (PROJECT_DIR / "mirrors" / self.name).mkdir(parents=True, exist_ok=True)
        if funcs := self.get_hooks("pull"):
            for f in funcs:
                info(f"- Pull {self.name} via {f.get_title()}")
                try:
                    f.func(path=PROJECT_DIR / "mirrors" / self.name)
                except Exception:
                    logging.error("Pull failed :", exc_info=True)
                print()
        else:
            return debug("🚫 Nothing to do")

    def import_python_modules(self):
        """
        Import the product's python modules to collect all hooks
        """
        for module in self.path.glob("*.py"):
            import_module(module, package_dir=self.path)

    def get_hooks(
        self,
        type: Literal["setup", "teardown", "scaffold", "watch", "pull"] | None = None,
        topic: str | None = None,
        mode: Mode | None = None,
        role: Role | None = None,
        format: str | None = None,
    ):
        """
        List all the Hooks defined for this product, declared either:
        - via meshroom.decorators.setup_consumer(...) or meshroom.decorators.setup_producer(...) decorators
        - via meshroom.decorators.watch(...) decorator
        Matching hooks are those whose target_product is None
        """
        from meshroom.decorators import Hook

        self.import_python_modules()

        # Sort the Hooks by their declared order
        return sorted(
            sf
            for sf in Hook.get_all(type)
            if sf.match(self) and sf.target_product is None and topic in (None, sf.topic) and mode in (None, sf.mode) and role in (None, sf.role) and format in (None, sf.format)
        )


class ProductSetting(Model):
    name: str
    type: Literal["string", "integer", "float", "boolean", "array", "object"] = "string"
    items: list["ProductSetting"] | Literal["string", "integer", "float", "boolean"] = []
    properties: list["ProductSetting"] = []
    default: str | int | float | bool | None = None
    description: str = ""
    secret: bool = False
    required: bool = False

    @field_validator("type", mode="before")
    def convert_type(cls, v):
        # Some settings are defined as [type, 'null'] to reflect optional values, we want to keep only the type
        if isinstance(v, list):
            return [x for x in v if x not in ("null")][0]
        return v

    @staticmethod
    def from_json_schema(
        schema: dict | None = None,
        force_secret: set[str, Pattern] | None = {r"password|token|secret"},  # Ensure password/token are stored as secrets by default, even when they are missing the secret:true flag
    ) -> list["ProductSetting"]:
        """
        Convert a JSON schema to a list of ProductSetting objects
        :schema: A valid JSON schema to convert
        :force_secret: An optional set of setting names or regex patterns who shall be forced as secret
        """
        out = []
        if not schema:
            return out

        def is_secret(x: dict, name: str | None = None):
            for rule in force_secret or []:
                if isinstance(rule, str) and (name or x.get("name")) == rule:
                    return True
                elif re.search(rule, (name or x.get("name", "")), re.I):
                    return True
            if x.get("secret", False):
                return True
            return x.get("secret", False)

        if schema.get("type") not in (None, "object", "array"):
            if schema.get("name"):
                return ProductSetting(
                    name=schema["name"],
                    type=schema["type"],
                    description=schema.get("description", ""),
                    default=schema.get("default"),
                    required=schema.get("required", False),
                    secret=is_secret(schema),
                )
            return schema["type"]

        for k, v in schema.get("properties", {}).items():
            is_required = k in schema.get("required", [])
            try:
                out.append(
                    ProductSetting(
                        name=k,
                        type=v.get("type", "string"),
                        description=v.get("description", ""),
                        default=v.get("default"),
                        required=is_required or v.get("required", False),
                        secret=is_secret(v, k),
                        items=ProductSetting.from_json_schema(v.get("items", {}), force_secret) or [],
                        properties=ProductSetting.from_json_schema({"name": k, **v}, force_secret) if v.get("type") == "object" else [],
                    )
                )
            except ValueError:
                logging.warning(f"WARNING: Error creating product setting from JSON schema\n\n{schema}\n\n{k}:{v}", exc_info=True)

        return out


class Integration(Model):
    """
    Implementation of an integration of :product to :target_product
    :product: The product on which the integration is deployed
    :target_product: The product to which the integration is connected
    :topic: The data topic exchanged between the two products
    :role: The role played by the product in the integration (consumer, producer, trigger, executor)
    :mode: The mode of the data exchange (producer push, or consumer pull)
    """

    product: str
    target_product: str
    topic: str
    role: Role
    mode: Mode = "push"
    format: str | None = None
    documentation_url: str = ""
    settings: list["ProductSetting"] = []
    description: str = ""
    is_generic: bool = False

    model_config = ConfigDict(
        extra="allow",
    )

    def __str__(self):
        if self.owns_both:
            owns = "can setup both"
        elif self.owns_self:
            owns = "can setup self"
        else:
            owns = "no setup hook"

        if self.role in ("producer", "trigger"):
            return f"{self.product} --[{self.topic}:{self.mode}]-> {self.target_product} ({self.role}, {owns})"
        else:
            return f"{self.product} <-[{self.topic}:{self.mode}]-- {self.target_product} ({self.role}, {owns})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.product, self.target_product, self.topic, self.role, self.mode))

    def __eq__(self, value: "Integration"):
        if not isinstance(value, Integration):
            return False
        return (
            self.product == value.product
            and self.target_product == value.target_product
            and self.topic == value.topic
            and self.role == value.role
            and (self.mode == value.mode or None in (self.mode, value.mode))
        )

    def get_product(self):
        return get_product(self.product)

    def get_target_product(self):
        return get_product(self.target_product)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path.with_suffix(".yml"), "w") as f:
            yaml.safe_dump(self.model_dump(exclude={"is_generic"}), f)
        return self

    @staticmethod
    def load(filepath: Path):
        filepath = path_in_project(filepath)
        if not (filepath.with_suffix(".yml").is_file() or filepath.with_suffix(".yaml").is_file()) or filepath.parent.parent.parent.parent.resolve() != (PROJECT_DIR / "products").resolve():
            raise ValueError(f"No integration found at {filepath}")

        mode = "push"
        if filepath.stem.endswith("_pull"):
            topic, role, mode = filepath.stem.rsplit("_", maxsplit=2)
        else:
            topic, role = filepath.stem.rsplit("_", maxsplit=1)
        product = filepath.parent.parent.parent.name
        target_product = filepath.parent.name

        try:
            with open(filepath.with_suffix(".yml")) as f:
                config = yaml.safe_load(f)
        except Exception:
            config = {}

        return Integration.model_validate(
            {
                **config,
                "product": product,
                "target_product": target_product,
                "topic": topic,
                "role": role,
                "mode": mode,
            }
        )

    @property
    def plugs(self):
        if self.role in ("producer", "trigger"):
            return list(list_plugs(self.product, self.target_product, self.topic, self.mode))
        else:
            return list(list_plugs(self.target_product, self.product, self.topic, self.mode))

    @property
    def path(self):
        fn = f"{self.topic}_{self.role}"
        if self.format:
            fn += f"_{self.format}"
        if self.mode == "pull":
            fn += f"_{self.mode}"
        return path_in_project(PROJECT_DIR / "products" / self.product / "integrations" / self.target_product / fn)

    @cached_property
    def owns_both(self):
        """
        Check if the integration is able to setup both sides of a plug (*i.e.* has at least one setup hook with "owns_both=True")
        """
        return any(h.owns_both for h in self.get_hooks("setup"))

    @cached_property
    def owns_self(self):
        """
        Check if the integration is able to setup its side of a plug (*i.e.* has at least one setup hook, but no setup hook with "owns_both=True")
        """
        if not (hooks := self.get_hooks("setup")):
            return False

        return not any(h.owns_both for h in hooks)

    def get_or_prompt(self, attribute: str, prompt: str):
        """Get the given :attribute from the integration's manifest, or prompt the user for it"""
        if not getattr(self, attribute, None):
            setattr(self, attribute, interaction.prompt(prompt))
            self.save()
        return getattr(self, attribute)

    def matches(self, integration: "Integration"):
        """Check if this integration matches a complementary integration (e.g., consumer/producer)"""
        return (
            self.topic == integration.topic
            and (sorted((self.role, integration.role)) in (["consumer", "producer"], ["executor", "trigger"]))
            and (self.mode == integration.mode or self.mode is None or integration.mode is None)
            and (self.format == integration.format or self.format is None or integration.format is None)
        )

    def scaffold(self):
        info("Scaffold integration", self.product, "to", self.target_product, self.topic, self.role, self.mode)
        for i, f in enumerate(self.get_hooks("scaffold")):
            info(f"\n{i + 1}) {f.get_title()}")
            f.call(integration=self)
        return self

    def add_setup_step(self, title: str, func: Callable | str, order: Literal["first", "last"] | int | None = None, owns_both: bool = False):
        """
        Append a setup step to the integration's python code
        """
        import meshroom.decorators

        return self.add_function(func, decorator=meshroom.decorators.setup, title=title, order=order, owns_both=owns_both)

    def add_teardown_step(self, title: str, func: Callable | str, order: Literal["first", "last"] | int | None = None):
        """
        Append a teardown step to the integration's python code
        """
        import meshroom.decorators

        return self.add_function(func, decorator=meshroom.decorators.teardown, title=title, order=order)

    def add_function(self, func: Callable, decorator: Callable, **decorator_kwargs):
        """
        Append a function to the integration's python code
        """
        ast = AST(self.path.with_suffix(".py"))
        if f := ast.append_function(func):
            ast.add_imports(Integration, Plug, Instance)
            f.decorate(
                decorator,
                **decorator_kwargs,
                exclude_none=True,
            )
        ast.save()
        return self

    def up(self, plug: "Plug"):
        """Setup the Integration on the instance"""
        info(f"> Setup {self.role}")
        instance = plug.get_src_instance() if self.role in ("producer", "trigger") else plug.get_dst_instance()
        for i, f in enumerate(self.get_hooks("setup")):
            info(f"\n{i + 1}) {f.get_title()}")
            f.call(plug=plug, integration=self, instance=instance)
        info("✓ done\n")

    def down(self, plug: "Plug"):
        """Tear down the Integration from the instance"""
        info("> Teardown", self.role)
        instance = plug.get_src_instance() if self.role in ("producer", "trigger") else plug.get_dst_instance()
        for i, f in enumerate(self.get_hooks("teardown")):
            info(f"\n{i + 1}) {f.get_title()}")
            f.call(plug=plug, integration=self, instance=instance)
        info("✓ done\n")

    def get_hooks(self, type: Literal["setup", "teardown", "scaffold", "watch"] | None = None):
        """
        List all the hooks defined for this integration, declared either:
        - via meshroom.decorators.setup(...) decorator at integration-level
        - via meshroom.decorators.scaffold(...) decorator at integration-level, providing integration scaffolding steps
        - via meshroom.decorators.setup_consumer(...) or meshroom.decorators.setup_producer(...) decorators at product-level
        """
        from meshroom.decorators import Hook

        self.import_python_modules()

        # Sort the hooks by their declared order
        funcs = sorted(sf for sf in Hook.get_all(type) if sf.match(self))

        # If the integration overloads the setup hooks, keep only the overloaded ones and the ones marked to be kept
        if any(f.target_product for f in funcs):
            funcs = [f for f in funcs if f.target_product or f.keep_when_overloaded]

        return funcs

    def import_python_modules(self):
        """
        Import the integration's python module to collect all hooks
        Also ensure the product's python modules are imported too
        """
        import_module(self.path.with_suffix(".py"), package_dir=self.path.parent.parent.parent)
        self.get_product().import_python_modules()

    def publish(self):
        """Publish the integration according to the defined product's @publish hooks"""
        if not self.path.with_suffix(".yml").is_file():
            return False  # Skip publishing if the integration isn't an explicitly defined one
        funcs = self.get_hooks("publish")
        if not funcs:
            return False
        info(f"Publish integration {self}")
        for f in funcs:
            f.call(integration=self)
        info(f"✓ Published {self}")
        return True


class Instance(Model):
    """
    A Instance is an instantiation of a product, configuring a set of Plug instances
    :name: The name of the instance, which is also the directory name under /config/:product
    :product: The product the instance instantiates
    """

    name: str
    product: str
    settings: dict = {}

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    @staticmethod
    def load(path: Path):
        if not path.is_dir():
            raise ValueError(f"Path {path} is not a plug directory")
        path = path_in_project(path)
        config = {}
        if (path / "config.yaml").is_file():
            with open(path / "config.yaml") as f:
                config = yaml.safe_load(f)
        config["name"] = path.name
        config["product"] = path.parent.name
        return Instance.model_validate(config)

    def save(self):
        self.path.mkdir(parents=True, exist_ok=True)
        with open(self.path / "config.yaml", "w") as f:
            yaml.safe_dump(self.model_dump(), f)
        return self

    def get_settings_schema(self):
        """Get the product's settings expected JSON schema"""
        return get_product(self.product).settings

    def set_secret(self, key: str, value: Any):
        """Store a secret value for this instance (GPG encrypted)"""
        return secrets.set_secret(f"{self.product}_{self.name}_{key}", value)

    def get_secret(self, key: str, prompt_if_not_exist: str | bool | None = None):
        """Retrieve a secret value for this instance (GPG encrypted)"""
        if prompt_if_not_exist is True:
            prompt_if_not_exist = f"Enter secret for {key}"

        return secrets.get_secret(f"{self.product}_{self.name}_{key}", prompt_if_not_exist=prompt_if_not_exist)

    def get_product(self) -> Product:
        return get_product(self.product)

    @property
    def plugs(self):
        """List the plugs configured for this instance"""
        return list(list_plugs(src_instance=self.name))

    @property
    def path(self):
        """Get the path to the instance's configuration directory"""
        return path_in_project(PROJECT_DIR / "instances" / self.product / self.name)

    def watch(self, topic: str, role: Role | None = None, mode: Mode | None = None):
        """
        Watch the instance for data flowing through a given topic,
        using the most specific @watch hook found
        """
        try:
            w = sorted(
                self.get_product().get_hooks("watch", topic=topic, role=role, mode=mode),
                key=lambda x: (x.topic is None, x.role is None, x.mode is None),
                reverse=True,
            )[0]

        except IndexError:
            raise ValueError(f"🚫 No @watch function found for {self}")
        yield from w.call(instance=self, topic=topic, role=role, mode=mode)

    def produce(self, topic: str, data: str | bytes, mode: Mode | None = None):
        """
        Produce data flowing through a given topic to this instance
        using the most specific @produce hook found
        """
        try:
            s = sorted(
                self.get_product().get_hooks("produce", topic=topic, mode=mode),
                key=lambda x: (x.topic is None, x.role is None, x.mode is None),
                reverse=True,
            )[0]
        except IndexError:
            raise ValueError(f"🚫 No @produce function found for {self}")
        return s.call(
            plug=self,
            instance=self,
            topic=topic,
            mode=mode,
            data=data,
        )

    def trigger(self, topic: str, data: dict | None = None, mode: Mode | None = None):
        """
        Emulate a trigger exposed by this instance
        using the most specific @trigger hook found
        """
        try:
            s = sorted(
                self.get_product().get_hooks("trigger", topic=topic, mode=mode),
                key=lambda x: (x.topic is None, x.role is None, x.mode is None),
                reverse=True,
            )[0]
        except IndexError:
            raise ValueError(f"🚫 No @trigger function found for {self}")
        return s.call(
            plug=None,
            instance=self,
            topic=topic,
            mode=mode,
            data=data,
        )

    def execute(self, topic: str, data: dict | None = None, mode: Mode | None = None):
        """
        Remotely trigger an executor exposed by this instance
        using the most specific @execute hook found
        """
        try:
            s = sorted(
                self.get_product().get_hooks("execute", topic=topic, mode=mode),
                key=lambda x: (x.topic is None, x.role is None, x.mode is None),
                reverse=True,
            )[0]
        except IndexError:
            raise ValueError(f"🚫 No @execute function found for {self}")
        return s.call(
            plug=None,
            instance=self,
            topic=topic,
            mode=mode,
            data=data,
        )


class Plug(Model):
    """
    A Plug is a configuration of an integration between two Instances of two Products
    that defines the data exchange of a given topic

    :src_instance: The source instance of the integration, producing data
    :dst_instance: The destination instance of the integration, consuming data
    :topic: The data topic exchanged between the two instances
    :mode: The mode of the data exchange (push or pull)

    A plug can be setup or torn down on the target systems via the up() and down() methods
    """

    src_instance: str
    dst_instance: str
    topic: str
    mode: Mode
    format: str | None = None
    src_config: dict = {}
    dst_config: dict = {}
    status: Literal["up", "down"] = "down"
    kind: Literal["trigger"] | None = None
    owner: str | None = None
    settings: dict = {}

    def __str__(self):
        out = f"{self.src_instance} --[{self.topic}:{self.mode}]-> {self.dst_instance}"
        if self.format:
            out += f" ({self.format})"
        return out

    @staticmethod
    def load(filepath: Path):
        filepath = path_in_project(filepath)
        config = {}
        with open(filepath) as f:
            config = yaml.safe_load(f)
        if filepath.stem.endswith("_pull") or filepath.stem.endswith("_push"):
            topic, mode = filepath.stem.rsplit("_", maxsplit=1)
        else:
            mode = "push"
            topic = filepath.stem
        config["topic"] = topic
        config["mode"] = mode
        config["src_instance"] = filepath.parent.parent.parent.name
        config["dst_instance"] = filepath.parent.name
        return Plug.model_validate(config)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            yaml.safe_dump(self.model_dump(), f)
        return self

    def delete(self):
        self.path.unlink()
        if not list(self.path.parent.iterdir()):
            self.path.parent.rmdir()
        if not list(self.path.parent.parent.iterdir()):
            self.path.parent.parent.rmdir()
        info(f"✓ Unplugged {self}")

    @property
    def path(self):
        fn = f"{self.topic}_{self.mode}" if self.mode == "pull" else self.topic
        return path_in_project(get_instance(self.src_instance).path / "plugs" / self.dst_instance / f"{fn}.yaml")

    def get_secret(self, key: str, prompt_if_not_exist: str | bool | None = None):
        """Retrieve a secret value for this plug (GPG encrypted)"""
        if prompt_if_not_exist is True:
            prompt_if_not_exist = f"Enter secret for {key}: "

        return secrets.get_secret(
            f"{self.src_instance}_{self.dst_instance}_{self.topic}_{self.mode}_{key}",
            prompt_if_not_exist=prompt_if_not_exist or False,
        )

    def set_secret(self, key: str, value: Any):
        """Store a secret value for this plug (GPG encrypted)"""
        return secrets.set_secret(
            f"{self.src_instance}_{self.dst_instance}_{self.topic}_{self.mode}_{key}",
            value,
        )

    def delete_secret(self, key: str):
        """Delete a secret value for this plug"""
        return secrets.delete_secret(f"{self.src_instance}_{self.dst_instance}_{self.topic}_{self.mode}_{key}")

    def get_consumer(self):
        """Get a suitable consumer to setup the consumer side of the integration"""
        try:
            return self.get_matching_integrations()[1]
        except ValueError:
            raise ValueError(f"No consumer seems to be implemented for {self}")

    def get_producer(self):
        """Get a suitable producer to setup the producer side of the integration"""
        try:
            return self.get_matching_integrations()[0]
        except ValueError:
            raise ValueError(f"No producer seems to be implemented for {self}")

    def get_trigger(self):
        """Get a suitable trigger to setup the trigger side of the integration"""
        try:
            return self.get_matching_integrations()[0]
        except ValueError:
            raise ValueError(f"No trigger seems to be implemented for {self}")

    def get_executor(self):
        """Get a suitable executor to setup the executor side of the integration"""
        try:
            return self.get_matching_integrations()[1]
        except ValueError:
            raise ValueError(f"No executor seems to be implemented for {self}")

    def get_src_instance(self):
        """Get the source Instance of the integration"""
        return get_instance(self.src_instance)

    def get_dst_instance(self):
        """Get the destination Instance of the integration"""
        return get_instance(self.dst_instance)

    def get_src_product(self):
        """Get the source Product of the integration"""
        return get_product(self.get_src_instance().product)

    def get_dst_product(self):
        """Get the destination Product of the integration"""
        return get_product(self.get_dst_instance().product)

    def get_matching_integrations(self):
        """
        Get the matching source and destination integrations for this plug
        * If a matching couple each owning its side is found, it is returned
        * Otherwise if one of the two defines a hook having owns_both=True, the other is returned as None
        * Producers/Triggers with owns_both=True take precedence over Consumers/Executors with owns_both=True
        """
        src_role = "trigger" if self.kind == "trigger" else "producer"
        dst_role = "executor" if self.kind == "trigger" else "consumer"
        srcs = list(list_integrations(self.get_src_product().name, self.get_dst_product().name, self.topic, role=src_role, mode=self.mode))
        dsts = list(list_integrations(self.get_dst_product().name, self.get_src_product().name, self.topic, role=dst_role, mode=self.mode))

        # Prioritize integration pairs whose members only own their side of the edge
        if self.owner is None and any(p.owns_self for p in srcs) and any(c.owns_self for c in dsts):
            return [p for p in srcs if p.owns_self][0], [c for c in dsts if c.owns_self][0]

        # If we can't find an integration for one of the sides, create a generic without setup hook, in case we find subsequently find an integration owning both sides
        if not srcs:
            srcs.append(Integration(product=self.get_src_product().name, target_product=self.get_dst_product().name, topic=self.topic, role=src_role, mode=self.mode))
        if not dsts:
            dsts.append(Integration(product=self.get_dst_product().name, target_product=self.get_src_product().name, topic=self.topic, role=dst_role, mode=self.mode))

        # Then look for a source integration that owns both sides,
        for s in srcs:
            if s.owns_both and self.owner in (None, self.src_instance):
                return s, dsts[0]
        # or a destination integration that owns both sides
        for d in dsts:
            if d.owns_both and self.owner in (None, self.dst_instance):
                return srcs[0], d

        raise ValueError(f"No matching integrations found for {self}")

    def get_unconfigured_settings(self):
        """List the settings that are not configured yet for the producer and the consumer"""
        # Look unconfigured settings for the producer and the consumer, respectively
        p = [("src", s) for s in self.get_producer().settings if s.name not in self.src_config]
        c = [("dst", s) for s in self.get_consumer().settings if s.name not in self.dst_config]

        # In pull mode, the producer is configured first, (resp. consumer in push mode)
        return p + c if self.mode == "pull" else c + p

    def up(self):
        """Setup the integration on the target Instances"""
        if self.status == "up":
            return debug(f"🚫 {self} is already up")

        info("Setup", self)

        # Look for a (consumer, producer) pair of integrations
        p, c = self.get_matching_integrations()

        # If one of the integration owns both sides, no need to setup the other side
        # In pull mode, the producer is set up first, (resp. consumer in push mode)
        if self.mode == "pull" and p.owns_self and c.owns_self:
            p.up(self)
            c.up(self)
        elif p.owns_self and c.owns_self:
            c.up(self)
            p.up(self)
        elif p.owns_both:
            p.up(self)
        elif c.owns_both:
            c.up(self)
        else:
            raise ValueError(f"🚫 Can't setup {self}: no @setup hook found on corresponding integrations")

        self.status = "up"
        return self.save()

    def down(self):
        """Tear down the integration on the target Instances"""
        if self.status == "down":
            return debug(f"🚫 {self} is already down")

        info("Teardown", self)

        # Look for a (consumer, producer) pair of integrations
        p = self.get_producer()
        c = self.get_consumer()

        p.down(self)
        c.down(self)
        self.status = "down"
        return self.save()

    def watch(self):
        """Watch the integration for data received by its consumer end"""
        try:
            w = self.get_consumer().get_hooks("watch")[0]
        except IndexError:
            raise ValueError(f"🚫 No @watch function found for {self}")
        yield from w.call(
            plug=self,
            instance=self.get_dst_instance(),
            integration=self.get_consumer(),
            mode=self.mode,
        )

    def produce(self, data: str | bytes):
        """Produce data flowing through the integration"""
        try:
            s = self.get_consumer().get_hooks("produce")[0]
        except IndexError:
            raise ValueError(f"🚫 No @produce function found for {self}")
        return s.call(
            plug=self,
            instance=self.get_dst_instance(),
            integration=self.get_consumer(),
            mode=self.mode,
            data=data,
        )

    def trigger(self, data: str | bytes):
        """Emulate the triggering of the trigger exposed by this integration"""
        try:
            s = self.get_trigger().get_hooks("trigger")[0]
        except IndexError:
            raise ValueError(f"🚫 No @trigger function found for {self}")
        return s.call(
            plug=self,
            instance=self.get_src_instance(),
            integration=self.get_trigger(),
            mode=self.mode,
            data=data,
        )

    def execute(self, data: str | bytes):
        """Execute the executor exposed by this integration"""
        try:
            s = self.get_executor().get_hooks("execute")[0]
        except IndexError:
            raise ValueError(f"🚫 No @execute function found for {self}")
        return s.call(
            plug=self,
            instance=self.get_dst_instance(),
            integration=self.get_executor(),
            mode=self.mode,
            data=data,
        )


def set_project_dir(path: str | Path):
    """Set the base project directory where all meshroom data will be loaded and saved"""
    path = Path(path)
    global PROJECT_DIR
    PROJECT_DIR = path


def get_project_dir():
    return PROJECT_DIR


def path_in_project(path: str | Path):
    """Check if the given path is under the project directory"""
    if Path(path).resolve().is_relative_to(PROJECT_DIR.resolve()):
        return Path(path)
    raise ValueError(f"Path {path} is not under the project directory {PROJECT_DIR}")


def init_project(path: str | Path, git: bool | str = True):
    """Initialize a new meshroom project in an empty or existing directory, optionally backing it with a git repo"""
    from meshroom.git import Git

    path = Path(path)
    set_project_dir(path)

    if path.is_dir() and list(PROJECT_DIR.iterdir()):
        if validate_meshroom_project(PROJECT_DIR):
            if git:
                Git().init(remote=git or None)
            debug("🚫 This meshroom project is already initialized")
            return False
        raise ValueError("Directory is not empty and is not a meshroom project")

    # Create the project directory structure
    generate_files_from_template(
        TEMPLATES_DIR / "init_project",
        PROJECT_DIR,
        {"{{NAME}}": path.name},
    )

    (PROJECT_DIR / "products").mkdir(parents=True, exist_ok=True)
    (PROJECT_DIR / "instances").mkdir(parents=True, exist_ok=True)

    Git().init(remote=git or None)
    info(f"✓ Meshroom project initialized at {PROJECT_DIR.absolute()}")
    return True


def validate_meshroom_project(path: str | Path):
    """Check if the given directory is a valid meshroom project"""
    path = Path(path)
    if not (path / "products").is_dir():
        return False
    return True


def list_products(tags: set[str] | None = None, search: str | None = None):
    """
    List all products found in the project's products/ directory
    If :tags is specified, only list products that have all the specified tags
    If :search is specified, only list products whose name match the search string
    """
    for product_dir in (PROJECT_DIR / "products").iterdir():
        if product_dir.is_dir() and (search is None or search in product_dir.name):
            p = get_product(product_dir.name)
            if tags is None or p.tags & tags:
                yield p


def list_instances(product: str | None = None, search: str | None = None) -> Generator[Instance, None, None]:
    """
    List all instances found in the project's instances/ directory
    If a product is specified, only list instances for this product
    """
    path = PROJECT_DIR / "instances"
    if product:
        path = path_in_project(path / product)
        if path.is_dir():
            for instance_dir in path.iterdir():
                if instance_dir.is_dir() and (search is None or search in instance_dir.name):
                    yield Instance.load(instance_dir)
    else:
        if path.is_dir():
            for product_dir in path.iterdir():
                if product_dir.is_dir():
                    yield from list_instances(product_dir.name, search=search)


@cache
def get_product(product: str):
    """Get a product by name"""
    path = path_in_project(PROJECT_DIR / "products" / product)
    if not path.is_dir():
        raise ValueError(f"Product {product} not found")

    return Product.load(path)


@cache
def get_instance(instance: str, product: str | None = None):
    """Get a instance by name"""
    path = path_in_project(PROJECT_DIR / "instances")
    if product:
        instance_dir = path / product / instance
        if instance_dir.is_dir():
            return Instance.load(instance_dir)
    else:
        for t in list_instances():
            if t.name == instance:
                return t
    raise ValueError(f"Instance {instance} not found")


def create_instance(product: str, name: str | None = None):
    name = name or product
    instance_dir = path_in_project(PROJECT_DIR / "instances" / product / name)
    if instance_dir.exists():
        debug(f"🚫 Instance {name} already exists")
        return Instance.load(instance_dir)

    if not (PROJECT_DIR / "products" / product).is_dir():
        raise ValueError(f"Product {product} not found")

    instance_dir.mkdir(parents=True, exist_ok=True)
    info(f"Create instance {name} for product {product}")
    return Instance.load(instance_dir).save()


def delete_instance(instance: str, product: str | None = None):
    path = PROJECT_DIR / "instances"
    get_instance(instance, product)
    if product:
        path = path_in_project(path / product / instance)
        shutil.rmtree(path)
        info("✓ Removed", path)
    else:
        for product_dir in path.iterdir():
            if path_in_project(product_dir / instance).is_dir():
                delete_instance(instance, product_dir.name)


def plug(
    topic: str,
    src_instance: str,
    dst_instance: str,
    mode: Mode | None = None,
    format: str | None = None,
    owner: Literal["both"] | str | None = None,
):
    """
    Create a new Plug between two Instances for a given topic
    The plug is created based on the available integrations between the products of the two instances:
    * If one producer and one consumer integrations are found, each owning its side of the plug, they are plugged together
    * If one trigger and one executor integrations are found, each owning its side of the plug, they are plugged together
    * If only one end of the plug is found, the plug is created only if one integration can setup both ends

    If no integration is found, or no integration with owns_both=True, or only one end is found but hasn't owns_both=True,
    the plug can't be created and a ValueError is raised
    """

    # Ensure instances exist
    src = get_instance(src_instance)
    dst = get_instance(dst_instance)
    try:
        # Check if the plug already exists (whatever the format)
        plug = get_plug(topic, src_instance, dst_instance, mode)
        debug(f"🚫 Plug {plug}  already exists at {plug.path}")
        return plug
    except ValueError:
        producers = list(list_integrations(src.product, dst.product, topic, "producer", mode=mode, format=format))
        consumers = list(list_integrations(dst.product, src.product, topic, "consumer", mode=mode, format=format))
        triggers = list(list_integrations(src.product, dst.product, topic, "trigger", mode=mode, format=format))
        executors = list(list_integrations(dst.product, src.product, topic, "executor", mode=mode, format=format))

        # priority is given to producer-consumer pairs where each owns its side of the plug
        for producer in producers:
            for consumer in consumers:
                if producer.matches(consumer):
                    if producer.owns_self and consumer.owns_self and owner in (None, "both"):
                        plug = Plug(
                            src_instance=src_instance,
                            dst_instance=dst_instance,
                            topic=topic,
                            mode=producer.mode or consumer.mode or mode,
                            format=producer.format or consumer.format or format,
                            owner=owner,
                        ).save()
                        info(f"✓ Plugged {plug}")
                        return plug

        for trigger in triggers:
            for executor in executors:
                if trigger.matches(executor):
                    if producer.owns_self and consumer.owns_self and owner in (None, "both"):
                        plug = Plug(
                            src_instance=src_instance,
                            dst_instance=dst_instance,
                            topic=topic,
                            mode=trigger.mode or executor.mode or mode,
                            format=trigger.format or executor.format or format,
                            kind="trigger",
                            owner=owner,
                        ).save()
                        info(f"✓ Plugged {plug}")
                        return plug

        # If not found, look for one integration able to setup both ends (*i.e.* having owns_both=True)
        if owner in (None, src_instance):
            for i in [*producers, *triggers]:
                kind = "trigger" if i.role == "trigger" else None
                if i.owns_both:
                    plug = Plug(
                        src_instance=src_instance,
                        dst_instance=dst_instance,
                        topic=topic,
                        mode=i.mode or mode,
                        format=i.format or format,
                        kind=kind,
                        owner=owner,
                    ).save()
                    info(f"✓ Plugged {plug}")
                    return plug
        if owner in (None, dst_instance):
            for i in [*consumers, *executors]:
                kind = "trigger" if i.role == "executor" else None
                if i.owns_both:
                    plug = Plug(
                        src_instance=src_instance,
                        dst_instance=dst_instance,
                        topic=topic,
                        mode=i.mode or mode,
                        format=i.format or format,
                        kind=kind,
                        owner=owner,
                    ).save()
                    info(f"✓ Plugged {plug}")
                    return plug

            raise ValueError(f"""❌ Matching capabilities were found between {dst_instance} ({dst.product}) and {src_instance} ({src.product}) for topic {topic} (mode={mode}),
but couldn't find any @setup hook among matching integrations

    Consumers found: {consumers or "None"}
    Producers found: {producers or "None"}
    Triggers found: {triggers or "None"}
    Executors found: {executors or "None"}

    You may want to scaffold setup hooks via

    meshroom create integration {src.product} {dst.product} {topic} producer {f"--format {format} " if format else ""}{f"--mode {mode} " if mode not in (None, "push") else ""}
    meshroom create integration {dst.product} {src.product} {topic} consumer {f"--format {format} " if format else ""}{f"--mode {mode} " if mode not in (None, "push") else ""}

    or manually implement the setup hooks for those integrations
""")

        raise ValueError(f"""❌ No integration between {dst_instance} ({dst.product}) and {src_instance} ({src.product}) for topic {topic} (mode={mode}) is implemented

    Consumers found: {consumers or "None"}
    Producers found: {producers or "None"}
    Triggers found: {triggers or "None"}
    Executors found: {executors or "None"}

    You may want to scaffold one via

    meshroom create integration {src.product} {dst.product} {topic} producer {f"--format {format} " if format else ""}{f"--mode {mode} " if mode not in (None, "push") else ""}
    meshroom create integration {dst.product} {src.product} {topic} consumer {f"--format {format} " if format else ""}{f"--mode {mode} " if mode not in (None, "push") else ""}
""")


def unplug(topic: str, src_instance: str, dst_instance: str, mode: Mode | None = None):
    try:
        get_plug(topic, src_instance, dst_instance, mode).delete()
    except ValueError:
        error(f"❌ Plug {src_instance} --[{topic}:{mode}]-> {dst_instance} not found")


def list_integrations(
    product: str | None = None,
    target_product: str | None = None,
    topic: str | None = None,
    role: Role | None = None,
    mode: Mode | None = None,
    format: str | None = None,
) -> list[Integration]:
    out: list[Integration] = []
    path = PROJECT_DIR / "products"
    for product_dir in path.iterdir() if product is None else [get_product(product).path]:
        if not product_dir.is_dir():
            continue

        # 1) First look for specifically implemented integrations
        if (product_dir / "integrations").is_dir():
            for target_product_dir in (product_dir / "integrations").iterdir() if target_product is None else [product_dir / "integrations" / target_product]:
                if not target_product_dir.is_dir():
                    continue

                for integration_file in target_product_dir.iterdir():
                    if integration_file.is_file() and integration_file.suffix in (".yml", ".yaml"):
                        i = Integration.load(integration_file)
                        if (not topic or i.topic == topic) and (not role or i.role == role) and (not mode or i.mode == mode) and (not format or i.format == format):
                            out.append(i)

        # 2) Look for matching pairs of generic product capabilities, with lower priority
        for a in get_product(product_dir.name).list_capabilities(role=role, topic=topic, format=format, mode=mode):
            for target_product_dir in path.iterdir() if target_product is None else [path / target_product]:
                if not target_product_dir.is_dir():
                    continue

                for b in get_product(target_product_dir.name).list_capabilities(topic=topic, format=format, mode=mode):
                    if a.matches(b):
                        # Yield generic Integration objects for matching capabilities
                        out.append(
                            Integration(
                                product=product_dir.name,
                                target_product=target_product_dir.name,
                                topic=a.topic or b.topic,
                                role=a.role,
                                mode=a.mode,
                                format=a.format or b.format,
                                is_generic=True,
                            )
                        )
    # Return a list of unique integrations, sorted by priority
    return list(set(sorted(out, key=lambda i: (i.product, i.target_product or "", i.topic, i.role, i.mode or "", i.format or ""))))


@cache
def get_integration(product: str, target_product: str, topic: str, role: Role, mode: Mode | None = None):
    try:
        return list(list_integrations(product, target_product, topic, role, mode))[0]
    except Exception:
        return None


def list_plugs(
    src_instance: str | None = None,
    dst_instance: str | None = None,
    topic: str | None = None,
    mode: Mode | None = None,
):
    path = PROJECT_DIR / "instances"
    if not path.is_dir():
        return
    for product_dir in path.iterdir():
        if not product_dir.is_dir():
            continue
        for src_instance_dir in product_dir.iterdir() if src_instance is None else [product_dir / src_instance]:
            if not (src_instance_dir / "plugs").is_dir():
                continue

            for dst_instance_dir in (src_instance_dir / "plugs").iterdir() if dst_instance is None else [src_instance_dir / "plugs" / dst_instance]:
                if dst_instance_dir.is_dir():
                    for plug_file in dst_instance_dir.iterdir():
                        if plug_file.is_file():
                            p = Plug.load(plug_file)
                            if (
                                (not src_instance or p.src_instance == src_instance)
                                and (not dst_instance or p.dst_instance == dst_instance)
                                and (not topic or p.topic == topic)
                                and (mode is None or p.mode == mode)
                            ):
                                yield p


def get_plug(topic: str, src_instance: str, dst_instance: str, mode: Mode | None = None):
    for plug in list_plugs(src_instance, dst_instance, topic, mode):
        return plug
    raise ValueError(f"Plug {src_instance} --[{topic}]-> {dst_instance}  {mode or ''} not found")


def scaffold_integration(
    product: str,
    target_product: str,
    topic: str,
    role: Role = "producer",
    mode: Mode = "push",
    format: str | None = None,
    **kwargs,
):
    fn = f"{topic}_{role}" if mode in (None, "push") else f"{topic}_{role}_{mode}"
    path = path_in_project(PROJECT_DIR / "products" / product / "integrations" / target_product / fn)

    if path.with_suffix(".yml").is_file():
        debug(f"🚫 Integration {product} -> {target_product} {topic} {role} {mode} already exists at {path}")
        return Integration.load(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    i = Integration(product=product, target_product=target_product, topic=topic, role=role, mode=mode, format=format).scaffold(**kwargs).save()

    info(f"✓ Integration {product} -> {target_product} {topic} {role} {mode} scaffolded at {path}")

    return i


def scaffold_product(name: str, template: str | None = None, **kwargs):
    path = path_in_project(PROJECT_DIR / "products" / name)
    if path.is_dir():
        debug(f"🚫 Product {name} already exists, see {path}/definition.yaml")
        return Product.load(path)

    p = create_product(path, **kwargs)
    if template:
        p.scaffold(template=template)
        p = Product.load(path)

    p.save()
    info(f"✓ Product {name} scaffolded {f'from {template}' if template else ''} at {path}/definition.yaml")
    return p


def scaffold_capability(product: str, topic: str, role: Role, mode: Mode = "push", format: str | None = None, **kwargs):
    p = get_product(product)
    if cap := p.list_capabilities(role, topic, format, mode):
        debug(f"🚫 Product '{product}' already has capability {cap[0]}")
        return cap[0]

    p.add_capability(role, topic, mode, format)
    p.save()
    out = p.list_capabilities(role, topic, format, mode)[0]
    info(f"✓ Capability {out} scaffolded for Product '{product}'")
    return out


def create_product(name: str, **kwargs):
    return Product.load(path_in_project(PROJECT_DIR / "products" / name)).update(**kwargs)


def up(src_instance: str | None = None, dst_instance: str | None = None, topic: str | None = None, mode: Mode | None = None):
    for plug in list_plugs(src_instance, dst_instance, topic, mode):
        plug.up()


def down(src_instance: str | None = None, dst_instance: str | None = None, topic: str | None = None, mode: Mode | None = None):
    for plug in list_plugs(src_instance, dst_instance, topic, mode):
        plug.down()


def watch(topic: str, instance: str, dst_instance: str | None, mode: Mode | None = None):
    if dst_instance:
        p = get_plug(topic, instance, dst_instance, mode)
        w = p.watch()
        log(f"Watching plug {p} for {topic}", file=sys.stderr)
        return w
    else:
        t = get_instance(instance)
        w = t.watch(topic, "consumer", mode)
        log(f"Watching instance {t} for {topic}", file=sys.stderr)
        return w


def produce(topic: str, instance: str, dst_instance: str | None, data: str | bytes, mode: Mode | None = None):
    if dst_instance:
        return get_plug(topic, instance, dst_instance, mode).produce(data)
    else:
        return get_instance(instance).produce(topic, data, mode=mode)


def trigger(topic: str, instance: str, dst_instance: str | None, data: dict | None = None, mode: Mode | None = None):
    if dst_instance:
        return get_plug(topic, instance, dst_instance, mode).trigger(data)
    else:
        return get_instance(instance).trigger(topic, data, mode=mode)


def execute(topic: str, instance: str, dst_instance: str | None, data: dict | None = None, mode: Mode | None = None):
    if dst_instance:
        return get_plug(topic, instance, dst_instance, mode).execute(data)
    else:
        return get_instance(instance).execute(topic, data, mode=mode)


def publish(
    product: str | None = None,
    target_product: str | None = None,
    topic: str | None = None,
    role: Role | None = None,
    mode: Mode | None = None,
    format: str | None = None,
):
    if not any(i.publish() for i in list_integrations(product, target_product, topic, role, mode, format)):
        debug("🚫 No publish hook found")
