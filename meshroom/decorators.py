import inspect
from pathlib import Path
from typing import Callable, Literal
from meshroom.ast import adapt_kwargs_to_signature
from meshroom.model import Integration, Model, Product, Role, Mode, get_product, get_project_dir

HookType = Literal[
    "setup",  # @setup hooks are executed upon `meshroom up`
    "teardown",  # @teardown hooks are executed upon `meshroom down`
    "scaffold",  # @scaffold hooks are executed upon `meshroom create integration`
    "watch",  # @watch hooks are executed upon `meshroom watch`
    "produce",  # @produce hooks are executed upon `meshroom produce`
    "trigger",  # @trigger hooks are executed upon `meshroom trigger`
    "execute",  # @execute hooks are executed upon `meshroom execute`
    "publish",  # @publish hooks are executed upon `meshroom publish`
    "pull",  # @pull hooks are executed upon `meshroom pull`
]
all_hooks: set["Hook"] = set()
HookOrder = Literal["first", "last"] | int


class Hook(Model):
    product: str
    target_product: str | None
    role: Role | None = None
    topic: str | None = None
    func: Callable
    mode: Mode | None = None
    format: str | None = None
    keep_when_overloaded: bool = False
    order: HookOrder | None = None
    title: str
    type: HookType = "setup"
    owns_both: bool = False

    def match(self, o: Integration | Product):
        if isinstance(o, Integration):
            return (
                self.product == o.product
                and self.target_product in (None, o.target_product)
                and self.role == o.role
                and self.topic in (None, o.topic)
                and self.mode in (None, o.mode)
                and self.format in (None, o.format)
            )
        else:
            return self.product == o.name and self.target_product is None

    def __lt__(self, other: "Hook"):
        if self.order == "first":
            return True
        elif self.order == "last":
            return False
        if other.order == "first":
            return False
        elif other.order == "last":
            return True
        if other is None or other.order is None:
            return True
        if self.order is None:
            return False
        return self.order < other.order

    def get_title(self):
        """Return this setup step's title, falling back to the Hook's name if not set"""
        return self.title or self.func.__name__

    @staticmethod
    def clear():
        all_hooks.clear()

    def __hash__(self):
        return hash((self.product, self.target_product, self.role, self.mode, self.topic, self.title, self.type, self.owns_both))

    def __eq__(self: "Hook", other: "Hook"):
        return (
            self.product == other.product
            and self.target_product == other.target_product
            and self.role == other.role
            and self.mode == other.mode
            and self.topic == other.topic
            and self.title == other.title
            and self.type == other.type
            and self.owns_both == other.owns_both
        )

    @staticmethod
    def add(
        product: str,
        target_product: str | None,
        role: Role,
        topic: str | None,
        mode: Mode,
        func: Callable,
        keep_when_overloaded: bool,
        order: Literal["first", "last"] | None = None,
        title: str | None = None,
        type: HookType = "setup",
        format: str | None = None,
        owns_both: bool = False,
    ):
        all_hooks.add(
            sf := Hook(
                product=product,
                target_product=target_product,
                role=role,
                topic=topic,
                mode=mode,
                func=func,
                keep_when_overloaded=keep_when_overloaded,
                order=order,
                title=title or inspect.getdoc(func) or func.__name__,
                type=type,
                format=format,
                owns_both=owns_both,
            )
        )
        return sf

    @staticmethod
    def get_all(type: HookType | None = None):
        return [sf for sf in all_hooks if type is None or sf.type == type]

    def call(self, **kwargs):
        """Call the Hook with the given kwargs, adapted to its signature"""
        return self.func(**adapt_kwargs_to_signature(self.func, **kwargs))


# Product-level setup decorators


def setup_consumer(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic consumer setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("setup_consumer() decorator is allowed only in a product's setup.py")
        Hook.add(product.name, None, "consumer", topic, mode, func, keep_when_overloaded, order, title, "setup", format, owns_both=owns_both)
        return func

    return decorator


def teardown_consumer(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic consumer setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("teardown_consumer() decorator is allowed only in a product's setup.py")
        Hook.add(product.name, None, "consumer", topic, mode, func, keep_when_overloaded, order, title, "teardown", format, owns_both=owns_both)
        return func

    return decorator


def setup_executor(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic executor setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("setup_executor() decorator is allowed only in a product's setup.py")
        Hook.add(product.name, None, "executor", topic, mode, func, keep_when_overloaded, order, title, "setup", format, owns_both=owns_both)
        return func

    return decorator


def teardown_executor(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic executor setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("teardown_executor() decorator is allowed only in a product's setup.py")
        Hook.add(product.name, None, "executor", topic, mode, func, keep_when_overloaded, order, title, "teardown", format, owns_both=owns_both)
        return func

    return decorator


def setup_producer(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic producer setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("setup_producer() decorator is allowed only in a product's setup.py")

        Hook.add(product.name, None, "producer", topic, mode, func, keep_when_overloaded, order, title, "setup", format, owns_both=owns_both)
        return func

    return decorator


def teardown_producer(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic producer setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("teardown_producer() decorator is allowed only in a product's setup.py")

        Hook.add(product.name, None, "producer", topic, mode, func, keep_when_overloaded, order, title, "teardown", format, owns_both=owns_both)
        return func

    return decorator


def setup_trigger(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic trigger setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("setup_trigger() decorator is allowed only in a product's setup.py")

        Hook.add(product.name, None, "trigger", topic, mode, func, keep_when_overloaded, order, title, "setup", format, owns_both=owns_both)
        return func

    return decorator


def teardown_trigger(
    topic: str | None = None,
    title: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    keep_when_overloaded: bool = False,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a generic trigger setup hook for the product where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("teardown_trigger() decorator is allowed only in a product's setup.py")

        Hook.add(product.name, None, "trigger", topic, mode, func, keep_when_overloaded, order, title, "teardown", format, owns_both=owns_both)
        return func

    return decorator


def watch(topic: str, mode: Mode | None = None, format: str | None = None):
    """
    Decorator to declare a function as yielding data received from a topic consumed by the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        try:
            i = Integration.load(func_file.with_suffix(""))
            if i.role not in "consumer":
                raise ValueError("watch() decorator can only be used in a consumer Integration")
            Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, None, None, "watch", format)
            return func
        except ValueError:
            if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
                raise ValueError("watch() decorator can't be used outside of a Product's directory")

            Hook.add(product.name, None, "consumer", topic, mode, func, True, None, None, "watch", format)
            return func

    return decorator


def produce(topic: str, mode: Mode | None = None, format: str | None = None):
    """
    Decorator to declare a function as emulating data transmission to a topic consumed by the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        try:
            i = Integration.load(func_file.with_suffix(""))
            if i.role not in "producer":
                raise ValueError("produce() decorator can only be used in a consumer Integration")
            Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, None, None, "produce", format)
            return func
        except ValueError:
            if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
                raise ValueError("produce() decorator can't be used outside of a Product's directory")

            Hook.add(product.name, None, "consumer", topic, mode, func, True, None, None, "produce", format)
            return func

    return decorator


def trigger(topic: str | None = None, mode: Mode | None = None, format: str | None = None):
    """
    Decorator to declare a function as triggering the given trigger topic by the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        try:
            i = Integration.load(func_file.with_suffix(""))
            if i.role not in "trigger":
                raise ValueError("trigger() decorator can only be used in a trigger Integration")
            Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, None, None, "trigger", format)
            return func
        except ValueError:
            if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
                raise ValueError("trigger() decorator can't be used outside of a Product's directory")

            Hook.add(product.name, None, "trigger", topic, mode, func, True, None, None, "trigger", format)
            return func

    return decorator


def execute(topic: str | None = None, mode: Mode | None = None, format: str | None = None):
    """
    Decorator to declare a function as remotely executing the given executor exposed by the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        try:
            i = Integration.load(func_file.with_suffix(""))
            if i.role not in "trigger":
                raise ValueError("execute() decorator can only be used in an executor Integration")
            Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, None, None, "execute", format)
            return func
        except ValueError:
            if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
                raise ValueError("execute() decorator can't be used outside of a Product's directory")

            Hook.add(product.name, None, "executor", topic, mode, func, True, None, None, "execute", format)
            return func

    return decorator


def publish(topic: str | None = None, role: Role | None = None, mode: Mode | None = None, format: str | None = None):
    """
    Decorator to declare a function as publishing an integration exposed by the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        try:
            i = Integration.load(func_file.with_suffix(""))
            Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, None, None, "publish", format)
            return func
        except ValueError:
            if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
                raise ValueError("publish() decorator can't be used outside of a Product's directory")

            Hook.add(product.name, None, role, topic, mode, func, True, None, None, "publish", format)
            return func

    return decorator


def pull(title: str | None = None, order: HookOrder | None = None):
    """
    Decorator to declare a function as pull a product's integrations catalog
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("pull() decorator can't be used outside of a Product's directory")

        Hook.add(product.name, None, None, None, None, func, True, order, title, "pull", None)
        return func

    return decorator


def scaffold_consumer(
    topic: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    order: HookOrder | None = None,
):
    """
    Decorator to declare a function as a code generator for a new consumer integration for the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("scaffold_consumer() decorator is allowed only in a product's python modules")

        Hook.add(product.name, None, "consumer", topic, mode, func, True, order, None, "scaffold", format)
        return func

    return decorator


def scaffold_executor(
    topic: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    order: HookOrder | None = None,
):
    """
    Decorator to declare a function as a code generator for a new executor integration for the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("scaffold_executor() decorator is allowed only in a product's scaffold.py")

        Hook.add(product.name, None, "executor", topic, mode, func, True, order, None, "scaffold", format)
        return func

    return decorator


def scaffold_producer(
    topic: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    order: HookOrder | None = None,
):
    """
    Decorator to declare a function as a code generator for a new producer integration for the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("scaffold_producer() decorator is allowed only in a product's scaffold.py")

        Hook.add(product.name, None, "producer", topic, mode, func, True, order, None, "scaffold", format)
        return func

    return decorator


def scaffold_trigger(
    topic: str | None = None,
    mode: Mode | None = None,
    format: str | None = None,
    order: HookOrder | None = None,
):
    """
    Decorator to declare a function as a code generator for a new trigger integration for the product where it resides
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        if func_file.parent.parent.resolve() != (get_project_dir() / "products").resolve() or not (product := get_product(func_file.parent.name)):
            raise ValueError("scaffold_trigger() decorator is allowed only in a product's scaffold.py")

        Hook.add(product.name, None, "trigger", topic, mode, func, True, order, None, "scaffold", format)
        return func

    return decorator


# Integration-level setup decorators


def setup(
    title: str | None = None,
    format: str | None = None,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a setup step for the integration where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        i = Integration.load(func_file.with_suffix(""))
        if not i:
            raise ValueError("setup() decorator can't be used outside of an Integration")

        Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, order, title, "setup", format, owns_both=owns_both)
        return func

    return decorator


def teardown(
    title: str | None = None,
    order: HookOrder | None = None,
    owns_both: bool = False,
):
    """
    Decorator to declare a function as a setup step for the integration where it resides
    If :title is not set, the function's docstring or name will be used
    """

    def decorator(func: Callable):
        func_file = Path(inspect.getfile(func))
        i = Integration.load(func_file.with_suffix(""))
        if not i:
            raise ValueError("teardown() decorator can't be used outside of an Integration")

        Hook.add(i.product, i.target_product, i.role, i.topic, i.mode, func, True, order, title, "teardown", owns_both=owns_both)
        return func

    return decorator
