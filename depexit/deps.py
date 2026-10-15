"""Read declared dependencies from requirements.txt and pyproject.toml.

Owner: Sohan. Output shape: DepRecord in team/CONTRACT.md
(fill name, specs, pinned_version, spec_mismatch, status="declared";
leave usages/pypi/signals empty for later stages).
"""
import re
import tomllib
from pathlib import Path

# "Jinja2==2.11.3", "pydantic>=2", "requests[socks]>=2 ; python_version>'3.8'", "six"
REQ_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*([^;]*)")


def normalise(name):
    """PyPI-style name: lowercase, runs of - _ . become a single '-'."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement(line):
    """Return (name, spec) for one requirement line, or None if it is not a requirement."""
    line = line.split("#", 1)[0].strip()
    if not line or line.startswith("-"):  # blank, comment, or an option like -r other.txt
        return None
    match = REQ_RE.match(line)
    if not match:
        return None
    return match.group(1), match.group(2).replace(" ", "")


def read_requirements_txt(path):
    if not path.exists():
        return []
    found = (parse_requirement(line) for line in path.read_text(encoding="utf-8").splitlines())
    return [item for item in found if item]


def read_pyproject(path):
    if not path.exists():
        return []
    with open(path, "rb") as fh:  # tomllib needs binary mode
        data = tomllib.load(fh)
    found = (parse_requirement(line) for line in data.get("project", {}).get("dependencies", []))
    return [item for item in found if item]


def blank_record(name, status="declared"):
    """An empty DepRecord; later stages (scan, pypi) fill in the rest."""
    return {
        "name": name,
        "import_names": [],
        "status": status,
        "specs": {},
        "pinned_version": None,
        "spec_mismatch": False,
        "usages": [],
        "pypi": {},
        "signals": [],
    }


def collect(repo):
    """Return a list of DepRecord dicts, one per declared package (merged across both files)."""
    repo = Path(repo)
    sources = {
        "requirements.txt": read_requirements_txt(repo / "requirements.txt"),
        "pyproject.toml": read_pyproject(repo / "pyproject.toml"),
    }
    records = {}  # normalised name -> record; dicts keep first-seen order
    for filename, items in sources.items():
        for name, spec in items:
            record = records.setdefault(normalise(name), blank_record(name))
            record["specs"][filename] = spec

    for record in records.values():
        specs = record["specs"]
        # Only a real disagreement counts: the package must be listed in both files.
        record["spec_mismatch"] = len(specs) > 1 and len(set(specs.values())) > 1
        # requirements.txt is what gets installed, so its pin wins over pyproject's.
        for filename in ("requirements.txt", "pyproject.toml"):
            spec = specs.get(filename, "")
            if spec.startswith("==") and "," not in spec:
                record["pinned_version"] = spec[2:]
                break
    return list(records.values())


if __name__ == "__main__":
    import json
    import sys

    print(json.dumps(collect(sys.argv[1] if len(sys.argv) > 1 else "."), indent=2))
