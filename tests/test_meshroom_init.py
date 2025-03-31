from shutil import rmtree
from meshroom.model import init_project
from tests.conftest import PROJECT_DIR


def test_meshroom_init():
    rmtree(PROJECT_DIR, ignore_errors=True)
    init_project(PROJECT_DIR)
    assert (PROJECT_DIR / ".gitignore").is_file()
    assert (PROJECT_DIR / "README.md").is_file()
    assert (PROJECT_DIR / "products").is_dir()
    assert (PROJECT_DIR / "instances").is_dir()
