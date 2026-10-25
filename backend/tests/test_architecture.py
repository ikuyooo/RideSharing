"""Module boundaries of the modular monolith (Revision 9 Section 54, D-31):
a module never imports another module's `models` (it would query tables it
does not own); it calls that module's `service` / `deps` instead."""

import ast
from pathlib import Path

MODULES_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
            names.extend(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
    return names


def test_no_cross_module_model_imports() -> None:
    violations = []
    for path in MODULES_ROOT.rglob("*.py"):
        owner = path.relative_to(MODULES_ROOT).parts[0]
        for name in _imports(path):
            parts = name.split(".")
            if len(parts) >= 4 and parts[:2] == ["app", "modules"] and parts[3] == "models" and parts[2] != owner:
                violations.append(f"{path.relative_to(MODULES_ROOT)} imports {name}")
    assert violations == []


def test_every_table_is_owned_by_exactly_one_module() -> None:
    from app.db.models import metadata

    owners: dict[str, str] = {}
    for table in metadata.sorted_tables:
        for path in MODULES_ROOT.glob("*/models.py"):
            if f'__tablename__ = "{table.name}"' in path.read_text(encoding="utf-8"):
                assert table.name not in owners, f"{table.name} declared twice"
                owners[table.name] = path.parent.name
    assert set(owners) == set(metadata.tables)
