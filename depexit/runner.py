"""Create isolated Python 3.12 venvs, apply migrations in a copy of the repo, and run pytest.

Owner: Sheersh. Output shapes: TestRun in team/CONTRACT.md. Everything this module reports
is VERIFIED evidence, so record every command it runs.
"""
import difflib
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# "linkwatch/resources.py:1: DeprecationWarning: pkg_resources is deprecated ..."
# Any category name: pydantic's is "PydanticDeprecatedSince20", which doesn't end in "Warning".
WARNING_RE = re.compile(r"^\S+:\d+: \w+: ")


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
        line = relative(line, repo_dir)
        text = line.strip()
        if WARNING_RE.match(text):
            found.append(text)
        elif found and text and line.startswith("  ") and not line.startswith("   "):
            found[-1] += " " + text  # next line of a multi-line message (source code lines are indented 4)
    return list(dict.fromkeys(found))  # drop duplicates, keep order


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


REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalise(name):
    """PyPI treats Jinja2, jinja2 and jinja_2 style names as the same package."""
    return re.sub(r"[-_.]+", "-", name).lower()


def req_name(line):
    """Package name of a requirements.txt line, or None for comments, blanks and pip options."""
    match = REQ_NAME_RE.match(line)
    return normalise(match.group(1)) if match else None


def read_text(path):
    """File text with its line endings untouched, or None if the file doesn't exist."""
    return path.read_bytes().decode("utf-8") if path.exists() else None


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:  # newline="": don't add \r on Windows
        fh.write(text)


def change_requirements(text, changes, notes):
    """Apply Gemma's set/remove/add changes to requirements.txt text."""
    lines = text.splitlines(keepends=True)
    for change in changes:
        action, name = change.get("action"), normalise(str(change.get("name", "")))
        line = str(change.get("line") or "").strip()
        if action == "remove":
            lines = [l for l in lines if req_name(l) != name]
        elif action in ("set", "add"):
            # AI output: only accept a plain package line for the package it names,
            # never pip options like "--index-url ..." or a second package smuggled in
            if req_name(line) != name or "\n" in line:
                notes.append(f"rejected requirement change {change!r}")
                continue
            if any(req_name(l) == name for l in lines):
                lines = [line + "\n" if req_name(l) == name else l for l in lines]
            else:
                if lines and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"
                lines.append(line + "\n")
        else:
            notes.append(f"unknown requirement action {change!r}")
    return "".join(lines)


def file_diff(path, old, new):
    """Unified diff of one file in the a/ b/ form that `git apply` accepts."""
    old_lines = old.splitlines(keepends=True) if old is not None else []
    new_lines = new.splitlines(keepends=True)
    for lines in (old_lines, new_lines):
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n\\ No newline at end of file\n"
    return list(difflib.unified_diff(old_lines, new_lines,
                                     "/dev/null" if old is None else f"a/{path}", f"b/{path}"))


def apply_migration(repo, record, ai, work):
    """Copy repo to work/candidates/<name>, apply ai['requirement_changes'] and ai['file_edits'].
    Return (candidate_path, unified_diff_text)."""
    repo = Path(repo).resolve()
    cand = Path(work).resolve() / "candidates" / re.sub(r"[^A-Za-z0-9._-]", "_", record["name"])
    if cand.exists():
        shutil.rmtree(cand)  # start clean on every run
    shutil.copytree(repo, cand, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "junit.xml"))
    cand = cand.resolve()
    notes, changed = [], {}  # changed: "relative/path" -> new file text

    if ai.get("requirement_changes"):
        old = read_text(cand / "requirements.txt") or ""
        changed["requirements.txt"] = change_requirements(old, ai["requirement_changes"], notes)

    for edit in ai.get("file_edits") or []:
        path, content = str(edit.get("path", "")), edit.get("new_content")
        target = (cand / path).resolve()
        # AI output: refuse anything that would write outside the candidate copy (../, /etc/...)
        if not target.is_relative_to(cand) or target == cand or not isinstance(content, str):
            notes.append(f"rejected file edit {path!r}")
            continue
        changed[target.relative_to(cand).as_posix()] = content

    diff = [f"# depexit: {note}\n" for note in notes]  # git apply ignores text before the first diff
    for path, new in changed.items():
        old = read_text(repo / path)
        if new != old:
            write_text(cand / path, new)
            diff += file_diff(path, old, new)
    return cand, "".join(diff)
