"""Find where each dependency is imported, using the ast module.

Owner: Sohan. Adds `import_names` and `usages` to each DepRecord, marks declared-but-never-imported
records as status="unused", and appends new records with status="undeclared" for third-party
imports that are not declared anywhere (e.g. certifi).
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

from .deps import blank_record, normalise

SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", "build", "dist",
             "site-packages", "capsule_out", ".tox", ".mypy_cache", ".pytest_cache"}

# Used only when no venv is available to ask. Import name differs from the package name.
KNOWN_IMPORT_NAMES = {
    "python-dateutil": ["dateutil"],
    "setuptools": ["setuptools", "pkg_resources"],  # pkg_resources ships inside setuptools
    "pyyaml": ["yaml"],
    "pillow": ["PIL"],
    "beautifulsoup4": ["bs4"],
    "scikit-learn": ["sklearn"],
}


def python_files(repo):
    """Yield every .py file under repo, skipping virtualenvs and caches."""
    for path in sorted(repo.rglob("*.py")):
        parts = path.relative_to(repo).parts[:-1]
        if any(part in SKIP_DIRS for part in parts):
            continue
        if any((repo.joinpath(*parts[: i + 1]) / "pyvenv.cfg").exists() for i in range(len(parts))):
            continue  # a venv under another name
        yield path


def local_modules(repo):
    """Top-level names that belong to the project itself (packages and root-level .py files)."""
    names = set()
    for child in repo.iterdir():
        if child.is_dir() and (child / "__init__.py").exists():
            names.add(child.name)
        elif child.suffix == ".py":
            names.add(child.stem)
    return names


def is_test_file(rel):
    return rel.parts[0] in ("tests", "test") or rel.name.startswith("test_") or rel.name == "conftest.py"


def is_private(module, names):
    """True if the import reaches into something marked private (_name, but not __dunder__)."""
    parts = module.split(".") + list(names)
    return any(p.startswith("_") and not p.startswith("__") for p in parts)


def find_imports(path, rel):
    """Return one dict per absolute import statement in a file. Relative imports are skipped."""
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            pairs = [(alias.name, []) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            pairs = [(node.module, [alias.name for alias in node.names])]
        else:
            continue
        for module, names in pairs:
            found.append({
                "top": module.split(".")[0],
                "file": rel.as_posix(),
                "line": node.lineno,
                "code": lines[node.lineno - 1].strip(),
                "names": names,
                "private": is_private(module, names),
                "is_test": is_test_file(rel),
            })
    return found


def installed_distributions(venv_python):
    """Ask the baseline venv which import name belongs to which package. {import: [package, ...]}"""
    if not venv_python:
        return {}
    code = "import importlib.metadata as m, json; print(json.dumps(m.packages_distributions()))"
    try:
        out = subprocess.run([str(venv_python), "-c", code], capture_output=True, text=True,
                             timeout=60, check=True).stdout
        return json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}


def import_names_for(name, dist_to_imports):
    """Import names for one package: from the venv if known, else a name-based guess."""
    key = normalise(name)
    if key in dist_to_imports:
        return sorted(dist_to_imports[key])
    return KNOWN_IMPORT_NAMES.get(key, [key.replace("-", "_")])


def attach_usages(records, repo, venv_python=None):
    """Return records with usages filled in. venv_python (baseline venv) may be used to map
    package names to import names via importlib.metadata.packages_distributions()."""
    repo = Path(repo)
    import_to_dists = installed_distributions(venv_python)
    dist_to_imports = {}
    for import_name, dists in import_to_dists.items():
        for dist in dists:
            dist_to_imports.setdefault(normalise(dist), set()).add(import_name)

    skip = set(sys.stdlib_module_names) | local_modules(repo)
    imports = [imp for path in python_files(repo)
               for imp in find_imports(path, path.relative_to(repo))
               if imp["top"] not in skip]

    owner = {}  # import name -> record
    for record in records:
        record["import_names"] = import_names_for(record["name"], dist_to_imports)
        for import_name in record["import_names"]:
            owner[import_name] = record

    for imp in imports:
        top = imp.pop("top")
        record = owner.get(top)
        if record is None:
            # Imported but declared nowhere. Imports that only appear in tests (pytest) are dev
            # tooling, not a runtime dependency, so they don't create a record.
            if imp["is_test"]:
                continue
            package = (import_to_dists.get(top) or [top])[0]
            record = blank_record(package, status="undeclared")
            record["import_names"] = [top]
            records.append(record)
            owner[top] = record
        record["usages"].append(imp)

    for record in records:
        record["usages"].sort(key=lambda u: (u["file"], u["line"]))
        if record["status"] == "declared" and not record["usages"]:
            record["status"] = "unused"
    return records


if __name__ == "__main__":
    from . import deps

    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(attach_usages(deps.collect(target), target, sys.argv[2] if len(sys.argv) > 2 else None),
                     indent=2))
