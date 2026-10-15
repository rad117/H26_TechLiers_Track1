"""Find where each dependency is imported, using the ast module.

Owner: Sohan. Adds `import_names` and `usages` to each DepRecord, marks declared-but-never-imported
records as status="unused", and appends new records with status="undeclared" for third-party
imports that are not declared anywhere (e.g. certifi).
"""


def attach_usages(records, repo, venv_python=None):
    """Return records with usages filled in. venv_python (baseline venv) may be used to map
    package names to import names via importlib.metadata.packages_distributions()."""
    raise NotImplementedError("Sohan: see team/SOHAN.md, task 2")
