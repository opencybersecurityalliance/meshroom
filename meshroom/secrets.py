from functools import cache
from getpass import getpass, getuser
from hashlib import md5
import json
import gnupg

from meshroom.interaction import prompt_password


def get_gpg_id():
    """Generate a GPG ID based on the current user and the project directory"""
    from meshroom.model import get_project_dir

    return f"{getuser()}-{md5(bytes(get_project_dir().absolute())).hexdigest()[:8]}@meshroom"


@cache
def read_secrets():
    """Read the GPG-encrypted secrets store"""
    from meshroom.model import get_project_dir

    try:
        secrets_path = get_project_dir() / "secrets.gpg"
        gpg = gnupg.GPG()
        with open(secrets_path, "rb") as f:
            decrypted_data = gpg.decrypt_file(f)

        if not decrypted_data.ok:
            raise ValueError("Failed to decrypt secrets: No GPG key found for this Meshroom project")

        return json.loads(decrypted_data.data.decode())
    except FileNotFoundError:
        return {}


def write_secrets(secrets: dict, master_key: str | None = None):
    """Write the GPG-encrypted secrets store, eventually prompting for master key creation"""
    from meshroom.model import get_project_dir

    gpg_id = get_gpg_id()
    secrets_path = get_project_dir() / "secrets.gpg"
    secrets_path.parent.mkdir(parents=True, exist_ok=True)

    gpg = gnupg.GPG()
    keys = gpg.list_keys()
    if not any(f"<{gpg_id}>" in key["uids"][0] for key in keys):
        res = gpg.gen_key(
            gpg.gen_key_input(
                name_email=gpg_id,
                passphrase=master_key or prompt_password(f"Enter a Master Key to for this Meshroom project's secrets store (will use {gpg_id} GPG identity): "),
            )
        )
        if not res:
            raise ValueError("Failed to generate GPG key")

    with open(secrets_path, "wb") as f:
        encrypted_data = gpg.encrypt(json.dumps(secrets), gpg_id, always_trust=True)
        f.write(encrypted_data.data)


def get_secret(key: str, prompt_if_not_exist: str | bool = False):
    """Get a secret from the secrets store"""

    if not (v := read_secrets().get(key)) and prompt_if_not_exist:
        v = set_secret(key, prompt_password(prompt_if_not_exist))

    return v


def set_secret(key: str, value: str):
    """Set a secret in the secrets store"""
    s = read_secrets()
    s[key] = value
    write_secrets(s)
    return value


def delete_secret(key: str):
    """Delete a secret from the secrets store"""
    s = read_secrets()
    if key in s:
        del s[key]
    write_secrets(s)
