import os
from meshroom.model import get_project_dir
from meshroom.secrets import delete_secret, get_secret, read_secrets, set_secret
from tests.conftest import skip_during_ci


@skip_during_ci
def test_secrets():
    set_secret("test", "thisisatest")
    assert get_secret("test") == "thisisatest"

    # Force re-read the secrets file
    read_secrets.cache_clear()
    assert get_secret("test") == "thisisatest"

    # Force pinentry prompt
    os.system("gpgconf --kill gpg-agent")
    read_secrets.cache_clear()
    assert get_secret("test") == "thisisatest"

    set_secret("test", "thisisatest2")
    assert get_secret("test") == "thisisatest2"
    read_secrets.cache_clear()
    assert get_secret("test") == "thisisatest2"

    delete_secret("test")
    read_secrets.cache_clear()
    assert get_secret("test") is None

    (get_project_dir() / "secrets.gpg").unlink()
