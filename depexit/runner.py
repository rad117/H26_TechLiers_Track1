"""Create isolated Python 3.12 venvs, apply migrations in a copy of the repo, and run pytest.

Owner: Sheersh. Output shapes: TestRun in team/CONTRACT.md. Everything this module reports
is VERIFIED evidence, so record every command it runs.
"""
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# "  linkwatch/resources.py:1: DeprecationWarning: pkg_resources is deprecated ..."
WARNING_RE = re.compile(r"^\s*\S+:\d+: \w*Warning: ")


def venv_python(repo_dir):
    """The venv's python: Scripts\\python.exe on Windows, bin/python on macOS/Linux."""
    if os.name == "nt":
        return repo_dir / ".venv" / "Scripts" / "python.exe"
    return repo_dir / ".venv" / "bin" / "python"


def relative(text, repo_dir):
    """Strip the absolute repo path so baseline and candidate output can be compared."""
    return text.replace(str(repo_dir) + os.sep, "")


def tail(text, lines=40):
    return "\n".join(text.splitlines()[-lines:])


def run_step(cmd, repo_dir, log, commands, timeout):
    """Run one command inside repo_dir, append its output to the log and record it.
    Return (exit_code, output). exit_code is None if it timed out or could not start."""
    cmd = [str(c) for c in cmd]
    shown = relative(" ".join(cmd), repo_dir)
    commands.append(shown)
    try:
        proc = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        code, output = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        code, output = None, f"TIMEOUT after {timeout} s"
    except OSError as exc:
        code, output = None, str(exc)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"$ {shown}\n{output}\n")
    return code, output


def parse_junit(junit, repo_dir):
    """Counts and failing tests from pytest's junit.xml."""
    root = ET.parse(junit).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    count = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    failing = {}
    for case in root.iter("testcase"):
        problem = case.find("failure")
        if problem is None:  # `or` would be wrong here: an Element with no children is falsy
            problem = case.find("error")
        if problem is not None:
            # classname "tests.test_report" -> "tests/test_report.py"
            test_id = case.get("classname").replace(".", "/") + ".py::" + case.get("name")
            message = (problem.get("message") or "").splitlines()
            failing[test_id] = relative(message[0], repo_dir) if message else ""
    return {
        "tests": count["tests"],
        "passed": count["tests"] - count["failures"] - count["errors"] - count["skipped"],
        "failed": count["failures"], "errors": count["errors"], "skipped": count["skipped"],
        "failing_tests": failing,
    }


def parse_warnings(output, repo_dir):
    """The 'path:line: SomeWarning: message' lines under pytest's 'warnings summary'."""
    if "warnings summary" not in output:
        return []
    section = output.split("warnings summary", 1)[1].split("-- Docs:", 1)[0]
    found = []
    for line in section.splitlines():
        line = relative(line, repo_dir).strip()
        if WARNING_RE.match(line) and line not in found:
            found.append(line)
    return found


def run_tests(repo_dir, label, work):
    """Make a fresh venv in repo_dir, install requirements.txt + pytest, run pytest; return a TestRun."""
    repo_dir, work = Path(repo_dir).resolve(), Path(work).resolve()
    (work / "logs").mkdir(parents=True, exist_ok=True)
    log = work / "logs" / f"{label}.log"
    log.write_text("", encoding="utf-8")
    py = venv_python(repo_dir)
    started = time.monotonic()
    result = {
        "label": label, "stage": "venv", "ok": False, "python_version": None, "venv_python": str(py),
        "tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0,
        "failing_tests": {}, "warnings": [], "duration_s": 0.0, "commands": [], "log_file": str(log),
    }

    def finish(error=None):
        if error:
            result["error"] = error
        result["duration_s"] = round(time.monotonic() - started, 1)
        return result

    # uv is fast; without it fall back to the normal venv + pip
    if shutil.which("uv"):
        make_venv = ["uv", "venv", "--clear", "--python", "3.12", ".venv"]
        install = ["uv", "pip", "install", "--python", py, "-r", "requirements.txt", "pytest"]
    else:
        python312 = ["py", "-3.12"] if os.name == "nt" else ["python3.12"]
        make_venv = python312 + ["-m", "venv", "--clear", ".venv"]
        install = [py, "-m", "pip", "install", "-r", "requirements.txt", "pytest"]

    # 1. fresh venv
    code, output = run_step(make_venv, repo_dir, log, result["commands"], timeout=120)
    if code != 0:
        return finish(tail(output))
    result["python_version"] = subprocess.run(
        [str(py), "-c", "import platform; print(platform.python_version())"],
        capture_output=True, text=True).stdout.strip()

    # 2. install (requirements.txt only: requirements-dev.txt has nose, which breaks on 3.12)
    result["stage"] = "install"
    code, output = run_step(install, repo_dir, log, result["commands"], timeout=600)
    if code != 0:
        return finish(tail(output))  # a failed install is a result, not a crash

    # 3. tests
    result["stage"] = "tests"
    junit = repo_dir / "junit.xml"
    junit.unlink(missing_ok=True)
    pytest = [py, "-m", "pytest", "-q", "-W", "default", "-p", "no:cacheprovider", "--junitxml=junit.xml"]
    code, output = run_step(pytest, repo_dir, log, result["commands"], timeout=300)
    if not junit.exists():
        return finish(tail(output))
    result.update(parse_junit(junit, repo_dir))
    result["warnings"] = parse_warnings(output, repo_dir)
    result["ok"] = result["tests"] > 0 and result["failed"] == 0 and result["errors"] == 0
    return finish()


def apply_migration(repo, record, ai, work):
    """Copy repo to work/candidates/<name>, apply ai['requirement_changes'] and ai['file_edits'].
    Return (candidate_path, unified_diff_text)."""
    raise NotImplementedError("Sheersh: see team/SHEERSH.md, task 2")
