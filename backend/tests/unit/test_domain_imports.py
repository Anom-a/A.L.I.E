"""Architecture tests: the domain layer must be pure standard-library Python.

These enforce the Clean Architecture dependency rule:

* every module under ``domain/`` imports only the standard library or other
  ``domain`` modules — never a third-party framework;
* importing the domain does not pull any forbidden framework into
  ``sys.modules``; and (Phase 1)
* the dependency arrow points inward only: ``adapters`` may depend on
  ``domain``, never the reverse, and adapters never read configuration.

The import scan uses the ``ast`` module (not text matching) so that framework
*names appearing in docstrings/comments* are correctly ignored.
"""

from __future__ import annotations

import ast
import importlib
import json
import pkgutil
import subprocess
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
    "tavily",
    "dotenv",
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

#: Layers that sit *outside* the domain. The domain may never import these.
OUTER_LAYER_ROOTS = {"adapters", "infrastructure", "application", "scripts"}

_DOMAIN_DIR = Path(domain.__file__).resolve().parent
_BACKEND_DIR = _DOMAIN_DIR.parent
_ADAPTERS_DIR = _BACKEND_DIR / "adapters"
_ALLOWED_LOCAL = {"domain", "__future__"}


def _domain_py_files() -> list[Path]:
    return sorted(_DOMAIN_DIR.rglob("*.py"))


def _adapter_py_files() -> list[Path]:
    return sorted(_ADAPTERS_DIR.rglob("*.py"))


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
    # This must run in a *clean* interpreter. The test session itself imports
    # the adapters (and therefore openai/tavily/requests/httpx), so the current
    # process's sys.modules says nothing about what the domain pulls in. A
    # subprocess that imports only the domain answers the real question.
    script = (
        "import importlib, json, pkgutil, sys\n"
        "import domain\n"
        "for info in pkgutil.walk_packages(domain.__path__, prefix='domain.'):\n"
        "    importlib.import_module(info.name)\n"
        "print(json.dumps(sorted(sys.modules)))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=_BACKEND_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = set(json.loads(completed.stdout))
    leaked = loaded & FORBIDDEN_ROOTS
    assert not leaked, f"importing the domain pulled in: {leaked}"


# --- Phase 1: the dependency arrow points inward only -----------------------


def test_adapter_files_found() -> None:
    # Guard against the adapter scans silently passing because they found nothing.
    assert _adapter_py_files(), "no adapter source files discovered"


def test_domain_does_not_depend_on_outer_layers() -> None:
    for path in _domain_py_files():
        outward = _imported_roots(path) & OUTER_LAYER_ROOTS
        assert not outward, f"{path.name} imports outer layer(s): {outward}"


def test_adapters_depend_on_the_domain() -> None:
    # Adapters exist to serve the domain; at least one must speak its language.
    roots: set[str] = set()
    for path in _adapter_py_files():
        roots |= _imported_roots(path)
    assert "domain" in roots, "no adapter imports the domain"


def test_adapters_do_not_depend_on_infrastructure_or_application() -> None:
    # Adapters receive configuration through their constructors, so they never
    # reach outward to the configuration/composition layer.
    for path in _adapter_py_files():
        outward = _imported_roots(path) & {"infrastructure", "application", "scripts"}
        assert not outward, f"{path.name} imports outer layer(s): {outward}"


def test_adapters_do_not_read_the_environment() -> None:
    # Environment/.env access belongs to infrastructure/config.py alone.
    for path in _adapter_py_files():
        roots = _imported_roots(path)
        assert "os" not in roots, f"{path.name} imports os (environment access)"
        assert "dotenv" not in roots, f"{path.name} imports dotenv"
