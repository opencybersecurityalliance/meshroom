from pathlib import Path
import re
from subprocess import DEVNULL, STDOUT, CalledProcessError, check_call, check_output
from typing import Literal
from meshroom.model import get_project_dir


class Git:
    """
    Wrapper around the git command line tool
    """

    def __init__(self, path: str | None = None):
        self.path = path or get_project_dir()

    def init(self, remote: str):
        """Initialize a new Git repository in the project directory"""
        try:
            self._call("git", "init")

            if remote:
                old_remote = self._cmd("git", "remote").strip()
                if old_remote:
                    self._call("git", "remote", "remove", old_remote)
                self._call("git", "remote", "add", "origin", remote)
                self.pull()
        except Exception:
            ...

    def status(self):
        """Get the current status of the repository"""
        return self._cmd("git", "status")

    def branch(self, branch: str):
        """Switch to the given branch"""
        self._call("git", "checkout", branch)

    def pull(self, url: str | None = None):
        """Pull the latest changes from the remote repository"""
        if self.path.is_dir() and (self.path / ".git").is_dir():
            self._call("git", "pull")
        elif url:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            check_call(["git", "clone", url, Path(self.path).resolve().as_posix()])

    def add(self, path: str):
        """Add a file or directory to the staging area"""
        self._call("git", "add", path)

    def commit(self, msg: str):
        """Commit all changes in the staging area"""
        self._call("git", "commit", "-m", msg)

    def push(self, autocommit: bool = True, path: str = ".", commit_msg: str | None = None, remote: str | None = None, force: bool = False):
        """
        Push the current branch to the remote repository, optionally committing all changes under :path
        returns True if any files were committed
        """
        files = []
        try:
            if autocommit and (files := self.get_updated_files()):
                updated = ", ".join(files[:3])
                if len(files) > 3:
                    updated += f" and {len(files) - 3} more"
                self._call("git", "add", path)
                self._call("git", "commit", "-m", commit_msg or f"Update {updated}")
        except Exception:
            ...
        try:
            if remote:
                self._cmd("git", "push", remote, self.get_branch(), *["--force"] if force else [])
            else:
                self._cmd("git", "push", *["--force"] if force else [])
        except CalledProcessError as e:
            raise RuntimeError(e.stdout)
        return bool(files)

    def get_updated_files(self, depth: int = 1):
        """Get the list of updated paths in the current branch, up to the given depth"""
        files = set()
        for line in self._cmd("git", "diff", "--name-only").split():
            files.add("/".join(line.strip().split("/")[:depth]))
        return list(files)

    def get_remote(self, scheme: Literal["https"] | None = None):
        """Get the remote URL of the current repository"""
        try:
            res = self._cmd("git", "remote", "get-url", "origin").strip()
            if scheme == "https":
                res = re.sub(r"^git@(.+):(.+?)/(.+?)(?:\.git)?$", r"https://\1/\2/\3", res)
            return res
        except Exception:
            raise RuntimeError("\nThis git repository has no remote URL, please set one up using\ngit remote add origin <url>")

    def get_branch(self):
        """Get the current branch"""
        return self._cmd("git", "rev-parse", "--abbrev-ref", "HEAD").strip()

    def create_branch(self, name: str):
        """Create a new branch with the given name"""
        self._call("git", "checkout", "-b", name)

    def is_private(self, url: str):
        """Check if the remote git repository at :url is private (aka requires authentication)"""
        try:
            # Ensure we use https:// repo URL and pass dummy credentials
            url = re.sub(r"^git@([^:]+):", r"https://dummy:password@\1/", url)
            self._call("git", "ls-remote", url)
            return False
        except Exception:
            return True

    def copy_branch(self, src_branch: str, dst_repo: str, dst_branch: str):
        """Copy a branch from a source repo to the a differently-named branch of another repo"""
        if ":" in src_branch + dst_branch:
            raise ValueError("Branch names cannot contain ':'")
        remote = f"remote-{dst_branch}"
        self.add_remote(remote, dst_repo)
        self._call("git", "push", remote, f"{src_branch}:{dst_branch}")
        self.remove_remote(remote)

    def add_remote(self, name: str, url: str):
        """Add a new remote repository"""
        self._call("git", "remote", "add", name, url)

    def remove_remote(self, name: str):
        """Remove a remote repository"""
        self._call("git", "remote", "remove", name)

    def _cmd(self, *cmd: list[str], **kwargs):
        return check_output(cmd, cwd=self.path, encoding="utf-8", **kwargs)

    def _call(self, *cmd: list[str], stderr: bool = False, **kwargs):
        return check_call(cmd, cwd=self.path, stderr=DEVNULL if not stderr else STDOUT, **kwargs)
