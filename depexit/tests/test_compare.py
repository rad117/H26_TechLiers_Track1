"""Tests for compare.compare and compare.scorecard. Run: python -m pytest depexit/tests -q"""
from depexit import compare

REPORT = "tests/test_report.py::test_report_renders_all_sites"
CONFIG = "tests/test_config.py::test_sites_file_loads"
PKG_WARNING = "linkwatch/resources.py:1: DeprecationWarning: pkg_resources is deprecated as an API."

# the real baseline: 10 tests, Jinja2's soft_unicode failure, one warning
BASELINE = {"stage": "tests", "ok": False, "tests": 10, "passed": 9,
            "failing_tests": {REPORT: "ImportError: cannot import name 'soft_unicode'"},
            "warnings": [PKG_WARNING]}
AI = {"ok": True, "predicted_outcome": "pass", "file_edits": []}


def run(failing=None, warnings=(PKG_WARNING,), tests=10, stage="tests", error=None):
    failing = failing or {}
    return {"stage": stage, "ok": stage == "tests" and tests > 0 and not failing, "tests": tests,
            "passed": tests - len(failing), "failing_tests": failing, "warnings": list(warnings),
            "error": error}


def test_fixing_the_baseline_failure_is_improved():
    cmp = compare.compare(BASELINE, run(), AI)
    assert cmp["verdict"] == "improved"
    assert cmp["newly_passing"] == [REPORT]
    assert cmp["actual_outcome"] == "pass" and cmp["prediction_correct"] is True


def test_unrelated_old_failure_still_counts_as_pass():
    # decision A: a change that breaks nothing new is a pass, even with the old Jinja2 failure
    cmp = compare.compare(BASELINE, run(failing=dict(BASELINE["failing_tests"])), AI)
    assert cmp["verdict"] == "same"
    assert cmp["still_failing"] == [REPORT]
    assert cmp["actual_outcome"] == "pass"


def test_newly_failing_test_is_regressed_with_a_gap():
    failing = {**BASELINE["failing_tests"], CONFIG: "ValidationError: url"}
    cmp = compare.compare(BASELINE, run(failing=failing), AI)
    assert cmp["verdict"] == "regressed"
    assert cmp["newly_failing"] == [CONFIG]
    assert cmp["gaps"][0] == f"{CONFIG} now fails: ValidationError: url"
    assert cmp["actual_outcome"] == "fail" and cmp["prediction_correct"] is False


def test_failed_install_is_blocked():
    cmp = compare.compare(BASELINE, run(stage="install", tests=0, error="error: no solution\nidna==99 not found"), AI)
    assert cmp["verdict"] == "blocked"
    assert cmp["newly_passing"] == []  # nothing ran, so the old failure did not "get fixed"
    assert "idna==99 not found" in cmp["gaps"][0]


def test_tests_that_stop_running_are_a_regression_not_an_improvement():
    # e.g. removing toml makes conftest.py fail to import, so pytest runs 0 tests
    cmp = compare.compare(BASELINE, run(tests=0, error="E   ModuleNotFoundError: No module named 'toml'"), AI)
    assert cmp["verdict"] == "regressed"
    assert cmp["newly_passing"] == []
    assert cmp["gaps"][0].startswith("10 of the original 10 tests no longer ran")


def test_gone_warning_is_improved_and_new_warning_is_a_gap():
    assert compare.compare(BASELINE, run(failing=dict(BASELINE["failing_tests"]), warnings=[]), AI)["verdict"] == "improved"
    cmp = compare.compare(BASELINE, run(warnings=[PKG_WARNING, "x.py:1: UserWarning: renamed"]), AI)
    assert cmp["new_warnings"] == ["x.py:1: UserWarning: renamed"]
    assert "New warning: x.py:1: UserWarning: renamed" in cmp["gaps"]


def test_patch_that_edits_tests_is_flagged():
    ai = {**AI, "file_edits": [{"path": "tests/test_report.py", "new_content": "def test_x(): pass\n"}]}
    assert any("edits test files" in g for g in compare.compare(BASELINE, run(), ai)["gaps"])


def test_failed_ai_is_not_graded():
    cmp = compare.compare(BASELINE, run(), {"ok": False, "error": "bad json"})
    assert cmp["prediction_correct"] is None and cmp["predicted_outcome"] is None


def test_scorecard_counts_only_graded_results():
    good = {"dep": {"name": "Jinja2"}, "run": run(), "comparison": compare.compare(BASELINE, run(), AI)}
    bad_run = run(stage="install", tests=0, error="no solution")
    bad = {"dep": {"name": "idna"}, "run": bad_run, "comparison": compare.compare(BASELINE, bad_run, AI)}
    ai_failed = {"dep": {"name": "six"}, "run": None, "comparison": None}
    card = compare.scorecard([good, bad, ai_failed])
    assert (card["total"], card["correct"], card["accuracy"]) == (2, 1, 0.5)
    assert card["wrong"] == [{"dep": "idna", "predicted": "pass", "actual": "fail",
                              "why": "Blocked at the install stage, so no tests ran: no solution"}]
    assert compare.scorecard([])["accuracy"] is None  # never claim "0%" when nothing was graded
