"""Architecture tests: the domain layer must be pure standard-library Python.

These enforce the Clean Architecture dependency rule for Phase 0:

* every module under ``domain/`` imports only the standard library or other
  ``domain`` modules — never a third-party framework; and
* importing the domain does not pull any forbidden framework into ``sys.modules``.

The import scan uses the ``ast`` module (not text matching) so that framework
*names appearing in docstrings/comments* are correctly ignored.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
import sys
from pathlib import Path

import domain

FORBIDDEN_ROOTS = {
    "fastapi",
    "starlette",
    "langgraph",
    "langchain",
    "langchain_core",
    "openai",
    "httpx",
    "requests",
    "aiohttp",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
    "redis",
    "psycopg",
    "psycopg2",
    "asyncpg",
}

_DOMAIN_DIR = Path(domain.__file__).resolve().parent
_ALLOWED_LOCAL = {"domain", "__future__"}


def _domain_py_files() -> list[Path]:
    return sorted(_DOMAIN_DIR.rglob("*.py"))


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # Ignore relative imports (node.level > 0); they stay inside domain.
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return roots


def test_domain_files_found() -> None:
    # Guard against the scan silently passing because it found nothing.
    assert _domain_py_files(), "no domain source files discovered"


def test_domain_imports_only_stdlib_or_domain() -> None:
    stdlib = set(sys.stdlib_module_names)
    offenders: dict[str, set[str]] = {}
    for path in _domain_py_files():
        external = {
            root
            for root in _imported_roots(path)
            if root not in stdlib and root not in _ALLOWED_LOCAL
        }
        if external:
            offenders[str(path.relative_to(_DOMAIN_DIR))] = external
    assert not offenders, f"domain imports non-stdlib modules: {offenders}"


def test_domain_imports_no_forbidden_frameworks() -> None:
    for path in _domain_py_files():
        forbidden = _imported_roots(path) & FORBIDDEN_ROOTS
        assert not forbidden, f"{path.name} imports forbidden framework(s): {forbidden}"


def test_whole_domain_package_imports_cleanly() -> None:
    # Import every submodule to prove the package loads without any framework.
    for module_info in pkgutil.walk_packages(
        domain.__path__, prefix="domain."
    ):
        importlib.import_module(module_info.name)


def test_no_forbidden_framework_loaded_after_import() -> None:
    loaded = set(sys.modules)
    for forbidden in FORBIDDEN_ROOTS:
        assert forbidden not in loaded, f"{forbidden} was imported by the domain"
