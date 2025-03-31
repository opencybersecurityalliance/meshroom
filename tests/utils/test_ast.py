from meshroom.ast import AST


def test_append_function_to_file():
    ast = AST(
        code="""
import stuff

@decorate(arg, kwarg=0)
def myfunc(param):
    pass
"""
    )

    assert str(ast) == "import stuff\n\n@decorate(arg, kwarg=0)\ndef myfunc(param):\n    pass"
    assert ast.has_function("myfunc")
    assert ast.has_import("stuff")
    assert not ast.has_function("otherfunc")
    assert not ast.has_import("otherstuff")

    ast.append_function(_example_func)
    assert ast.has_function("_example_func")
    ast.append_function(_example_func)
    f = ast.append_function(_example_func, name="_example_func2")
    assert ast.has_function("_example_func2")
    ast.add_import(AST)
    assert ast.has_import("meshroom.ast")

    f.decorate(_the_decorator, arg=1, kwarg=2)

    assert (
        str(ast)
        == """
from test_ast import _the_decorator
from meshroom.ast import AST
import stuff

@decorate(arg, kwarg=0)
def myfunc(param):
    pass

def _example_func(somearg: str):
    pass

@_the_decorator(arg=1, kwarg=2)
def _example_func2(somearg: str):
    pass
""".strip()
    )


def _example_func(somearg: str):
    pass


def _the_decorator(*args, **kwargs):
    return lambda func: func
