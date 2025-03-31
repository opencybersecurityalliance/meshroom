import os
from pathlib import Path
import shutil
import pytest

os.environ["PASSWORD"] = "password"


PROJECT_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="function", autouse=True)
def setup_project():
    from meshroom.model import set_project_dir

    shutil.rmtree(PROJECT_DIR, ignore_errors=True)
    set_project_dir(PROJECT_DIR)


def skip_during_ci(func):
    """Decorator to skip a test if running in Github CI."""
    if os.getenv("GITHUB_RUN_ID"):
        return pytest.mark.skip(reason="Skipped during CI, please run interactively")(func)
    return func
