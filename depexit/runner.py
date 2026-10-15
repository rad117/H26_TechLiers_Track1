"""Create isolated Python 3.12 venvs, apply migrations in a copy of the repo, and run pytest.

Owner: Sheersh. Output shapes: TestRun in team/CONTRACT.md. Everything this module reports
is VERIFIED evidence, so record every command it runs.
"""


def run_tests(repo_dir, label, work):
    """Make a fresh venv in repo_dir, install requirements.txt + pytest, run pytest; return a TestRun."""
    raise NotImplementedError("Sheersh: see team/SHEERSH.md, task 1")


def apply_migration(repo, record, ai, work):
    """Copy repo to work/candidates/<name>, apply ai['requirement_changes'] and ai['file_edits'].
    Return (candidate_path, unified_diff_text)."""
    raise NotImplementedError("Sheersh: see team/SHEERSH.md, task 2")
