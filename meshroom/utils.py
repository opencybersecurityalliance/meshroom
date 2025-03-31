import os
from pathlib import Path
import shutil
import sys
import importlib.util
from typing import Iterable
from pydantic import BaseModel
from tabulate import tabulate as _tabulate

ROOT_DIR = Path(__file__).resolve().parent
UI_DIR = ROOT_DIR / ".." / "dist"


def read_file(directory: str, filename: str) -> str:
    """Read a file's content or return empty string if not exists"""
    try:
        with open(os.path.join(directory, filename)) as f:
            return f.read()
    except Exception:
        return ""


def tabulate(
    data,
    headers: Iterable[str] | None = None,
    formatters: dict | None = None,
):
    columns = []
    for h in headers:
        if isinstance(h, dict):
            columns.append(list(h.keys())[0])
        elif not isinstance(h, str):
            columns.append(h[0])
        else:
            columns.append(h)

    def _format(x):
        for t, f in (formatters or {}).items():
            if isinstance(x, t):
                return f(x)
        if x is None:
            return "-"
        if isinstance(x, (list, tuple, set)):
            if not x:
                return "-"
            return ", ".join(map(_format, x))
        if isinstance(x, BaseModel):
            return f"{x}"
        return x

    def _field(x, h: str | dict | tuple):
        if isinstance(h, dict):
            key = list(h.values())[0]
        elif not isinstance(h, str):
            key = h[-1]
        else:
            key = h.lower().replace(" ", "_")

        if isinstance(x, BaseModel):
            if callable(key):
                return key(x)
            v = getattr(x, key, None)
            if callable(v):
                return v()
            return v
        if isinstance(x, dict):
            return x.get(key)
        return x

    out = []
    for i in data:
        if isinstance(i, BaseModel):
            out.append([_format(_field(i, h)) for h in headers] if headers else i.model_dump())
        elif isinstance(i, dict):
            out.append([_format(_field(i, h)) for h in headers] if headers else i)
        else:
            out.append(i)
    return _tabulate(out, headers=columns or "keys", tablefmt="rounded_outline")


def import_module(path: Path | str, package_dir: Path | str | None = ""):
    path = Path(path)
    package_dir = package_dir or path.parent
    if path.is_file():
        name = path.stem
        old_sys_path = sys.path.copy()
        if package_dir:
            name = path.relative_to(Path(package_dir).parent).with_suffix("").as_posix().replace("/", ".")
            sys.path.insert(0, Path(package_dir).parent.as_posix())
        spec = importlib.util.spec_from_file_location(name, str(Path(path).resolve()))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        sys.path = old_sys_path
        return m
    return None


def overwrite_directory(src_dir: Path | str, dst_dir: Path | str):
    """Force-copy the :src_dir to the :dst_dir, removing all existing files in the :dst_dir"""
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(dst_dir, ignore_errors=True)
    shutil.copytree(src_dir, dst_dir)
