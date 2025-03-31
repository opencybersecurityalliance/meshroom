import ast
import inspect
from pathlib import Path
from typing import Any, Callable


class AST:
    """
    Class to manipulate python files AST
    """

    def __init__(self, path: Path | str | None = None, code: str | None = None):
        """
        Build an AST from a file or a code string
        """
        if path:
            if code:
                raise ValueError("path and code arguments are mutually exclusive")
            self.path = Path(path)
            if self.path.is_file():
                with open(self.path, "r") as f:
                    self._ast = ast.parse(f.read())
            else:
                self._ast = ast.parse("\n")
        else:
            self.path = None
            self._ast = ast.parse(code)

    def has_function(self, name: str):
        """Check if a function exists in the AST"""
        for node in self._ast.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return True
        return False

    def has_import(self, name: str):
        """Check if a symbol is already imported in the AST"""
        for node in self._ast.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == name:
                        return True
            elif isinstance(node, ast.ImportFrom) and (name in [n.name for n in node.names] or name == node.module):
                return True
        return False

    def add_import(self, x: Any, exist_ok: bool = True):
        """Add an import to the AST"""
        if self.has_import(x.__name__):
            if exist_ok:
                return False
            raise ValueError(f"Import {x.__name__} already exists in {self.path}")
        imp = ast.ImportFrom(module=x.__module__, names=[ast.alias(name=x.__name__)], level=0)
        self._ast.body.insert(0, imp)
        return imp

    def add_imports(self, *x):
        """Add multiple imports to the AST"""
        for i in x:
            self.add_import(i)

    def append_function(self, func: Callable | str, name: str | None = None, exist_ok: bool = True):
        """Append a function to the AST"""
        name = name or func.__name__
        if not isinstance(func, str):
            func = inspect.getsource(func)

        if self.has_function(name):
            if exist_ok:
                return False
            raise ValueError(f"Function {name} already exists in {self.path}")

        f = ast.parse(func).body[0]
        if name:
            f.name = name

        self._ast.body.append(f)

        return Function(self, f)

    def save(self, path: Path | str | None = None):
        """Save the manipulated AST to a file"""
        path = path or self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(str(self))

    def __str__(self):
        """Return the python code representation of the AST"""
        return ast.unparse(self._ast)


class Function:
    """Wrapper around a FunctionDef AST node"""

    def __init__(self, ast: AST, func: ast.FunctionDef):
        self.ast = ast
        self.func = func

    def decorate(self, decorator: Callable, *decorator_args, exclude_none: bool = True, replace: bool = True, **decorator_kwargs):
        """Decorate the function with the given decorator, called with the given arguments and keyword arguments"""
        d: ast.Call = ast.parse(f"{decorator.__name__}()").body[0].value
        for k, v in decorator_kwargs.items():
            if not exclude_none or v is not None:
                keyword = ast.keyword(arg=k, value=ast.Constant(value=v))
                d.keywords.append(keyword)
        for arg in decorator_args:
            d.args.append(ast.Constant(value=arg))

        if replace:
            self.func.decorator_list.clear()

        self.func.decorator_list.insert(0, d)

        self.ast.add_import(decorator, exist_ok=True)

        return self


def adapt_kwargs_to_signature(func: Callable, **kwargs):
    """Adapt kwargs to a function signature"""
    sig = inspect.signature(func)
    return {k: v for k, v in kwargs.items() if k in sig.parameters}
