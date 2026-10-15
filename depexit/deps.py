"""Read declared dependencies from requirements.txt and pyproject.toml.

Owner: Sohan. Output shape: DepRecord in team/CONTRACT.md
(fill name, specs, pinned_version, spec_mismatch, status="declared";
leave usages/pypi/signals empty for later stages).
"""


def collect(repo):
    """Return a list of DepRecord dicts, one per declared package (merged across both files)."""
    raise NotImplementedError("Sohan: see team/SOHAN.md, task 1")
