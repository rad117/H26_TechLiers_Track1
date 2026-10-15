"""Tests for runner's parsing and apply_migration (no venvs, no network). Run: python -m pytest depexit/tests -q"""
import subprocess
from pathlib import Path

from depexit import runner

JUNIT = """<?xml version="1.0" encoding="utf-8"?><testsuites name="pytest tests">
<testsuite name="pytest" errors="0" failures="1" skipped="0" tests="3">
<testcase classname="tests.test_cache" name="test_round_trip" />
<testcase classname="tests.test_config" name="test_loads" />
<testcase classname="tests.test_report" name="test_renders">
<failure message="ImportError: cannot import name 'soft_unicode' from 'markupsafe' (REPO/.venv/x.py)&#10;more">trace</failure>
</testcase></testsuite></testsuites>"""


def test_parse_junit_counts_and_failing_test_ids(tmp_path):
    (tmp_path / "junit.xml").write_text(JUNIT.replace("REPO", str(tmp_path)), encoding="utf-8")
    result = runner.parse_junit(tmp_path / "junit.xml", tmp_path)
    assert (result["tests"], result["passed"], result["failed"]) == (3, 2, 1)
    # classname -> file path, only the first message line, absolute repo path stripped
    assert result["failing_tests"] == {
        "tests/test_report.py::test_renders":
            "ImportError: cannot import name 'soft_unicode' from 'markupsafe' (.venv/x.py)"}


def test_parse_warnings_any_category_multiline_and_relative(tmp_path):
    output = f"""=== warnings summary ===
linkwatch/config.py:14
  {tmp_path}/linkwatch/config.py:14: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated.
    @validator("name")

.venv/pydantic/_config.py:408
  {tmp_path}/.venv/pydantic/_config.py:408: UserWarning: Valid config keys have changed in V2:
  * 'anystr_strip_whitespace' has been renamed to 'str_strip_whitespace'
    warnings.warn(message, UserWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
"""
    assert runner.parse_warnings(output, tmp_path) == [
        "linkwatch/config.py:14: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated.",
        ".venv/pydantic/_config.py:408: UserWarning: Valid config keys have changed in V2: "
        "* 'anystr_strip_whitespace' has been renamed to 'str_strip_whitespace'",
    ]


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "linkwatch").mkdir(parents=True)
    (repo / "requirements.txt").write_text("toml==0.10.2\nJinja2==2.11.3\n# PyYAML==5.1\n", encoding="utf-8")
    (repo / "linkwatch" / "resources.py").write_text("import pkg_resources\n", encoding="utf-8")
    return repo


def test_apply_migration_set_remove_add_and_diff_applies_with_git(tmp_path):
    repo = make_repo(tmp_path)
    ai = {"requirement_changes": [{"action": "set", "name": "jinja2", "line": "Jinja2>=3.1,<4"},
                                  {"action": "remove", "name": "toml"},
                                  {"action": "add", "name": "platformdirs", "line": "platformdirs>=4"}],
          "file_edits": [{"path": "linkwatch/resources.py", "new_content": "import importlib.resources\n"}]}
    cand, diff = runner.apply_migration(repo, {"name": "Jinja2"}, ai, tmp_path / "work")
    assert (cand / "requirements.txt").read_text() == "Jinja2>=3.1,<4\n# PyYAML==5.1\nplatformdirs>=4\n"
    assert (repo / "requirements.txt").read_text().startswith("toml==")  # the original is untouched
    # the patch must recreate the candidate from the original (replay.ps1 runs `git apply`)
    (tmp_path / "patch.diff").write_text(diff, encoding="utf-8")
    subprocess.run(["git", "apply", str(tmp_path / "patch.diff")], cwd=repo, check=True)
    assert (repo / "requirements.txt").read_text() == (cand / "requirements.txt").read_text()
    assert (repo / "linkwatch" / "resources.py").read_text() == "import importlib.resources\n"


def test_apply_migration_rejects_unsafe_ai_output(tmp_path):
    repo = make_repo(tmp_path)
    ai = {"requirement_changes": [{"action": "set", "name": "toml", "line": "--index-url http://evil.test"},
                                  {"action": "set", "name": "toml", "line": "toml\nevilpkg"}],
          "file_edits": [{"path": "../../escape.txt", "new_content": "x"},
                         {"path": str(tmp_path / "abs.txt"), "new_content": "x"}]}
    cand, diff = runner.apply_migration(repo, {"name": "toml"}, ai, tmp_path / "work")
    assert diff.count("# depexit: rejected") == 4
    assert not (tmp_path / "work" / "escape.txt").exists() and not (tmp_path / "abs.txt").exists()
    assert (cand / "requirements.txt").read_text() == (repo / "requirements.txt").read_text()
